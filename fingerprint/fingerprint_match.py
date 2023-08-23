import adafruit_fingerprint
from RPLCD.i2c import CharLCD
import serial
import RPi.GPIO as GPIO
import time
import sys
import mariadb
from datetime import datetime

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



############## Find/Match Process

#function to check if id and pin match for selected fingerprint
def check_pin_match(fingerprint_id, entered_pin):
    cur = conn.cursor()
    cur.execute("SELECT EXISTS (SELECT 1 FROM users WHERE id=? AND pin=?)", (fingerprint_id, entered_pin))
    return cur.fetchone()[0] == 1

#function to unlock the electronic lock for 5s
def unlock():
    # Open the lock (initial state)
    GPIO.output(24, 0)  # Assuming GPIO pin 24 controls the lock
    time.sleep(5)       # Wait for stability
    
    # Close the lock
    GPIO.output(24, 1)  # Turn on relay to close the lock
    time.sleep(1)    # Wait for the lock to close

#check if certain id exists in the database
def check_id_exists(id_to_check):
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE id=?", (id_to_check,))
    return cur.fetchone() is not None

#Just a print statement for the lcd screen upon successful login
def show_fingerprint_result(fingerprint_id):
    if fingerprint_id is not None:
        #success = "Welcome #" + str(fingerprint_id)
        print("Detected #", fingerprint_id, "with confidence", finger.confidence)
        lcd.clear()
        #lcd.write_string(success)
        lcd.write_string("Enter PIN...")
        time.sleep(1)
    else:
        for _ in range(3):
            lcd.clear()
            lcd.write_string("Finger not\r\nfound...")
            time.sleep(1)
            lcd.clear()
            time.sleep(1)
        print("Finger not found")


def log_user_login(user_id):
    cursor = conn.cursor()

    # Get the user's name from the "users" table based on the user_id
    cursor.execute("SELECT name FROM users WHERE id = ?", (user_id,))
    user_name = cursor.fetchone()[0]

    # Get the current time and date
    current_time = datetime.now().strftime('%H:%M:%S')
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Insert the log entry into the "logs" table
    cursor.execute("INSERT INTO logs (user_id, user_name, login_time, login_date) VALUES (?, ?, ?, ?)",
                    (user_id, user_name, current_time, current_date))
    
    # Commit the transaction
    conn.commit()



#Fingerprint match function, returns fingerprint id
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

#def get_username():
#    cur = conn.cursor()
#    name = cur.execute("SELECT name from users WHERE id=?", (fingerprint_id,))

#Once finger is matched and id is returned, check id with pin in database

def get_username_by_id(user_id):
    cursor = conn.cursor()

    # Query to select the name from the 'users' table based on the provided ID
    query = "SELECT name FROM users WHERE id = ?"

    # Execute the query with the user_id as a parameter
    cursor.execute(query, (user_id,))

    # Fetch the result (assuming there's only one result, as IDs should be unique)
    result = cursor.fetchone()

    # Close the database connection
    # conn.close()

    # Check if a result was found
    if result:
        return result[0]  # Return the first (and only) column, which is the name
    else:
        return None  # Return None if no user with the given ID was found

def verify_fingerprint_pin(fingerprint_id):
    name = get_username_by_id(fingerprint_id)
    if check_id_exists(fingerprint_id):
        pin_digits = []
        pin_length = 4
        
        # Set up the keypad
        from keypad import setup_keypad
        setup_keypad()
        
        lcd_string = ""
        while len(pin_digits) < pin_length:
            from keypad import read_pin_pad
            input_value = read_pin_pad()
            if input_value is not None and input_value.isdigit():
                pin_digits.append(input_value)
                lcd.clear()
                lcd_string += str(input_value)
                lcd.write_string(lcd_string)
                print(f"Entered PIN: {''.join(pin_digits)}{'*'*(pin_length - len(pin_digits))}")
                time.sleep(0.1)
        
        entered_pin = ''.join(pin_digits)

        if check_pin_match(fingerprint_id, entered_pin):
            print("Fingerprint and PIN verified successfully.")        
            name_string = f"Welcome\r\n{name}!"
            lcd.clear()
            lcd.write_string(name_string)

            unlock()
            log_user_login(fingerprint_id)
            # You can perform additional actions here if needed
        else:
            print("Incorrect PIN. Please try again.")
    else:
        print("Fingerprint ID not found in the database.")


def scan_loop():
    fingerprint_id = capture_and_process_fingerprint()
    if fingerprint_id is not None:
        verify_fingerprint_pin(fingerprint_id)
    else:
        lcd.clear()
        lcd.write_string("Finger not found...\r\nTry again.")
        time.sleep(1)
        lcd.clear()
        time.sleep(1)
        lcd.write_string("Finger not found...\r\nTry again.")
        time.sleep(1)
        lcd.clear()
        time.sleep(1)
