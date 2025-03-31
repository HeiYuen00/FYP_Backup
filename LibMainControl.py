import yaml
import LibCamera as Cam
import LibLC as LC
import LibMotion as Motion
import time as t 

def Read_initcfg():
    with open('initcfg.yaml') as f:
            cfg = yaml.load(f, Loader=yaml.FullLoader)
    return cfg

def Read_Collectcfg():
     a = []
     with open ('collectmodecfg.txt') as f:
          for line in f:
               print(line.split())
               a.append(line.split())
          print(a)
     return a
def Start_test(MC_Test_Handle):
    #print(MC_Test_Handle)
     if(MC_Test_Handle["Mode"] is True and MC_Test_Handle["MeasureMode"] is True):
        print("MeasureMode Flow")    
        return 1,0  
     elif(MC_Test_Handle["Mode"] is True and MC_Test_Handle["CollectMode"] is True):
        print("CollectMode Flow")
        CollectModeSetting = Read_Collectcfg()
        LC.TurnOn(1, CollectModeSetting[4][0],CollectModeSetting[4][1],CollectModeSetting[4][2],CollectModeSetting[4][3])
        return 2,CollectModeSetting
     else:
        LC.TurnOn(MC_Test_Handle["LC"],MC_Test_Handle["LCIO1"],MC_Test_Handle["LCIO2"],
                 MC_Test_Handle["LCIO3"],MC_Test_Handle["LCIO4"])
        #ChangeMotorStatus(MC_Test_Handle["Motion"])
        return 3,0  
"""     if(MC_Test_Handle["Mode"] is True and MC_Test_Handle["MeasureMode"] is True):
        print("MeasureMode Flow")
        #TODO Measure Mode
        return 1,0"""
        #1. Grab Img 
        #2. Pass to model collect the result 
        #3. Motion compensation
        #4. Grab Img again
        #5. Pass to model collect the result  


#LC Control Part   
def InitLCIO():
     LC.Init()

def CleanUpLC():
     LC.CleanUpPin()

def ResetLC():
     LC.TurnOff_All()



#Camera Control Part
def InitCam():
     Cam.InitCam()

def ReleaseCam():
     ReleaseCam()

def ModifyCamConfig(item, value):
     if item == "ExposureTime":   
          Expo_us = int(value*1000000)
          Cam.ModifyCamConfig(item,Expo_us)
          for dumpgrab in range(5):
               Cam.GrabImage()
     else: Cam.ModifyCamConfig(item, value)

def GrabImg():
     image = Cam.GrabImage()
     return image



#Motion Control Part 
def GetMoveDistX(X_Loc_Target,X_Loc_Real):
     X_Dist =  X_Loc_Target - X_Loc_Real #Get the distance need to move
     Motion.MoveX(X_Dist)  #Send to arduino
     X_Loc_Real = X_Loc_Target 
     return X_Loc_Real

def GetMoveDistY(Y_Loc_Target,Y_Loc_Real):
     Y_Dist =  Y_Loc_Target - Y_Loc_Real #Get the distance need to move
     Motion.MoveY(Y_Dist) #Send to arduino
     Y_Loc_Real = Y_Loc_Target
     return Y_Loc_Real

def GetMoveAngle(Angle):
     Motion.MoveAngle(Angle)
