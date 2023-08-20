import time
import adafruit_fingerprint
from RPLCD.i2c import CharLCD
import RPi.GPIO as GPIO
from enroll_finger import enrollment
import mariadb
import sys

# Set the GPIO numbering mode
GPIO.setmode(GPIO.BCM)
#This sets up the GPIO 18 pin as an output pin
GPIO.setup(24, GPIO.OUT)

##################


try:
    conn = mariadb.connect(
            user="root",
            password="csi",
            database="OUSS"
    )
except mariadb.Error as e:
    print(f"Error connecting to db: {e}")
    sys.exit(1)



def main():
    print("e for enroll\n")
    print("d for delete user\n")
    print("l for log viewing\n")
    print("r for reset library\n\n")

    decision = input("> ")

    if decision == "e":
        enrollment()


#reset
def reset_pins_table():
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM PINS")
        conn.commit()
        print("PINS table reset successful.")
    except mariadb.Error as e:
        print(f"Error resetting PINS table: {e}")


if __name__ == "__main__":
    main()

