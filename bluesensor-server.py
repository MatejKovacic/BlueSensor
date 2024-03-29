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
from multiprocessing import queues, get_context
from collections import deque

import database as db

DB_SAVE = 5 # every <n> sensor reports

def dump(obj, detailed=False):
    sys.stdout.write('obj.type = {}\n'.format(type(obj)))
    sys.stdout.flush()
    for attr in dir(obj):
        try:
            value = getattr(obj, attr)
            sys.stdout.write('obj.{} = {}\n'.format(attr, value))
            sys.stdout.flush()
            if detailed and str(value).startswith('<'):
                sys.stdout.write('  '); n = 0
                for oattr in dir(value):
                    if n > 0: sys.stdout.write(' ')
                    sys.stdout.write('{}'.format(oattr)); n += 1
                sys.stdout.write('\n')
                sys.stdout.flush()
        except: pass

def print_exc(f_name, msg=''):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    exc = traceback.format_exception_only(exc_type, exc_obj)
    err = '{}({}): {}'.format(f_name, exc_tb.tb_lineno, msg) + exc[-1].strip()
    sys.stderr.write(err + '\n')
    sys.stderr.flush()

class MainHandler(web.RequestHandler):
    @gen.coroutine
    def get(self):
        try:
            graf_template = os.path.join(os.path.dirname(__file__), 'graf.html')
            with open(graf_template) as f:
                html = f.read()
            self.write(html)
            self.flush()
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

@gen.coroutine
def update_db(sensor, data):
    try:
        print('Inserting data into db', flush=True)
        db.dbInsert(sensor, data)
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
            cmd = [sys.executable, reader_py, sensor_name]
            if simulate: cmd.append('simulate')
            # this subprocess creation with pipes works on Unix and Windows!
            proc = subprocess.Popen(cmd, bufsize=1, universal_newlines=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            q = queues.Queue(ctx=get_context())
            t = Thread(target=enque_output, args=(proc.stdout, q))
            t.daemon = True; t.start()

            tick = 1
            while True:
                try:
                    line = q.get_nowait().strip() # get next line from subprocess
                except:
                    yield gen.sleep(1) # wait 1 second
                    continue # no output yet

                print('Got JSON: %r' % line, flush=True)
                try:
                    measurement = json.loads(line)
                    #print(measurement, flush=True)
                    ioloop.add_callback(send_update, measurement)
                    if db_use and (tick % db_save) == 0:
                        ioloop.add_callback(update_db, USBPORT, line)
                    tick += 1
                except:
                    print_exc(sys._getframe().f_code.co_name, 'invalid JSON: ')
                    yield gen.sleep(1) # wait 1 second
                    continue
        except:
            print_exc(sys._getframe().f_code.co_name)
            yield gen.sleep(5) # wait 5 seconds

# Reopen stdout and stderr with buffer size 0 (unbuffered) - only in python 2.7
#sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
#sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 0)

db_use = False; db_save = DB_SAVE

argv = []; vf = False
for arg in sys.argv:
    if re.match(r'^-', arg) or vf:
        if re.match(r'--data-log', arg):
            db_use = True
            vf = True
        elif vf:
            try:
                db_save = int(arg)
                if db_save <= 0:
                    db_save = DB_SAVE
            except ValueError:
                db_save = DB_SAVE
            vf = False
        else:
            sys.stderr.write('Error: unknown argument \'{}\'\n'.format(arg))
            sys.stderr.flush()
            vf = False
    else:
        argv.append(arg)

if len(argv) == 1:
    sys.stderr.write('This application must be called with parameters specifying reader and port number.\n')
    sys.stderr.write('For example:\n')
    sys.stderr.write('$ python bluesensor-server.py read-raw-serial 0\n')
    sys.stderr.write('  for reading data from BlueSensor connected to ttyUSB0\n')
    sys.stderr.write('$ python bluesensor-server.py read-dust 1\n')
    sys.stderr.write('  for reading data from dust sensor connected to ttyUSB1\n')
    sys.stderr.flush()
    sys.exit(1)

sensor_name = str(argv[1])
if re.match(r'read-dust', sensor_name):
    reader_py = os.path.join(os.path.dirname(__file__), 'read-dust.py')
elif re.match(r'read-raw-serial', sensor_name):
    reader_py = os.path.join(os.path.dirname(__file__), 'read-raw-serial.py')
#elif re.match(r'read-serial', sensor_name):
else: # default
    reader_py = os.path.join(os.path.dirname(__file__), 'read-serial.py')

if not os.path.isfile(reader_py):
    sys.stderr.write('Error: file "{}" doesn\'t exist\n'.format(reader_py))
    sys.stderr.flush()
    sys.exit(2)

if len(argv) < 3:
    sys.stderr.write('Error: missing USB port number (for example from 0 to 3)\n')
    sys.stderr.flush()
    sys.exit(3)
else:
    sensor_name = str(argv[2])
    port_id = int('808' + sensor_name) # set port number according to sensor number

if sys.platform.startswith('win'):
    DEVNAME = 'COM'
elif sys.platform.startswith('darwin'):
    DEVNAME = '/dev/tty.'
else: # linux
    DEVNAME = '/dev/ttyUSB'
USBPORT = DEVNAME + sensor_name # can be 'usbserialxxx' on Mac

simulate = len(argv) > 3

STATIC_PATH = os.path.join(os.path.dirname(__file__), 'static')
app = web.Application([
    (r"/", MainHandler),
    (r"/data", DataHandler),
    (r'/static/(.*)', web.StaticFileHandler, {'path': STATIC_PATH})
])
app.listen(port_id) # webserver listening TCP port

if db_use:
    db_use = db.dbOpen()

sys.stdout.write('Starting Sensor web server with {}\n'.format(reader_py))
sys.stdout.write('To connect, open http://localhost:' + str(port_id) + '/\n')
sys.stdout.flush()
ioloop = ioloop.IOLoop.current()
ioloop.add_callback(reader, ioloop)
ioloop.start()
