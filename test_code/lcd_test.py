from signal import signal, SIGTERM, SIGHUP, pause
from rpi_lcd import LCD

'''
Hey team,

There are some things working behind the scenes here that make the LCD work

I've imported  a bunch of stuff from signal and rpi_lcd libraries and here 
a few  things you should know about implementing them:

1) Both libraries need to be installed on the rpi. They are not standard
2) When we write our final code we can simply import the whole library rather than the 
   individual components. I did that to test stuff
3) The default channel that the  LCD uses is 27. If you are unable to get things to print
   to the LCD you need to check if something got switched around on the rpi
4) If you are curious about the function that you can use, google the libraries  listed above 
'''


lcd = LCD()

def safe_exit(signum, frame):
    exit(1)

try:
    signal(SIGTERM, safe_exit)
    signal(SIGHUP, safe_exit)

    lcd.text("Hello,", 1)
    lcd.text("Raspberry Pi!", 2)

    pause()

except KeyboardInterrupt:
    pass

finally:
    lcd.clear()
