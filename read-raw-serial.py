#coding: utf-8
#!/usr/bin/python
# Python application for reading raw (comma-delimited) data from BlueSensor via serial console (/dev/ttyUSB0).

import json
import os
import serial
import sys
import time

if len(sys.argv) == 1:
    sys.stderr.write('This application must be called with parameter specifying USB port.\n')
    sys.stderr.write('Use 0 for /dev/ttyUSB0, 1 for /dev/ttyUSB1, etc.\n')
    sys.exit()

USBNUM = str(sys.argv[1])
if (sys.argv[1].isdigit()):
  USBPORT = "/dev/ttyUSB" + USBNUM
else:
  USBPORT = "/dev/ttyUSB0"

ser = serial.Serial(port=USBPORT, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
sys.stderr.write('Reading raw data from ' + USBPORT + '...\n')

while True:
    t = int((time.time() - time.altzone)*1000)
    sensordata = ser.readline().rstrip()
    values = [str(i) for i in sensordata.split(',')]        

    data = {
        "metadata": {
            "device_name": str(values[0]),
            "device_btname": str(values[1]),
            "device_location": str(values[2]),
            "sensors": {
                "gas1": [str(values[3]), "Gas 1", "raw value", "black"],
                "gas2": [str(values[5]), "Gas 2", "raw value", "green"],
                "humidity": [str(values[7]), "DHT-22", "%", "blue"],
                "temp1": [str(values[9]), "DHT-22", "°C", "orange"],
                "temp2": [str(values[11]), "DS18B20", "°C", "red"],
                "temp3": [str(values[13]), "DS18B20", "°C", "yellow"],
            }
        },
        "time": t,
        "data": {
            "gas1": [values[4], 0],
            "gas2": [values[6], 0],
            "humidity": [values[8], 0],
            "temp1": [values[10], 0],
            "temp2": [values[12], 0],
            "temp3": [values[14], 0],
        }
    }

    sys.stdout.write(json.dumps(data) + '\n')
    sys.stdout.flush()
