#!/usr/bin/python
# coding: utf-8

# Python application for displaying data from BlueSensor in a web application.
# Appication runs web server on a localhost and calls data reader.
# Currently there are two data readers available:
# - read-raw-serial, which reads raw (tab-delimited) data from BlueSensor connected to USB port;
# - read-dust, which reads JSON formatted data from SDS011, SDS018 or SDS021 dust sensor.
# Credits: Gasper Zejn, Matjaz Rihtar, Matej Kovacic.

import sys, os, re
import traceback
import datetime, time
from pprint import pprint
import json
from tornado import ioloop, gen, websocket, web
import subprocess
from threading import Thread
from multiprocessing.queues import Queue, Empty
from collections import namedtuple, deque

def dump(obj, detailed=False):
    sys.stdout.write('obj.type = {}\n'.format(type(obj)))
    for attr in dir(obj):
        try:
            value = getattr(obj, attr)
            sys.stdout.write('obj.{} = {}\n'.format(attr, value))
            if detailed and str(value).startswith('<'):
                sys.stdout.write('  '); n = 0
                for oattr in dir(value):
                    if n > 0: sys.stdout.write(' ')
                    sys.stdout.write('{}'.format(oattr)); n += 1
                sys.stdout.write('\n')
        except: pass

def print_exc(f_name, msg=''):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    exc = traceback.format_exception_only(exc_type, exc_obj)
    err = '{}({}): {}'.format(f_name, exc_tb.tb_lineno, msg) + exc[-1].strip()
    sys.stderr.write(err + '\n')

class MainHandler(web.RequestHandler):
    @gen.coroutine
    def get(self):
        try:
            graf_template = os.path.join(os.path.dirname(__file__), 'graf.html')
            with open(graf_template) as f:
                html = f.read()
            self.write(html)
        except:
            print_exc(sys._getframe().f_code.co_name, graf_template + ': ')

class DataHandler(websocket.WebSocketHandler):
    clients = set()
    meritve = deque(maxlen=300)

    def open(self):
        self.send_initial()

    def send_initial(self):
        initial_message = json.dumps({}) # empty json
        self.write_message(initial_message)
        DataHandler.clients.add(self)

@gen.coroutine
def send_update(measurement):
    DataHandler.meritve.append(measurement)
    for client in DataHandler.clients.copy():
        try:
            client.write_message(measurement)
        except:
            print_exc(sys._getframe().f_code.co_name, 'WebSocket: ')
            try:
                DataHandler.clients.remove(client)
            except: pass

# async thread for reading subprocess' stdout
def enque_output(out, queue):
    try:
        for line in iter(out.readline, ''):
            queue.put(line)
        out.close()
    except: pass

@gen.coroutine
def reader(ioloop):
    while True:
        try:
            cmd = [sys.executable, reader_py, sensor_name, '1']
            # this subprocess creation with pipes works on Unix and Windows!
            proc = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            q = Queue()
            t = Thread(target=enque_output, args=(proc.stdout, q))
            t.daemon = True; t.start()

            while True:
                try:
                    line = q.get_nowait() # get next line from subprocess
                except:
                    yield gen.sleep(1) # wait 1 second
                    continue # no output yet

                print('Got JSON: %r' % line)
                try:
                    measurement = json.loads(line)
                    #print(measurement)
                    ioloop.add_callback(send_update, measurement)
                except:
                    print_exc(sys._getframe().f_code.co_name, 'invalid JSON: ')
                    yield gen.sleep(1) # wait 1 second
                    continue
        except:
            traceback.print_exc()
            print_exc(sys._getframe().f_code.co_name)
            yield gen.sleep(5) # wait 5 seconds

# Reopen sys.stdout with buffer size 0 (unbuffered)
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

if len(sys.argv) == 1:
    sys.stderr.write('This application must be called with parameters specifying reader and port number.\n')
    sys.stderr.write('For example:\n')
    sys.stderr.write('$ python bluesensor-server.py read-raw-serial 0\n')
    sys.stderr.write('  for reading data from BlueSensor connected to ttyUSB0\n')
    sys.stderr.write('$ python bluesensor-server.py read-dust 1\n')
    sys.stderr.write('  for reading data from dust sensor connected to ttyUSB1\n')
    sys.exit(1)

sensor_name = str(sys.argv[1])
if re.match('read-dust', sensor_name):
    reader_py = os.path.join(os.path.dirname(__file__), 'read-dust.py')
elif re.match('read-raw-serial', sensor_name):
    reader_py = os.path.join(os.path.dirname(__file__), 'read-raw-serial.py')
#elif re.match('read-serial', sensor_name):
else: # default
    reader_py = os.path.join(os.path.dirname(__file__), 'read-serial.py')

if not os.path.isfile(reader_py):
    sys.stderr.write('Error: file "{}" doesn\'t exist\n'.format(reader_py))
    sys.exit(2)

if len(sys.argv) < 3 or not sys.argv[2].isdigit():
    sys.stderr.write('Error: missing USB port number (for example from 0 to 3)\n')
    sys.exit(3)
else:
    sensor_name = str(sys.argv[2])
    port_id = int('808' + sensor_name) # set port number according to sensor number

STATIC_PATH = os.path.join(os.path.dirname(__file__), 'static')
app = web.Application([
    (r"/", MainHandler),
    (r"/data", DataHandler),
    (r'/static/(.*)', web.StaticFileHandler, {'path': STATIC_PATH})
])
app.listen(port_id) # webserver listening TCP port

sys.stdout.write('Starting Tornado web server...\n')
sys.stdout.write('To connect, open http://localhost:' + str(port_id) + '/\n')
ioloop = ioloop.IOLoop.current()
ioloop.add_callback(reader, ioloop)
ioloop.start()
