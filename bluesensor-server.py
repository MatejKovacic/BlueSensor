#!/usr/bin/python
# Python application for displaying data from BlueSensor in a web application.
# Appication runs web server on a localhost and calls data reader.
# Currently there are two data readers available:
# - read-raw-serial, which reads raw (tab-delimited) data from BlueSensor connected to USB port;
# - read-dust, which reads JSON formatted data from SDS011, SDS018 or SDS021 dust sensor.
# Credits: Gasper Zejn, Matjaz Rihtar, Matej Kovacic.

import sys, os, re
import json
import time
import tornado.ioloop
from tornado import template, gen, process, websocket, web
from collections import namedtuple, deque
import traceback

if len(sys.argv) == 1:
    sys.stderr.write('This application must be called with parameter specifying reader.\n')
    sys.stderr.write('For example:')
    sys.stderr.write('- "python bluesensor-server.py read-raw-serial 0" for reading data from BlueSensor connected to ttyUSB0,\n')
    sys.stderr.write('- "python bluesensor-server.py read-dust for reading data from dust sensor (which should be connected to ttyUSB0).\n')
    sys.exit()

sensor_name = str(sys.argv[1])

if re.match('read-dust', sensor_name):
    reader_py = 'read-dust.py'
    sensor_name = "9"
    port_id = int('808' + sensor_name) # set port number according to sensor number

elif re.match('read-raw-serial', sensor_name):
    reader_py = 'read-raw-serial.py'
    if len(sys.argv) < 3:
        sys.stderr.write('ERROR: when using "read-raw-serial" parameter you must add USB port number!\n')
        sys.exit()
    if (sys.argv[2].isdigit()):
        sensor_name = str(sys.argv[2])
        port_id = int('808' + sensor_name) # set port number according to sensor number
    else:
        sys.stderr.write('ERROR: when using "read-raw-serial" parameter you must add USB port number (for example from 0 to 3)!\n')
        sys.exit()


measurement = namedtuple("Measurement", ["t", "gas", "higro", "temp1", "temp2"])

DELIMITER = b'\n'
STATIC_PATH = os.path.join(os.path.dirname(__file__), 'static')

class MainHandler(web.RequestHandler):
    @gen.coroutine
    def get(self):
        with open(os.path.join(os.path.dirname(__file__), 'graf.html')) as f:
            graf_template = f.read()

        self.write(graf_template)


class DataHandler(websocket.WebSocketHandler):
    clients = set()
    meritve = deque(maxlen=300)

    def open(self):
        self.send_initial()

    def send_initial(self):
        initial_message = generate_json()
        self.write_message(initial_message)
        DataHandler.clients.add(self)


@gen.coroutine
def send_update(measurement):
    DataHandler.meritve.append(measurement)
    msg = measurement
    for client in DataHandler.clients.copy():
        try:
            client.write_message(msg)
        except websocket.WebSocketClosedError:
            try:
                DataHandler.clients.remove(client)
            except:
                pass


def generate_json(num=None):
    date = []
    if num is not None:
        data = data[-num:]
    resp = {}
    return json.dumps(resp)


@gen.coroutine
def reader(ioloop):
    while True:
        try:
            cmd = ['python', os.path.join(os.path.dirname(__file__), reader_py), sensor_name]
            proc = process.Subprocess(cmd, stdout=process.Subprocess.STREAM)

            while True:
                line = yield proc.stdout.read_until(DELIMITER)
                print('Got json? %r' % line)
                try:
                    measurement = json.loads(line)
                except ValueError:
                    sys.stderr.write("Got invalid JSON: %r" % line)
                    continue
                t = int((time.time() - time.altzone)*1000)
                measurement["time"] = t
                #print(measurement)
                ioloop.add_callback(send_update, measurement)
        except:
            traceback.print_exc()
            yield gen.sleep(10)


def main():
    app = web.Application([
        (r"/", MainHandler),
        (r"/data", DataHandler),
        (r'/static/(.*)', web.StaticFileHandler, {'path': STATIC_PATH}),
    ])
    app.listen(port_id)   # Set the webserver TCP port
    print('Starting Tornado web server...')
    print('Open URL: http://localhost:' + str(port_id) + '/') 
    ioloop = tornado.ioloop.IOLoop.current()
    ioloop.add_callback(reader, ioloop)
    ioloop.start()

if __name__ == "__main__":
    main()
