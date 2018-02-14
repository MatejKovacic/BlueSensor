#!/usr/bin/python
# coding: utf-8

# Application for reading data from SDS011, SDS018 and SDS021 dust sensors.
# Usage: "python dust.py 0" for reading from /dev/ttyUSB0
#
# Forked from: https://github.com/aqicn/sds-sensor-reader
# For Arduino code see: https://github.com/FriskByBergen/SDS011

import sys, os
import traceback
import datetime, time
import serial
import json
import random

class SDS021_Reader:
    def __init__(self, inport, simulate=False):
        self.simulate = simulate
        if not self.simulate:
            self.serial = serial.Serial(port=inport, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
            sys.stderr.write('Reading DUST data from ' + inport + '...\n')
        else:
            self.serial = None
            sys.stderr.write('Reading DUST data from simulated ' + inport + '...\n')

    def readValue(self):
        step = 0
        while True: 
            while self.serial.inWaiting() != 0:
                v = ord(self.serial.read())

                if step == 0:
                    if v == 170:
                        step = 1

                elif step == 1:
                    if v == 192:
                        values = [0,0,0,0,0,0,0]
                        step = 2
                    else:
                        step = 0

                elif step > 8:
                    step = 0
                    pm25 = (values[1]*256 + values[0])/10
                    pm10 = (values[3]*256 + values[2])/10
                    return [pm25,pm10]

                elif step >= 2:
                    values[step - 2] = v
                    step = step + 1

    def read(self):
        species = [[],[]]

        while True:
            try:
                if not self.simulate:
                    values = self.readValue()
                else:
                    values = []
                    values.append(random.random()*25)
                    values.append(random.random()*50)

                t = int((time.time() - time.altzone)*1000)
                species[0].append(values[0])
                species[1].append(values[1])

                data = {
                    "metadata": {
                        "device_name": "Senzor trdnih delcev",
                        "device_id": "DUST1",
                        "device_location": "IJS",
                        "sensors": {
                            "pm25": ["PM 2.5", "SDS021", "ug/m3", "red"],
                            "pm10": ["PM 10", "SDS021", "ug/m3", "blue"]
                        }
                    },
                    "time": t,
                    "data": {
                        "pm25": [round(values[0], 2), 25],
                        "pm10": [round(values[1], 2), 50]
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

# Reopen sys.stdout with buffer size 0 (unbuffered)
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

if len(sys.argv) == 1:
    sys.stderr.write('This application must be called with parameter specifying ID of a USB port where BlueSensor is conneccted.\n')
    sys.stderr.write('For example: "read-serial.py 0" for reading from device connected to /dev/ttyUSB0.\n')
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

reader = SDS021_Reader(USBPORT, simulate)
while True:
    reader.read()
