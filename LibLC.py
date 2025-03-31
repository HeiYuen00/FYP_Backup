import RPi.GPIO as GPIO

def Init(): 
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(15, GPIO.OUT,initial=GPIO.HIGH)
    GPIO.setup(19, GPIO.OUT,initial=GPIO.HIGH)
    GPIO.setup(11, GPIO.OUT,initial=GPIO.HIGH)
    GPIO.setup(13, GPIO.OUT,initial=GPIO.HIGH)

def TurnOn(Group, LCIO1,LCIO2,LCIO3,LCIO4):
    #For check LC status
    print("lc")
    print(Group)
    print(LCIO1)
    print(LCIO2)
    print(LCIO3)
    print(LCIO4)
    
    if(Group is True):
        if(LCIO1 is True):
            GPIO.output(15,GPIO.LOW)
        else: GPIO.output(15,GPIO.HIGH)
        if(LCIO2 is True):
            GPIO.output(19,GPIO.LOW)
        else: GPIO.output(19,GPIO.HIGH)    
        if(LCIO3 is True):
            GPIO.output(11,GPIO.LOW)
        else: GPIO.output(11,GPIO.HIGH)    
        if(LCIO4 is True):
            GPIO.output(13,GPIO.LOW)
        else: GPIO.output(13,GPIO.HIGH)
def TurnOff_All():
    GPIO.output(11,GPIO.HIGH)
    GPIO.output(13,GPIO.HIGH)
    GPIO.output(15,GPIO.HIGH)
    GPIO.output(19,GPIO.HIGH)

def CleanUpPin():
    GPIO.cleanup()
