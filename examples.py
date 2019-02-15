import GT_521F52
import time

try:
    p = GT_521F52.PyFingerprint_GT_521F52('/dev/ttyUSB0')

except Exception as e:
        print("Something went wrong")
        print('Exception message: ' + str(e))


try:
    print("Put your finger three times at the scanner to enrrol")
    p.enrollUser()
    print("Now lets identify you finger")
    time.sleep(2)
    pos = p.IdentifyUser()
    if(pos):
        print("Your finger was found at " + str(pos))
    #For other functions simply check the datasheet and the api
except Exception as e:
        print('Exception message: ' + str(e))