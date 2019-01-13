#!/usr/bin/python
# coding: utf-8

# Python application for reading raw (comma-delimited) data from BlueSensor via serial console (/dev/ttyUSB0).

import sys, os
import traceback
import datetime, time, pytz
from pprint import pprint
import serial
import json
import random

tz = pytz.timezone('Europe/Ljubljana')
va = [None]*6

def print_exc(f_name, msg=''):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    exc = traceback.format_exception_only(exc_type, exc_obj)
    err = '{}({}): {}'.format(f_name, exc_tb.tb_lineno, msg) + exc[-1].strip()
    sys.stderr.write(err + '\n')

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
    sys.stderr.write('This application must be called with parameter specifying USB port.\n')
    sys.stderr.write('Use 0 for /dev/ttyUSB0, 1 for /dev/ttyUSB1, etc.\n')
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
    try:
        ser = serial.Serial(port=USBPORT, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
    except:
        print_exc(sys._getframe().f_code.co_name)
        sys.exit(1)
    sys.stderr.write('Reading RAW data from ' + USBPORT + '...\n')
else:
    ser = None
    sys.stderr.write('Reading RAW data from simulated ' + USBPORT + '...\n')

while True:
    try:
        if not simulate:
           sensordata = ser.readline().rstrip()
           values = [str(i) for i in sensordata.split(',')]        
        else:
           values = []
           values.append('Raw sensor')
           values.append('RAW1')
           values.append('IJS')
           values.append('Gas 1'); values.append(sim_value(0, 10, 20))
           values.append('Gas 2'); values.append(sim_value(1, 10, 20))
           values.append('Hum 1'); values.append(sim_value(2, 100, 5))
           values.append('Temp 1'); values.append(sim_value(3, 50, 2))
           values.append('Temp 2'); values.append(sim_value(4, 50, 2))
           values.append('Temp 3'); values.append(sim_value(5, 50, 2))

        t = time_now_ms()

        data = {
            "metadata": {
                "device_name": str(values[0]),
                "device_id": str(values[1]),
                "device_location": str(values[2]),
                "sensors": {
                    "gas1": [str(values[3]), "Gas 1", "raw value", "black"],
                    "gas2": [str(values[5]), "Gas 2", "raw value", "green"],
                    "humidity": [str(values[7]), "DHT-22", "%", "blue"],
                    "temp1": [str(values[9]), "DHT-22", "°C", "orange"],
                    "temp2": [str(values[11]), "DS18B20", "°C", "red"],
                    "temp3": [str(values[13]), "DS18B20", "°C", "yellow"]
                }
            },
            "time": t,
            "data": {
                "gas1": round(values[4], 2),
                "gas2": round(values[6], 2),
                "humidity": round(values[8], 2),
                "temp1": round(values[10], 2),
                "temp2": round(values[12], 2),
                "temp3": round(values[14], 2)
            }
        }
        data_s = json.dumps(data)

        sys.stdout.write(data_s + '\n')

        time.sleep(1) # wait 1 second
    except KeyboardInterrupt:
        sys.stderr.write('Quit!\n')
        sys.exit(0)
    except:
        print_exc(sys._getframe().f_code.co_name)
        time.sleep(1) # wait 1 second
