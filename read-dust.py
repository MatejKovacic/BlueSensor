#!/usr/bin/python
# coding: utf-8

# Application for reading data from SDS011, SDS018 and SDS021 dust sensors.
# Usage: "python dust.py 0" for reading from /dev/ttyUSB0
#
# Forked from: https://github.com/aqicn/sds-sensor-reader
# For Arduino code see: https://github.com/FriskByBergen/SDS011

import sys, os
import traceback
import datetime, time, pytz
from pprint import pprint
import serial
import json
import random

tz = pytz.timezone('Europe/Ljubljana')
va = [None]*2

def print_exc(f_name, msg=''):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    exc = traceback.format_exception_only(exc_type, exc_obj)
    err = '{}({}): {}'.format(f_name, exc_tb.tb_lineno, msg) + exc[-1].strip()
    sys.stderr.write(err + '\n')
    sys.stderr.flush()

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

class SDS021_Reader:
    def __init__(self, inport, simulate=False):
        self.simulate = simulate
        if not self.simulate:
            try:
                self.serial = serial.Serial(port=inport, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
            except:
                print_exc(sys._getframe().f_code.co_name)
                sys.exit(1)
            sys.stderr.write('Reading DUST data from ' + inport + '...\n')
            sys.stderr.flush()
        else:
            self.serial = None
            sys.stderr.write('Reading DUST data from simulated ' + inport + '...\n')
            sys.stderr.flush()

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
                    values.append(sim_value(0, 25, 10))
                    values.append(sim_value(1, 50, 10))

                t = time_now_ms()
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
                        "pm25": round(values[0], 2),
                        "pm10": round(values[1], 2)
                    }
                }
                data_s = json.dumps(data)

                sys.stdout.write(data_s + '\n')
                sys.stdout.flush()

                time.sleep(1) # wait 1 second
            except KeyboardInterrupt:
                sys.stderr.write('Quit!\n')
                sys.stderr.flush()
                sys.exit(0)
            except:
                print_exc(sys._getframe().f_code.co_name)
                time.sleep(1) # wait 1 second

# Reopen stdout and stderr with buffer size 0 (unbuffered) - only in python 2.7
#sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
#sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 0)

if len(sys.argv) == 1:
    sys.stderr.write('This application must be called with parameter specifying ID of a USB port where BlueSensor is conneccted.\n')
    sys.stderr.write('For example: "read-serial.py 0" for reading from device connected to /dev/ttyUSB0.\n')
    sys.stderr.flush()
    sys.exit()

if sys.platform.startswith('win'):
    DEVNAME = 'COM'
elif sys.platform.startswith('darwin'):
    DEVNAME = '/dev/tty.'
else: # linux
    DEVNAME = '/dev/ttyUSB'
USBPORT = DEVNAME + sys.argv[1] # can be 'usbserialxxx' on Mac

simulate = len(sys.argv) > 2

reader = SDS021_Reader(USBPORT, simulate)
while True:
    reader.read()
