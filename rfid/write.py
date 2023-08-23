#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

#this code imports the simppleMFRC522 Library and allows the pi to talk with th>
#it simply takes a copy of the tool and stor it as a varible that can be used

reader = SimpleMFRC522()

try:
        text = input('New data:')
        print("Now place your tag to write")
        reader.write(text)
        print("Written")
finally:
        GPIO.cleanup()
