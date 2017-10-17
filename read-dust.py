#!/usr/bin/python

# Application for reading data from SDS011, SDS018 and SDS021 dust sensors.
# USAGE: "python dust.py" or "python dust.py /dev/ttyUSB1"
#
# Forked from: https://github.com/aqicn/sds-sensor-reader
# For Arduino code see: https://github.com/FriskByBergen/SDS011

import os
import sys
import time
import serial

# Reopen sys.stdout with buffer size 0 (unbuffered)
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

# Set default USB port
USBPORT = "/dev/ttyUSB0"


class SDS021Reader:

    def __init__(self, inport):
        self.serial = serial.Serial(port=inport, baudrate=9600)

    def readValue( self ):
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


    def read( self ):
        species = [[],[]]

        while 1:
            try:
                values = self.readValue()
                species[0].append(values[0])
                species[1].append(values[1])

                sys.stdout.write('{')
                sys.stdout.write('  "metadata": {')
                sys.stdout.write('    "device_name": "Senzor trdnih delcev",')
                sys.stdout.write('    "device_btname": "DUST1",')
                sys.stdout.write('    "device_location": "CodeWeek",')
                sys.stdout.write('    "sensors": {')
                sys.stdout.write('      "pm25": ["PM 2.5", "SDS021", "ug/m3", "red"],')
                sys.stdout.write('      "pm10": ["PM 10", "SDS021", "ug/m3", "blue"]')
                sys.stdout.write('    }')
                sys.stdout.write('  },')

                t = int((time.time() - time.altzone)*1000)
                sys.stdout.write('  "time": %d,' % t)

                sys.stdout.write('  "data": {')

                sys.stdout.write('    "pm25": [%.2f,  %.2f],' % (values[0], 25.0))
                sys.stdout.write('    "pm10": [%.2f,  %.2f]' % (values[1], 50.0))

                sys.stdout.write('  }')
                sys.stdout.write('}\n')

                time.sleep(1)  # wait for one second
            except KeyboardInterrupt:
                sys.stderr.write('Quit!\n')
                sys.exit()
            except:
                e = sys.exc_info()[0]
                sys.stderr.write('Can not read the sensor data: '+ str(e) + '\n')

def loop(usbport):
    reader = SDS021Reader(usbport) 
    while 1:
        reader.read()

if len(sys.argv)==2:
    if sys.argv[1].startswith('/dev'):
        loop(sys.argv[1])
    else:
        loop(USBPORT)
else:
    loop(USBPORT)
