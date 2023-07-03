'''
SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
SPDX-License-Identifier: MIT
The code is broken down into it's 5 main function that are
then called by get_num() function later on
'''

import time
import serial
import adafruit_fingerprint
from RPLCD.i2c import CharLCD
import mysql.connector 
import numpy as np
from PIL import Image
import pymysql
import pickle
import io
import array
import struct


# If using with Linux/Raspberry Pi and hardware UART:
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart) #initializes fingerprint object or sensor
lcd = CharLCD('PCF8574', 0x27) #initializes LCD screen


#Database Information
db_host = "localhost"
db_user = "root"
db_pass = "csi"
db_database = "OUSS"
db_table = "fpDATA"


##################################################

### ENROLLMENT ###
def enroll_finger():
    """Take two finger images, convert to templates, and store in 'fpDATA' table"""
    fingerprint_templates = []

    for fingerimg in range(1, 3):
        # Capture fingerprint images
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

        # Template the captured fingerprint image
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

        # Store the template data in the list
        fingerprint_templates.append(finger.templates)

    # Prompt the user for the first and last name
    print("Enter the first name:", end=" ")
    first_name = input().strip()
    print("Enter the last name:", end=" ")
    last_name = input().strip()

    # Store the fingerprint templates in the database
    store_fingerprint_templates_in_db(fingerprint_templates[0], fingerprint_templates[1], first_name, last_name)

    return True


### ENROLLMENT > DATABASE STORAGE ###
def convert_template_to_blob(template):
    """Convert the fingerprint template to a blob object"""
    return array.array('B', template).tobytes()

def store_fingerprint_templates_in_db(template1, template2, first_name, last_name):
    """Store the fingerprint templates in the 'fpDATA' table in the database"""
    try:
        # Connect to the database
        conn = pymysql.connect(host=db_host, user=db_user, password=db_pass, database=db_database)
        cursor = conn.cursor()

        # Convert templates to blobs
        blob_template1 = convert_template_to_blob(template1)
        blob_template2 = convert_template_to_blob(template2)

        # Insert the templates into the database
        sql = "INSERT INTO fpDATA (FirstName, LastName, TemplateData, TemplateData2) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (first_name, last_name, blob_template1, blob_template2))

        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        print("Fingerprint templates stored in the database successfully")

    except Exception as e:
        print("Error storing fingerprint templates in the database:", str(e))
        if 'conn' in locals() and conn.open:
            conn.rollback()
            conn.close()
        return False

    return True


### DATABASE RETRIEVAL ###

def retrieve_fingerprint_templates_from_db():
    try:
        # Connect to the database
        conn = pymysql.connect(host=db_host, user=db_user, password=db_pass, database=db_database)
        cursor = conn.cursor()

        # Retrieve the fingerprint templates from the database
        sql = "SELECT TemplateData, TemplateData2 FROM fpDATA"
        cursor.execute(sql)

        # Fetch the result
        result = cursor.fetchone()
        if result is not None:
            template1_data = result[0]
            template2_data = result[1]

            # Convert blob data back to template form
            template1 = array.array('B', template1_data).tolist()
            template2 = array.array('B', template2_data).tolist()

            # Return the templates
            return template1, template2

        else:
            print("No fingerprint templates found in the database")
            return None

    except Exception as e:
        print("Error retrieving fingerprint templates from the database:", str(e))
        if 'conn' in locals() and conn.open:
            conn.rollback()
            conn.close()
        return None

# Usage example
templates = retrieve_fingerprint_templates_from_db()
if templates is not None:
    template1, template2 = templates
    # Use the templates as needed
    print("Template 1:", template1)
    print("Template 2:", template2)







### idk yet ###
def convert_to_model(fingerprint_image):
    # Convert fingerprint image to model
    # Implementation specific to your fingerprint sensor/library
    model = finger.convert_to_model(fingerprint_image)
    return model



def get_fingerprint_image():
    """Scan fingerprint and return the image as a PIL Image object."""
    while finger.get_image():
        pass

    # Let PIL take care of the image headers and file structure
    from PIL import Image

    img = Image.new("L", (256, 288), "white")
    pixeldata = img.load()
    mask = 0b00001111
    result = finger.get_fpdata(sensorbuffer="image")

    # Unpack the data received from the fingerprint module and copy the image data to the "img" placeholder pixel by pixel.
    x = 0
    y = 0
    for i in range(len(result)):
        pixeldata[x, y] = (int(result[i]) >> 4) * 17
        x += 1
        pixeldata[x, y] = (int(result[i]) & mask) * 17
        if x == 255:
            x = 0
            y += 1
        else:
            x += 1

    return img

















##################################################

def main():
    """Main function for fingerprint example program"""
    while True:
        lcd.clear()
        lcd.write_string("Welcome to\r\nOUSS Inc.")
        print("----------------")
        if finger.read_templates() != adafruit_fingerprint.OK:
            raise RuntimeError("Failed to read templates")
        print("Fingerprint templates: ", finger.templates)
        if finger.count_templates() != adafruit_fingerprint.OK:
            raise RuntimeError("Failed to read templates")
        print("Number of templates found: ", finger.template_count)
        if finger.read_sysparam() != adafruit_fingerprint.OK:
            raise RuntimeError("Failed to get system parameters")
        print("Size of template library: ", finger.library_size)
        print("e) enroll print")
        print("f) find print")
        print("d) delete print")
        print("s) save fingerprint image")
        print("r) reset library")
        print("p) retrieve and print fingerprint data")
        print("2) print TemplateData for ID 2")
        print("q) quit")
        print("----------------")
        c = input("> ")

        if c == "e":
            enroll_finger()
        elif c == "f":
            if get_fingerprint():
                success = "Welcome #"+str(finger.finger_id)
                print("Detected #", finger.finger_id, "with confidence", finger.confidence)
                lcd.clear()
                lcd.write_string("Welcome #"+str(finger.finger_id))
                time.sleep(3)
            else:
                for i in range(3):
                    lcd.clear()
                    lcd.write_string("Finger not\r\nfound...")
                    time.sleep(1)
                    lcd.clear()
                    time.sleep(1)
                print("Finger not found")
        elif c == "d":
            if finger.delete_model(get_num(finger.library_size)) == adafruit_fingerprint.OK:
                print("Deleted!")
            else:
                print("Failed to delete")
        elif c == "s":
            if save_fingerprint_image("fingerprint.png"):
                print("Fingerprint image saved")
            else:
                print("Failed to save fingerprint image")
        elif c == "r":
            if finger.empty_library() == adafruit_fingerprint.OK:
                print("Library empty!")
            else:
                print("Failed to empty library")
        elif c == "p":
            retrieve_and_print_fpdata(db_host, db_user, db_pass, db_database, db_table)
        elif c == "2":
            template_data = retrieve_fingerprint_templates_from_db()
            if template_data is not None:
                template1, template2 = template_data
                print("TemplateData for ID 2:")
                print("TemplateData: ", template1)
                print("TemplateData2: ", template2)
            else:
                print("Error retrieving fingerprint templates for ID 2")
        elif c == "q":
            print("Exiting fingerprint example program")
            raise SystemExit


if __name__ == "__main__":
    main()
