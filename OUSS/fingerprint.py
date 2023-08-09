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

#Connect to MARIADB, exit system if fail.
try:
    conn = mariadb.connect(
            user="root",
            password="csi",
            database="OUSS"
    )
except mariadb.Error as e:
    print(f"Error connecting to db: {e}")
    sys.exit(1)




#Enrollment Process (MariaDB)
def check_id_exists(id_to_check):
    cur = conn.cursor()
    cur.execute("SELECT id FROM PINS WHERE id=?", (id_to_check,))
    return cur.fetchone() is not None

def add_entry(id, pin):
    cur = conn.cursor()
    cur.execute("INSERT INTO PINS (id, pin) VALUES (?, ?)", (id, pin))
    conn.commit()
    cur.close()

#Enrollment Process Overall

def get_id():
    """Use input() to get a valid number from 0 to the maximum size
    of the library. Retry till success!"""
    while True:
        try:
            i = int(input("Enter ID # from 0-{}: ".format(max_fp_id_num - 1)))
            if 0 <= i < max_fp_id_num:
                if check_id_exists(i):
                    print("ID already exists in the database. Please choose another.")
                else:
                    return i
            else:
                print("Invalid ID. Please enter a number from 0 to {}.".format(max_fp_id_num - 1))
        except ValueError:
            print("Invalid input. Please enter a valid number.")


def get_pin():
    while True:
        pin = input("Enter your 4 digit pin: ")
        if len(pin) != 4 or not pin.isdigit():
            print("Invalid PIN. Please enter a 4-digit number.")
            continue
        return pin
    

#Enrolls in both Flash Memory & Database
def enroll_finger(location, pin):
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

    print("Storing model #%d..." % location, end="")
    #Store in FM
    i = finger.store_model(location)
    if i == adafruit_fingerprint.OK:
        #Store in database
        add_entry(location, pin)
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


############## Find/Match Process

def capture_and_process_fingerprint(template_number=1):
    """Capture a finger print image, template it, and return the fingerprint ID if matched."""
    lcd.clear()
    lcd.write_string("Place finger\r\non sensor...")
    print("Waiting for image...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    print("Templating...")
    lcd.clear()
    lcd.write_string("Searching...")
    if finger.image_2_tz(template_number) != adafruit_fingerprint.OK:
        return None
    print("Searching...")
    if finger.finger_search() != adafruit_fingerprint.OK:
        return None
    fingerprint_id = finger.finger_id
    show_fingerprint_result(fingerprint_id)  # Call the function here
    return fingerprint_id

def check_pin_match(fingerprint_id, entered_pin):
    cur = conn.cursor()
    cur.execute("SELECT EXISTS (SELECT 1 FROM PINS WHERE id=? AND pin=?)", (fingerprint_id, entered_pin))
    return cur.fetchone()[0] == 1

def unlock():
    # Open the lock (initial state)
    GPIO.output(24, 0)  # Assuming GPIO pin 24 controls the lock
    time.sleep(5)       # Wait for stability
    
    # Close the lock
    GPIO.output(24, 1)  # Turn on relay to close the lock
    time.sleep(1)    # Wait for the lock to close


def verify_fingerprint(fingerprint_id):
    if check_id_exists(fingerprint_id):
        pin_digits = []
        pin_length = 4
        
        # Set up the keypad
        from Modulessss.keypad import setup_keypad
        setup_keypad()

        while len(pin_digits) < pin_length:
            from Modulessss.keypad import read_pin_pad
            input_value = read_pin_pad()
            if input_value is not None and input_value.isdigit():
                pin_digits.append(input_value)
                print(f"Entered PIN: {''.join(pin_digits)}{'*'*(pin_length - len(pin_digits))}")
                time.sleep(0.1)
        
        entered_pin = ''.join(pin_digits)

        if check_pin_match(fingerprint_id, entered_pin):
            print("Fingerprint and PIN verified successfully.")
            unlock()
            # You can perform additional actions here if needed
        else:
            print("Incorrect PIN. Please try again.")
    else:
        print("Fingerprint ID not found in the database.")


def show_fingerprint_result(fingerprint_id):
    if fingerprint_id is not None:
        success = "Welcome #" + str(fingerprint_id)
        print("Detected #", fingerprint_id, "with confidence", finger.confidence)
        lcd.clear()
        lcd.write_string(success)
        time.sleep(1)
    else:
        for _ in range(3):
            lcd.clear()
            lcd.write_string("Finger not\r\nfound...")
            time.sleep(1)
            lcd.clear()
            time.sleep(1)
        print("Finger not found")


def scan_loop():
    fingerprint_id = capture_and_process_fingerprint()
    if fingerprint_id is not None:
        verify_fingerprint(fingerprint_id)


#reset
def reset_pins_table():
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM PINS")
        conn.commit()
        print("PINS table reset successful.")
    except mariadb.Error as e:
        print(f"Error resetting PINS table: {e}")