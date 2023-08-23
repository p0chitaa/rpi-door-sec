import time
from RPLCD.i2c import CharLCD
import RPi.GPIO as GPIO
from fingerprint_match import scan_loop


# Set the GPIO numbering mode
GPIO.setmode(GPIO.BCM)
#This sets up the GPIO 18 pin as an output pin
GPIO.setup(24, GPIO.OUT)

lcd = CharLCD('PCF8574', 0x27)

##################

lcd.clear()
def main():
    while True:
        scan_loop()
if __name__ == "__main__":
    main()

