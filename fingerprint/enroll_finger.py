import adafruit_fingerprint
from RPLCD.i2c import CharLCD
import serial
import RPi.GPIO as GPIO
import time
import sys
import mariadb

#RPi Initialization
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)

#LCD Initialization
lcd = CharLCD('PCF8574', 0x27)

#Fingerprint Initialization
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

#FP Max Library Size
max_fp_id_num = 240

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#connect to database
try:
    conn = mariadb.connect(
            user="root",
            password="csi",
            database="OUSS"
    )
except mariadb.Error as e:
    print(f"Error connecting to db: {e}")
    sys.exit(1)

#-------------------------------#

#Determine the next available id in the database (auto_increment)
def get_next_id():
    cursor = conn.cursor()

    # Execute an SQL query to get the highest user ID
    cursor.execute("SELECT MAX(id) FROM users")

    # Fetch the result
    highest_id = cursor.fetchone()[0]

    # Check if highest_id is None (i.e., no records in the table)
    if highest_id is None:
        next_id = 1
    else:
        next_id = highest_id + 1

    return next_id


#add entry to database
def add_entry(id, pin, name):
    cur = conn.cursor()
    cur.execute("INSERT INTO users (id, pin, name) VALUES (?, ?, ?)", (id, pin, name))
    conn.commit()
    cur.close()

#have the user enter their desired pin
def get_pin():
    while True:
        pin = input("Enter your 4 digit pin: ")
        if len(pin) != 4 or not pin.isdigit():
            print("Invalid PIN. Please enter a 4-digit number.")
            continue
        return pin

#have the user enter their name
def get_name():
    while True:
        name = input("Enter your full name: ")
        return name
    

#Enrolls in Flash Memory then calls add_entry to enroll in database
def enroll_finger(id, pin, name):
    """Take a 2 finger images and template it, then store in 'location'"""
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            lcd.clear()
            print("Place finger on sensor...", end="")
            lcd.write_string("Place finger\r\non sensor...")
        else:
            lcd.clear()
            print("Place same finger again...", end="")
            lcd.write_string("Place same\r\nfinger again...")

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Image taken")
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="")
            elif i == adafruit_fingerprint.IMAGEFAIL:
                print("Imaging error")
                return False
            else:
                print("Other error")
                return False

        print("Templating...", end="")
        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            print("Templated")
            lcd.clear()
            lcd.write_string("Done!")
        else:
            if i == adafruit_fingerprint.IMAGEMESS:
                print("Image too messy")
            elif i == adafruit_fingerprint.FEATUREFAIL:
                print("Could not identify features")
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                print("Image invalid")
            else:
                print("Other error")
            return False

        if fingerimg == 1:
            print("Remove finger")
            lcd.clear()
            lcd.write_string("Remove finger...")
            time.sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    print("Creating model...", end="")
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        print("Created")
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            print("Prints did not match")
        else:
            print("Other error")
        return False

    print("Storing model #%d..." % id, end="")
    #Store in FM
    i = finger.store_model(id)
    if i == adafruit_fingerprint.OK:
        #Store in database
        add_entry(id, pin, name)
        print("Stored")
    else:
        if i == adafruit_fingerprint.BADLOCATION:
            print("Bad storage location")
        elif i == adafruit_fingerprint.FLASHERR:
            print("Flash storage error")
        else:
            print("Other error")
        return False

    return True

def enrollment():
    enroll_finger(get_next_id(), get_pin(), get_name())