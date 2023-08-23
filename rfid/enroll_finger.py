from RPLCD.i2c import CharLCD
import serial
import RPi.GPIO as GPIO
import time
import sys
import mariadb
from mfrc522 import SimpleMFRC522

#LCD Initialization
lcd = CharLCD('PCF8574', 0x27)

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
def enroll_rfid(id, pin, name):
    reader = SimpleMFRC522()

    try:
        print("Hold RFID card up to reader...")
        num = get_next_id()
        reader.write(str(num))
        add_entry(id, pin, name)
    finally:
        GPIO.cleanup()

def enrollment():
    enroll_rfid(get_next_id(), get_pin(), get_name())
