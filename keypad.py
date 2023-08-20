import RPi.GPIO as GPIO
import time
#Keypad Stuff

# Define pin numbers for the keypad
L1 = 5
L2 = 6
L3 = 13
L4 = 19

C1 = 12
C2 = 16
C3 = 20
C4 = 21

# Set up GPIO for keypad
def setup_keypad():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(L1, GPIO.OUT)
    GPIO.setup(L2, GPIO.OUT)
    GPIO.setup(L3, GPIO.OUT)
    GPIO.setup(L4, GPIO.OUT)

    GPIO.setup(C1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(C2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(C3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(C4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Function to read from the pin pad
def read_pin_pad():
    # List of characters arranged as per your keypad
    characters = [
        ["1", "2", "3", "A"],
        ["4", "5", "6", "B"],
        ["7", "8", "9", "C"],
        ["*", "0", "#", "D"]
    ]
    
    # Loop through each row of the keypad
    for row_num, row_pin in enumerate([L1, L2, L3, L4]):
        GPIO.output(row_pin, GPIO.HIGH)  # Activate the current row
        
        # Loop through each column of the keypad
        for col_num, col_pin in enumerate([C1, C2, C3, C4]):
            if GPIO.input(col_pin) == GPIO.HIGH:
                # Key is pressed, return the corresponding character
                return characters[row_num][col_num]
        
        GPIO.output(row_pin, GPIO.LOW)  # Deactivate the current row
    
    return None  # No key pressed

def readLine(line, characters):
    GPIO.output(line, GPIO.HIGH)
    
    if GPIO.input(C1) == 1:
        while GPIO.input(C1) == 1:
            pass
        return characters[0]
    if GPIO.input(C2) == 1:
        while GPIO.input(C2) == 1:
            pass
        return characters[1]
    if GPIO.input(C3) == 1:
        while GPIO.input(C3) == 1:
            pass
        return characters[2]
    if GPIO.input(C4) == 1:
        while GPIO.input(C4) == 1:
            pass
        return characters[3]
    
    GPIO.output(line, GPIO.LOW)
    return None

def wait_for_keypad_inputs(target_count):
    input_counter = 0
    inputs = []

    while input_counter < target_count:
        input_value = readLine(L1, ["1", "2", "3", "A"]) \
                    or readLine(L2, ["4", "5", "6", "B"]) \
                    or readLine(L3, ["7", "8", "9", "C"]) \
                    or readLine(L4, ["*", "0", "#", "D"])
                    
        if input_value is not None:
            input_counter += 1
            inputs.append(input_value)
            print(f"Input {input_counter}/{target_count}: {input_value}")
        
        time.sleep(0.1)

    return ''.join(inputs)


def pin_loop():
    try:
        setup_keypad()
        while True:
            target_count = 5
            pin = wait_for_keypad_inputs(target_count)
            time.sleep(2)  # Wait for 2 seconds before the next iteration
    except KeyboardInterrupt:
        print("\nApplication stopped!")
    finally:
        GPIO.cleanup()  # Clean up GPIO on application exit
