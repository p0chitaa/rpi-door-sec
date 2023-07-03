import os
import subprocess

# Delete the file "main.py"
try:
    os.remove("main.py")
    print("File 'main.py' deleted successfully.")
except FileNotFoundError:
    print("File 'main.py' does not exist.")

# Run the command 'nano main.py'
subprocess.call(["nano", "main.py"])
