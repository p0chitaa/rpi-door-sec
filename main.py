import time
import adafruit_fingerprint
from RPLCD.i2c import CharLCD
import RPi.GPIO as GPIO
from fingerprint_match import scan_loop


# Set the GPIO numbering mode
GPIO.setmode(GPIO.BCM)
#This sets up the GPIO 18 pin as an output pin
GPIO.setup(24, GPIO.OUT)

##################

def main():
    while True:
        scan_loop()
if __name__ == "__main__":
    main()

