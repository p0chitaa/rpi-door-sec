# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

'''
--------ATTENTION CSI4999 GROUPMATES--------
The code below was taken directly from Adafruit's website, and was used to verify that the
fingerprint scanner was working properly and didn't need to be replaced

It looks really compicated, but the code is broken down into it's 5 main function that are
then called by get_num() function later on

Everything else is fairly straight forward

DO NOT UNCOMMENT ANY OF THE LINES BETWEEN THE IMPORTS AND THE get_fingerprint()FUNCTION

IT WILL BREAK THE CODE

I left some comments that further explain wha everything does to hopefully negate this.

'''
import time
import serial
import adafruit_fingerprint
from RPLCD.i2c import CharLCD

# import board
# uart = busio.UART(board.TX, board.RX, baudrate=57600)

# If using with a computer such as Linux/RaspberryPi, Mac, Windows with USB/serial converter:
#uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)

# If using with Linux/Raspberry Pi and hardware UART:
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)

# If using with Linux/Raspberry Pi 3 with pi3-disable-bt
#uart = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

# Use dir() to get the attributes and methods of the Adafruit_Fingerprint object
print(dir(finger))
