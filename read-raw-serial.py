#!/usr/bin/python
# coding: utf-8

# Python application for reading raw (comma-delimited) data from BlueSensor via serial console (/dev/ttyUSB0).

import sys, os
import traceback
import datetime, time
import serial
import json
import random

# Reopen sys.stdout with buffer size 0 (unbuffered)
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

if len(sys.argv) == 1:
    sys.stderr.write('This application must be called with parameter specifying USB port.\n')
    sys.stderr.write('Use 0 for /dev/ttyUSB0, 1 for /dev/ttyUSB1, etc.\n')
    sys.exit()

USBNUM = str(sys.argv[1])
if (sys.argv[1].isdigit()):
    USBPORT = "/dev/ttyUSB" + USBNUM
else:
    USBPORT = "/dev/ttyUSB0"

if (len(sys.argv) > 2):
    simulate = True
else:
    simulate = False

if not simulate:
    ser = serial.Serial(port=USBPORT, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
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
           values.append('Gas 1'); values.append(random.random())
           values.append('Gas 2'); values.append(random.random())
           values.append('Hum 1'); values.append(random.random()*100)
           values.append('Temp 1'); values.append(random.random()*35)
           values.append('Temp 2'); values.append(random.random()*35)
           values.append('Temp 3'); values.append(random.random()*35)

        t = int((time.time() - time.altzone)*1000)

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
                "gas1": [round(values[4], 2), 0],
                "gas2": [round(values[6], 2), 0],
                "humidity": [round(values[8], 2), 100],
                "temp1": [round(values[10], 2), 50],
                "temp2": [round(values[12], 2), 50],
                "temp3": [round(values[14], 2), 50]
            }
        }
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
