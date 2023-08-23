import adafruit_fingerprint
import RPi.GPIO as GPIO
import time
import mariadb
import sys
import serial
from enroll_finger import enrollment
from tabulate import tabulate
from datetime import datetime


# Set the GPIO numbering mode
GPIO.setmode(GPIO.BCM)
#This sets up the GPIO 18 pin as an output pin
GPIO.setup(24, GPIO.OUT)

#RPi Initialization
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)

#Fingerprint Initialization
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

try:
    conn = mariadb.connect(
            user="root",
            password="csi",
            database="OUSS"
    )
except mariadb.Error as e:
    print(f"Error connecting to db: {e}")
    sys.exit(1)

##################

###RESETS
def reset_users_table():
    try:
        cur = conn.cursor()

        # Disable foreign key checks temporarily
        cur.execute("SET FOREIGN_KEY_CHECKS=0")

        # Delete records from the users table
        cur.execute("DELETE FROM users")
        conn.commit()

        # Enable foreign key checks
        cur.execute("SET FOREIGN_KEY_CHECKS=1")

        if finger.empty_library() == adafruit_fingerprint.OK:
            print("Library empty!")

        print("users table reset successful.")

    except mariadb.Error as e:
        # Check for the specific foreign key constraint error
        if "foreign key constraint fails" in str(e).lower():
            print("You must reset the logs table before resetting the user's library.")
        else:
            print(f"Error resetting users table: {e}")


def reset_logs_table():
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM logs")
        conn.commit()
        print("logs table reset successful.")
    except mariadb.Error as e:
        print(f"Error resetting logs table: {e}")

###############

###Searches

def format_login_time(login_time):
    hours, remainder = divmod(login_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def format_logs_table(results):
    print(results)
    headers = ["Log ID", "User ID", "User Name", "Login Time", "Login Date"]
    data = []

    for row in results:
        log_id, user_id, user_name, login_time, login_date = row
        login_time_formatted = format_login_time(login_time)
        login_date_formatted = login_date.strftime("%Y-%m-%d")
        data.append([log_id, user_id, user_name, login_time_formatted, login_date_formatted])

    return tabulate(data, headers, tablefmt="fancy_grid")

def format_users_table(results):
    headers = ["Name", "PIN"]
    data = []

    for row in results:
        name, pin = row
        data.append([name, pin])

    return tabulate(data, headers, tablefmt="fancy_grid")

def select_all_logs():
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM logs"
        cursor.execute(query)
        results = cursor.fetchall()
        return format_logs_table(results)
    except mariadb.Error as e:
        return f"Error: {e}"

def search_logs(search_value):
    try:
        cursor = conn.cursor()

        # Define the query to search multiple columns using LIKE for partial matches
        query = """
        SELECT * FROM logs
        WHERE user_name LIKE ? OR login_date = ? OR login_time LIKE ?
        """
        
        # Add '%' to the search value for partial matches in user_name and login_time
        search_value_with_wildcards = f"%{search_value}%"
        
        # Check if the search_value is a valid date in 'YYYY-MM-DD' format
        try:
            datetime.strptime(search_value, '%Y-%m-%d')
            cursor.execute(query, (search_value_with_wildcards, search_value, search_value_with_wildcards))
        except ValueError:
            # If it's not a valid date, only perform partial matches on user_name and login_time
            cursor.execute(query, (search_value_with_wildcards, search_value, search_value_with_wildcards))
        
        results = cursor.fetchall()
        return format_logs_table(results)
    except mariadb.Error as e:
        return f"Error: {e}"


def search_users_by_name(search_name):
    try:
        cursor = conn.cursor()

        # Define the query to search for a specific name
        query = """
        SELECT name, pin FROM users
        WHERE name LIKE ?
        """
        
        # Add '%' to the search_name for partial matches
        search_name_with_wildcards = f"%{search_name}%"
        
        cursor.execute(query, (search_name_with_wildcards,))
        results = cursor.fetchall()
        
        # Return the raw results (list of tuples)
        return results

    except mariadb.Error as e:
        print(f"Error: {e}")
        return None
    

def search_and_format_users(search_name):
    try:
        # Search for users by name and get the raw results
        search_results = search_users_by_name(search_name)

        if search_results:
            # Format the results using format_users_table
            formatted_results = format_users_table(search_results)
            return formatted_results
        else:
            return "No users found with the provided name."

    except mariadb.Error as e:
        print(f"Error: {e}")
        return None


def delete_user_by_name(name_to_delete):
    try:
        cursor = conn.cursor()

        # Search for users by name
        search_results = search_users_by_name(name_to_delete)

        if not search_results:
            print("No users found with the provided name.")
            return

        formatted_results = format_users_table(search_results)
        print(formatted_results)
        # Ask for confirmation
        confirmation_name = input("Enter the name to confirm deletion: ")

        # Disable foreign key checks temporarily
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")

        if confirmation_name == name_to_delete:
            # Delete the user by name
            delete_query = """
            DELETE FROM users
            WHERE name = ?
            """
            cursor.execute(delete_query, (name_to_delete,))
            conn.commit()
            print(f"User '{name_to_delete}' deleted successfully.")
            
            # Enable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS=1")

        else:
            print("Deletion canceled. Name confirmation does not match.")

    except mariadb.Error as e:
        print(f"Error: {e}")

#########################

### Main

def main_loop():

    print("\ne for enroll")
    print("l for log viewing")
    print("ls for log searching")
    print("us for user searching")
    print("r for reset library")
    print("rl for reset logs")
    print("d for delete user\n")

    decision = input("> ")
    print("\n")

    if decision == "e":
        enrollment()

    elif decision == "r":
        reset_users_table()

    elif decision == "d":
        search_criterea = input("Enter what name you want to search the users table for: ")
        delete_user_by_name(search_criterea)

    elif decision == "l":
        print(select_all_logs())

    elif decision == "ls":
        search_criterea = input("Enter what you want to search the log table for: ")
        print(search_logs(search_criterea))

    elif decision == "us":
        search_criterea = input("Enter what name you want to search the users table for: ")
        print(search_and_format_users(search_criterea))

    elif decision == "rl":
        reset_logs_table()

    else:
        print("Invalid Input.")


def main():
    while True:
        main_loop()
        

if __name__ == "__main__":
    main()

