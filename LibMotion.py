import serial
import time


def MoveX(DistX):
    print(DistX)
    send = 0
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    ser.reset_input_buffer()
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            print(line)
            if((line == "Init done") & (send == 0) ):
                ser.write(bytes("x"+str(DistX), 'utf-8'))
                send = 1
            if (line == "Done" ):
                break

def MoveY(DistY):
    send = 0
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    ser.reset_input_buffer()
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            print(line)
            if((line == "Init done") & (send == 0) ):
                ser.write(bytes("y"+str(DistY), 'utf-8'))
                send = 1
            if (line == "Done" ):
                break

def MoveAngle(Angle):
    send = 0
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    ser.reset_input_buffer()
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            print(line)
            if((line == "Init done") & (send == 0) ):
                ser.write(bytes("a"+str(Angle), 'utf-8'))
                send = 1
            if (line == "Done" ):
                break