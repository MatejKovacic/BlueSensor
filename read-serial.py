#!/usr/bin/python
# coding: utf-8

# BlueSensor data reader for reading JSON data fro sensor via serial console (/dev/ttyUSB0,...)

import sys, os
import traceback
import datetime, time, pytz
from pprint import pprint
import serial
import json
import random

tz = pytz.timezone('Europe/Ljubljana')
va = [None]*6

def time_now_ms():
    tt = datetime.datetime.now(tz).timetuple()
    now = time.mktime(tt) + 3600 # WTF?!
    if tt.tm_isdst: now += 3600
    return int(now)*1000

def sim_value(n, max, fluc):
    global va
    plus = random.random() > 0.5
    diff = random.random()*(max*fluc/100)
    if va[n] is None: va[n] = max/2
    if plus: va[n] += diff
    else: va[n] -= diff
    if va[n] > max: va[n] -= 2*diff
    elif va[n] < 0: va[n] += 2*diff
    return va[n]

# Reopen stdout and stderr with buffer size 0 (unbuffered)
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 0)

if len(sys.argv) == 1:
    sys.stderr.write('This application must be called with parameter specifying ID of a USB port where BlueSensor is conneccted.\n')
    sys.stderr.write('For example: "read-serial.py 0" for reading from device connected to /dev/ttyUSB0.\n')
    sys.exit()

if sys.platform.startswith('win'):
    DEVNAME = 'COM'
elif sys.platform.startswith('darwin'):
    DEVNAME = '/dev/tty.'
else: # linux
    DEVNAME = '/dev/ttyUSB'
USBPORT = DEVNAME + sys.argv[1] # can be 'usbserialxxx' on Mac

simulate = len(sys.argv) > 2

if not simulate:
    ser = serial.Serial(port=USBPORT, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
    sys.stderr.write('Reading JSON data from ' + USBPORT + '...\n')
else:
    ser = None
    sys.stderr.write('Reading JSON data from simulated ' + USBPORT + '...\n')

while True:
    try:
        if not simulate:
            data_s = ser.readline().rstrip()
        else:
            data = {
                "metadata": {
                    "device_name": "Serial sensor",
                    "device_id": "SER1",
                    "device_location": "IJS",
                    "sensors": {
                        "gas1": ["Gas 1", "Gas 1", "raw value", "black"],
                        "gas2": ["Gas 2", "Gas 2", "raw value", "green"],
                        "humidity": ["Hum 1", "DHT-22", "%", "blue"],
                        "temp1": ["Temp 1", "DHT-22", "°C", "orange"],
                        "temp2": ["Temp 2", "DS18B20", "°C", "red"],
                        "temp3": ["Temp 3", "DS18B20", "°C", "yellow"]
                    }
                },
                "time": 0,
                "data": {
                    "gas1": round(sim_value(0, 10, 20), 2),
                    "gas2": round(sim_value(1, 10, 20), 2),
                    "humidity": round(sim_value(2, 100, 5), 2),
                    "temp1": round(sim_value(3, 50, 2), 2),
                    "temp2": round(sim_value(4, 50, 2), 2),
                    "temp3": round(sim_value(5, 50, 2), 2)
                }
            }
            data_s = json.dumps(data)

        t = time_now_ms()

        data = json.loads(data_s)
        if data['time'] is None or data['time'] == 0:
            data['time'] = t
        data_s = json.dumps(data)

        sys.stdout.write(data_s + '\n')

        time.sleep(1) # wait 1 second
    except KeyboardInterrupt:
        sys.stderr.write('Quit!\n')
        sys.exit()
    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        exc = traceback.format_exception_only(exc_type, exc_obj)
        f_name = sys._getframe().f_code.co_name
        err = '{}({}): '.format(f_name, exc_tb.tb_lineno) + exc[-1].strip()
        sys.stderr.write(err + '\n')
        time.sleep(1) # wait 1 second
