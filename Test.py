from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot
import sys
import LibMainControl as MC
from PIL import ImageQt,Image
import time as t 
import numpy as np
import os
import threading
import serial
import LibAlg

#TODO Add Logging
#TODO modify logic of mode part
#TODO Add Commment
#Global Variable
job = {
            "Camera": False,
            "Expo_Start": 0,"Expo_End": 0,"Expo_Step": 0,"Gain": 0,
            "NumGrab": 0,"Save": False,"SavePath": "",
            "LC": False,
            "LCIO1": False,
            "LCIO2": False,
            "LCIO3": False,
            "LCIO4": False,
            "Motion": False,
            "X_Start": 0,"X_End": 0,"X_Step": 0,
            "Y_Start": 0,"Y_End": 0,"Y_Step": 0,
            "Rot_Start": 0,"Rot_End": 0,"Rot_Step": 0,
            "Mode": False,
            "CollectMode": False,"Collectpath": "",
            "MeasureMode": False,
            "MeasureGround": False,
            "MeasureMoved": False,
            "MeasureGroundCompensated": False
            }



CLIENT = 0
X_global = 0.0
Y_global = 0.0
Angle_global = 0.0
event = threading.Event()
Motion_Request = threading.Event()
Motion_Done_Signal = threading.Event()
Activate_Logging = 1
Logging_Buffer = "Test"
Motion_Buffer ="e0"

Array_GroundCorners = 0
Array_MovedCorners = 0
Array_MovedCorners_afterangle = 0
Array_CompensatedCorners = 0
Array_Center = [[0,0],[0,0],[0,0],[0,0]]

############################################################################################################################################################
class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('Test.v2.ui', self)
        #from ultralytics import YOLO
        #global Model
        #Model = YOLO(f'March7_Confid80.pt')
        from inference_sdk import InferenceHTTPClient
        global CLIENT
        CLIENT = InferenceHTTPClient(
            api_url="https://detect.roboflow.com",
            api_key="hvu54wFnVifPgcQOh6TK"
        )
        #Assign func to each but
        self.But_Start.clicked.connect(self.Start_test)
        self.But_Stop.clicked.connect(self.Stop_test)
        self.But_Reset.clicked.connect(self.Reset_all)
        self.Check_Camera.toggled.connect(self.Change_CameraStatus)
        self.Check_LC.toggled.connect(self.Change_LCStatus)
        self.Check_Motion.toggled.connect(self.Change_MotionStatus)
        self.Check_Mode.toggled.connect(self.Change_ModeStatus)
        self.Check_CollectData.toggled.connect(self.Change_CollectModeStatus)
        self.Check_MeasureData.toggled.connect(self.Change_MeasureModeStatus)

        self.But_Measure_Ground.toggled.connect(self.Change_MeasureMode_Button_Status)
        self.But_Measure_Moved.toggled.connect(self.Change_MeasureMode_Button_Status)
        self.But_Measure_Compensation.toggled.connect(self.Change_MeasureMode_Button_Status)

        #self.Check_Measure.toggled.connect(self.Change_MeasureModeStatus)
        self.Change_Checkbox(True) #Init Check box
        self.Change_Checkbox(False) #Init Check box

        self.Init_input()

        if (Activate_Logging):
            global Logging_Buffer
            print("log activate")
            self.logging_thread = logging()
            self.logging_thread.start()
            Logging_Buffer = "Start Application"
            event.set()
        self.MotionControl_thread = MotionControlThread()
        self.MotionControl_thread.start()    
        self.show()

    def Init_input(self):
        #pre enter the input block
        cfg =  MC.Read_initcfg()
        self.Input_Cam_ExpoStart.setText(str(cfg['Expo_Start']))
        self.Input_Cam_ExpoEnd.setText(str(cfg['Expo_End']))
        self.Input_Cam_ExpoStep.setText(str(cfg['Expo_Step']))
        self.Input_Cam_Num.setText(str(cfg['Num']))
        self.Input_Cam_Gain.setText(str(cfg['Gain']))
        self.Input_Cam_Save.setText(str(cfg['Savepath']))

        self.Input_Motion_XStart.setText(str(cfg['X_Start']))
        self.Input_Motion_XEnd.setText(str(cfg['X_End']))
        self.Input_Motion_XStep.setText(str(cfg['X_Step']))
        self.Input_Motion_YStart.setText(str(cfg['Y_Start']))
        self.Input_Motion_YEnd.setText(str(cfg['Y_End']))
        self.Input_Motion_YStep.setText(str(cfg['Y_Step']))
        self.Input_Motion_RotStart.setText(str(cfg['Rot_Start']))
        self.Input_Motion_RotEnd.setText(str(cfg['Rot_End']))
        self.Input_Motion_RotStep.setText(str(cfg['Rot_Step']))       
        self.Input_CollectData_Path.setText("Collect Train Data cfg")

        #self.Lab_Display_X.setText("0")
        #self.Lab_Display_Y.setText("0")
        #self.Lab_Display_Rot.setText("0")
        #self.Change_Checkbox(False)

        #init motion 
        X_global = 0
        Y_global = 0
        
    def closeEvent(self,ApplicationExit): #Trigger when Exit the application
        print("Closing")
        global Logging_Buffer
        if(Activate_Logging):
            Logging_Buffer = "Closing Application"
            event.set()
            self.logging_thread.requestInterruption() #Stop Logging thread
            self.logging_thread.quit()
            self.logging_thread.wait()
            Motion_Request.set()
            self.MotionControl_thread.requestInterruption() #Stop Logging thread
            self.MotionControl_thread.quit()
            self.MotionControl_thread.wait()
    
    def Start_test(self):
        global Logging_Buffer
        current_dir = os.getcwd()
        print(X_global,Y_global)
        self.But_Start.setEnabled(False)
        self.But_Stop.setEnabled(True)
        self.But_Reset.setEnabled(False)
        #TODO Get Parameters
        Test_Handle = self.Get_Inputpara()
        #As display image must return to UI from Cam directly
        #UI must call the LibCamera directly instead of pass to Maincontrol first.
        global Mode #Create global variable for thread to access
        global CollectModeSetting
        Mode,CollectModeSetting = MC.Start_test(Test_Handle) #LC control and determine the workflow use in test
        if Mode == 3:
            imgsave_folder = os.path.join(current_dir,Test_Handle["SavePath"])
        if Mode == 2:
            imgsave_folder = os.path.join(current_dir,Test_Handle["Collectpath"])
        if Mode == 1:
            imgsave_folder = os.path.join(current_dir,"MeasureMode")
        if not os.path.exists(imgsave_folder):
            os.makedirs(imgsave_folder)  

        Logging_Buffer = "Start Test, Mode = %s"%Mode
        event.set()

        self.job = jobthread()
        self.job.start()
        self.job.jobthread_image_signal.connect(self.displayimg)
        self.job.update_measuremode_UItext_signal.connect(self.UpdateMeasureUIText)
        self.job.finished.connect(self.job_finished)
    

    def job_finished(self):
        print("Job Done")
        global Logging_Buffer
        Logging_Buffer = "Test Finished"
        MC.ResetLC()
        event.set()
        self.But_Start.setEnabled(True)
        self.But_Stop.setEnabled(False)
        self.But_Reset.setEnabled(True)


    def Stop_test(self):
        self.But_Start.setEnabled(True)
        self.But_Stop.setEnabled(False)
        self.But_Reset.setEnabled(True)
        #TODO Stop the current progress including LC
        #MC.ResetLC()
        self.job.stop()



    def Reset_all(self):
        global X_global
        global Y_global
        self.Init_input()
        #TODO Add hardware reset
        MC.ResetLC()

        #MC.GetMoveDistX(0,X_global) # Moving back to the orginal location
        #MC.GetMoveDistY(0,Y_global)


    def Change_Checkbox(self,status):
        self.Check_Camera.setChecked(status)
        self.Check_LC.setChecked(status)
        self.Check_Motion.setChecked(status)
        self.Check_Mode.setChecked(status)
        self.Check_CollectData.setChecked(status)
        self.Check_MeasureData.setChecked(status)
        #self.Check_Measure.setChecked(status)S


    def Change_CameraStatus(self,status):
        if(self.Check_Camera.isChecked() is True):
            status = 1 #check box is checked
        else:
            status = 0
        #Change the status of other element in the group
        self.Input_Cam_ExpoStart.setEnabled(status)
        self.Input_Cam_ExpoEnd.setEnabled(status)
        self.Input_Cam_ExpoStep.setEnabled(status)
        self.Input_Cam_Gain.setEnabled(status)
        self.Input_Cam_Num.setEnabled(status)
        self.Check_Cam_Save.setEnabled(status)
        self.Input_Cam_Save.setEnabled(status)


    def Change_LCStatus(self):
        if(self.Check_LC.isChecked() is True):
            status = 1 #check box is checked
        else:
            status = 0
        #Change the status of other element in the group
        self.Check_LCIO1.setEnabled(status)
        self.Check_LCIO2.setEnabled(status)
        self.Check_LCIO3.setEnabled(status)
        self.Check_LCIO4.setEnabled(status)


    def Change_MotionStatus(self):
        if(self.Check_Motion.isChecked() is True):
            status = 1 #check box is checked
        else:
            status = 0
        #Change the status of other element in the group
        self.Input_Motion_XStart.setEnabled(status)
        self.Input_Motion_XEnd.setEnabled(status)
        self.Input_Motion_XStep.setEnabled(status)
        self.Input_Motion_YStart.setEnabled(status)
        self.Input_Motion_YEnd.setEnabled(status)
        self.Input_Motion_YStep.setEnabled(status)
        self.Input_Motion_RotStart.setEnabled(status)
        self.Input_Motion_RotEnd.setEnabled(status)
        self.Input_Motion_RotStep.setEnabled(status)
    

    def Change_ModeStatus(self):
        if(self.Check_Mode.isChecked() is True):
            status = 1 #check box is checked
        else:
            status = 0
        #Change the status of other element in the group
        self.Check_CollectData.setEnabled(status)
        self.Check_MeasureData.setEnabled(status)

        #self.Check_Measure.setEnabled(status)


    def Change_CollectModeStatus(self):
        if(self.Check_CollectData.isChecked() is True):
            status = 1 #check box is checked
            #self.Check_Measure.setChecked(False)
        else:
            status = 0
        self.Input_CollectData_Path.setEnabled(status)
        

    def Change_MeasureModeStatus(self):
        if(self.Check_MeasureData.isChecked() is True):
            status = 1 #check box is checked
        else:
            status = 0
        self.But_Measure_Ground.setEnabled(status)
        self.But_Measure_Moved.setEnabled(status)
        self.But_Measure_Compensation.setEnabled(status)
        self.Lab_Measure_Ground_Center.setEnabled(status)
        self.Lab_Measure_Ground_LU.setEnabled(status)
        self.Lab_Measure_Ground_LL.setEnabled(status)    
        self.Lab_Measure_Ground_RU.setEnabled(status)
        self.Lab_Measure_Ground_RL.setEnabled(status)   
        self.Lab_Measure_Moved_Center.setEnabled(status)
        self.Lab_Measure_Moved_LU.setEnabled(status)
        self.Lab_Measure_Moved_LL.setEnabled(status)    
        self.Lab_Measure_Moved_RU.setEnabled(status)
        self.Lab_Measure_Moved_RL.setEnabled(status)   
        self.Lab_Measure_CompensatedCen.setEnabled(status)
        self.Lab_Measure_compensated_LU.setEnabled(status)
        self.Lab_Measure_compensated_LL.setEnabled(status)    
        self.Lab_Measure_compensated_RU.setEnabled(status)
        self.Lab_Measure_compensated_RL.setEnabled(status)   
         
    def Change_MeasureMode_Button_Status(self):
        if(self.But_Measure_Ground.isChecked()):
            self.But_Measure_Moved.setEnabled(0)
            self.But_Measure_Compensation.setEnabled(0)
        elif(self.But_Measure_Moved.isChecked()):
            self.But_Measure_Ground.setEnabled(0)
            self.But_Measure_Compensation.setEnabled(0)
        elif (self.But_Measure_Compensation.isChecked()):
            self.But_Measure_Moved.setEnabled(0)
            self.But_Measure_Ground.setEnabled(0)
        else:
            self.But_Measure_Moved.setEnabled(1)
            self.But_Measure_Ground.setEnabled(1)           
            self.But_Measure_Compensation.setEnabled(1)


    def Get_Inputpara(self):
        #TODO
        #Get user input 
        if(self.Check_Camera.isChecked() is True):
            job['Camera'] = True
            job['Expo_Start'] = float(self.Input_Cam_ExpoStart.text())
            job['Expo_End'] = float(self.Input_Cam_ExpoEnd.text())
            job['Expo_Step'] = float(self.Input_Cam_ExpoStep.text())
            job['Gain'] = float(self.Input_Cam_Gain.text())
            job['NumGrab'] = int(self.Input_Cam_Num.text())
            job['Save'] = self.Check_Cam_Save.isChecked()
            if(job['Save'] is True ):
                job['SavePath'] = self.Input_Cam_Save.text()
        else:
            job['Camera'] = False

        if(self.Check_LC.isChecked() is True):
            job["LC"] = True
            print(self.Check_LCIO1.isChecked())
            print(self.Check_LCIO2.isChecked())
            print(self.Check_LCIO3.isChecked())
            print(self.Check_LCIO4.isChecked())
            job["LCIO1"] = bool(self.Check_LCIO1.isChecked())
            print("LCIO1 " + str(job["LCIO1"]) )
            job["LCIO2"] = bool(self.Check_LCIO2.isChecked())
            print("LCIO2 " + str(job["LCIO2"] ))
            job["LCIO3"] = bool(self.Check_LCIO3.isChecked())
            print("LCIO3 " + str(job["LCIO3"]) )
            job["LCIO4"] = bool(self.Check_LCIO4.isChecked())
            print("LCIO4 " + str(job["LCIO4"] ))
        else:
            job["LC"] = False

        if(self.Check_Motion.isChecked() is True):
            job['Motion'] = True
            job['X_Start'] = round(float(self.Input_Motion_XStart.text()),2)
            job['X_End'] = round(float(self.Input_Motion_XEnd.text()),2)
            job['X_Step'] = round(float(self.Input_Motion_XStep.text()),2)
            job['Y_Start'] = round(float(self.Input_Motion_YStart.text()),2)
            job['Y_End'] = round(float(self.Input_Motion_YEnd.text()),2)
            job['Y_Step'] = round(float(self.Input_Motion_YStep.text()),2)
            job['Rot_Start'] = round(float(self.Input_Motion_RotStart.text()),2)
            job['Rot_End'] = round(float(self.Input_Motion_RotEnd.text()),2)
            job['Rot_Step'] = round(float(self.Input_Motion_RotStep.text()),2)
        else:
            job['Motion'] = False

        if(self.Check_Mode.isChecked() is True):
            job['Mode'] = self.Check_Mode.isChecked()
            job['CollectMode'] = self.Check_CollectData.isChecked()
            job['MeasureMode'] = self.Check_MeasureData.isChecked()
            if(job['CollectMode'] is True ):
                job['Collectpath'] = self.Input_CollectData_Path.text()
            if(job['MeasureMode'] is True):
                job['MeasureGround'] = self.But_Measure_Ground.isChecked()
                job['MeasureMoved'] = self.But_Measure_Moved.isChecked()
                job['MeasureGroundCompensated'] = self.But_Measure_Compensation.isChecked()
        else: 
            job['CollectMode'] = False
            job['MeasureMode'] = False
        print(job)
        return job
    
    #@pyqtSlot(QImage)
    def displayimg(self,image):
        height, width, channel = image.shape
        image_addLine = image.copy()
        image_addLine[640,:] = 255
        image_addLine[:,640] = 255  
        QTimage = QtGui.QImage(image_addLine, width,height,3*width, QtGui.QImage.Format_RGB888 )
        self.Img_Display.setPixmap(QtGui.QPixmap(QTimage).scaled(self.Img_Display.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

    #@pyqtSlot(MeasureModeStatus)
    def UpdateMeasureUIText(self, MeasureModeStatus):   
        print("Test UpdateText")
        if (MeasureModeStatus == 1):
            self.Lab_Measure_Ground_Center.setText(str(Array_Center[0][0])+","+str(Array_Center[0][1])) 
            self.Lab_Measure_Ground_LU.setText(str(Array_GroundCorners[0][0])+","+str(Array_GroundCorners[0][1])) 
            self.Lab_Measure_Ground_LL.setText(str(Array_GroundCorners[1][0])+","+str(Array_GroundCorners[1][1]))     
            self.Lab_Measure_Ground_RU.setText(str(Array_GroundCorners[2][0])+","+str(Array_GroundCorners[2][1])) 
            self.Lab_Measure_Ground_RL.setText(str(Array_GroundCorners[3][0])+","+str(Array_GroundCorners[3][1]))      
        elif (MeasureModeStatus == 2):
            self.Lab_Measure_Moved_Center.setText(str(Array_Center[1][0])+","+str(Array_Center[1][1])) 
            self.Lab_Measure_Moved_LU.setText(str(Array_MovedCorners[0][0])+","+str(Array_MovedCorners[0][1])) 
            self.Lab_Measure_Moved_LL.setText(str(Array_MovedCorners[1][0])+","+str(Array_MovedCorners[1][1]))     
            self.Lab_Measure_Moved_RU.setText(str(Array_MovedCorners[2][0])+","+str(Array_MovedCorners[2][1])) 
            self.Lab_Measure_Moved_RL.setText(str(Array_MovedCorners[3][0])+","+str(Array_MovedCorners[3][1]))  
        elif (MeasureModeStatus == 4):# 3 is used in the angle compensated img before XY
            self.Lab_Measure_CompensatedCen.setText(str(Array_Center[2][0])+","+str(Array_Center[2][1])) 
            self.Lab_Measure_compensated_LU.setText(str(Array_CompensatedCorners[0][0])+","+str(Array_CompensatedCorners[0][1])) 
            self.Lab_Measure_compensated_LL.setText(str(Array_CompensatedCorners[1][0])+","+str(Array_CompensatedCorners[1][1]))     
            self.Lab_Measure_compensated_RU.setText(str(Array_CompensatedCorners[2][0])+","+str(Array_CompensatedCorners[2][1])) 
            self.Lab_Measure_compensated_RL.setText(str(Array_CompensatedCorners[3][0])+","+str(Array_CompensatedCorners[3][1]))   
############################################################################################################################################################
class logging(QThread):
    global Log_Status
    def run(self):
        log = open("Logging.txt", "a")
        Log_Status = 1
        while(Log_Status):
            event.wait()
            time = t.time()
            log.write(str(time)+ " " +Logging_Buffer + "\n")
            event.clear()
            if self.isInterruptionRequested():
                break
        print("Finish Loop")
        log.close()


############################################################################################################################################################
class jobthread(QThread):
    jobthread_image_signal = pyqtSignal(np.ndarray)
    update_measuremode_UItext_signal = pyqtSignal(int)
    def run(self):
        match Mode:
            case 1:
                self.MeasureMode(job)
            case 2:
                self.CollectMode(job)
            case 3:
                self.NormalMode(job)
                
    def SaveImg(self,Test_handle,image, name):
        current_dir = os.getcwd() 
        Expo = Test_handle["Expo_Start"]
        img = Image.fromarray(image)
        if(Test_handle["Mode"] is True and Test_handle["CollectMode"] is True):
            ImgName = str(CollectModeSetting[2][0]) + "_" + name + ".jpg"
            ImgPath = os.path.join(current_dir,Test_handle["Collectpath"], ImgName)    
        else:
            ImgName = str(Expo) + "_" + str(Test_handle["NumGrab"]) + "_" + name + ".jpg"
            ImgPath = os.path.join(current_dir,Test_handle["SavePath"], ImgName)
        img.save(f"%s"%ImgPath)  

    def SaveMeasureModeImg(self,image,mode):
        current_dir = os.getcwd()
        img = Image.fromarray(image)
        if (mode == 1):
            ImgPath = os.path.join(current_dir,"MeasureMode","MeasureGround.jpg")
        elif (mode == 2):
            ImgPath = os.path.join(current_dir,"MeasureMode","MeasureMoved.jpg")
        elif (mode == 3):
            ImgPath = os.path.join(current_dir,"MeasureMode","MeasureCompensated_Angle.jpg")   
        elif (mode == 4):
            ImgPath = os.path.join(current_dir,"MeasureMode","MeasureCompensated.jpg")    

        img.save(f"%s"%ImgPath)
        return(ImgPath)

    def stop(self):
        self.isRunning = False
        global Logging_Buffer
        Logging_Buffer = "Stop Test"
        event.set()
        self.terminate()

    def MeasureMode(self, Test_handle):
        print("MeasureMode")
        global CLIENT
        global X_global
        global Y_global
        global Angle_global        
        global Array_GroundCorners 
        global Array_MovedCorners
        global Array_CompensatedCorners 
        global Array_MovedCorners_afterangle
        global Array_Center 
        global Motion_Buffer
        MeasureModeStatus = 0
        global Logging_Buffer
        if(Test_handle["MeasureGround"] is True):
            MeasureModeStatus = 1
            MC.ModifyCamConfig("ExposureTime",Test_handle["Expo_Start"])
            image = MC.GrabImg()
            imgpath = self.SaveMeasureModeImg(image,MeasureModeStatus)
            self.jobthread_image_signal.emit(image)
            result = CLIENT.infer(imgpath, model_id="pcbholedetectionv3/4")
            result_unsorted_corner = LibAlg.filiter_Result(result)
            centroid,Array_GroundCorners = LibAlg.sort_points_anticlockwise(result_unsorted_corner)
            print(Array_GroundCorners)
            Array_Center[0][0] =centroid[0]
            Array_Center[0][1] = centroid[1]
        
        elif (Test_handle["MeasureMoved"] is True):
            MeasureModeStatus = 2
            if (Test_handle['X_Start'] != 0.0 or Test_handle['Y_Start'] != 0.0 or Test_handle['Rot_Start'] != 0.0):
                Motion_Buffer = "x" + str(Test_handle['X_Start'] - X_global)
                Motion_Request.set()
                Motion_Done_Signal.wait()
                Motion_Done_Signal.clear()
                X_global = Test_handle['X_Start']
                Logging_Buffer = "Moving X to  = %s"%X_global
                event.set()
                
                Motion_Buffer = "y" + str(Test_handle['Y_Start'] - Y_global)
                Motion_Request.set()
                Motion_Done_Signal.wait()
                Motion_Done_Signal.clear()
                Y_global = Test_handle['Y_Start']
                Logging_Buffer = "Moving Y to  = %s"%Y_global
                event.set()
                
                Motion_Buffer = "a" + str(Test_handle["Rot_Start"])
                Angle_global = Test_handle["Rot_Start"]
                Logging_Buffer = "Moving Y to  = %s"%Angle_global
                event.set()
                Motion_Request.set()
                Motion_Done_Signal.wait()
                Motion_Done_Signal.clear()
            MC.ModifyCamConfig("ExposureTime",Test_handle["Expo_Start"])
            image = MC.GrabImg()
            imgpath = self.SaveMeasureModeImg(image,MeasureModeStatus)
            self.jobthread_image_signal.emit(image)
            
            result = CLIENT.infer(imgpath, model_id="pcbholedetectionv3/4")
            
            result_unsorted_corner = LibAlg.filiter_Result(result)
            centroid,Array_MovedCorners = LibAlg.sort_points_anticlockwise(result_unsorted_corner)
            print(Array_MovedCorners)
            Array_Center[1][0] =centroid[0]
            Array_Center[1][1] = centroid[1]

        else: #MeasureGroundCompensated is Ture
            MeasureModeStatus = 3
            Translation,Angle_move  = LibAlg.robust_transform(Array_GroundCorners,Array_MovedCorners)
            print("Angle compensated")
            print (Translation,Angle_move)
            Angle_new = Angle_global - Angle_move #TODO determine the + or - the relative angle
            Motion_Buffer = "a" + str(Angle_new)
            Angle_global = Angle_new
            Motion_Request.set()
            Motion_Done_Signal.wait()
            Motion_Done_Signal.clear()
            Logging_Buffer = "Moving A to  = %s"%Angle_global
            event.set()

            #######################################
            #Add in 20250402, grab and pass to alg again after adjust angle to perform XY shift
            
            MC.ModifyCamConfig("ExposureTime",Test_handle["Expo_Start"])
            image = MC.GrabImg()
            imgpath = self.SaveMeasureModeImg(image,MeasureModeStatus)
            self.jobthread_image_signal.emit(image)
            
            result = CLIENT.infer(imgpath, model_id="pcbholedetectionv3/4")
            
            result_unsorted_corner = LibAlg.filiter_Result(result)
            centroid,Array_MovedCorners_afterangle = LibAlg.sort_points_anticlockwise(result_unsorted_corner)
            Array_Center[3][0] =centroid[0]
            Array_Center[3][1] = centroid[1]

            Translation,Angle_move  = LibAlg.robust_transform(Array_GroundCorners,Array_MovedCorners_afterangle)
            print("XY compensated")
            print (Translation,Angle_move)

            #######################################
            MeasureModeStatus = 4
            Motion_Buffer = "x" + str(Translation[0])
            Motion_Request.set()
            Motion_Done_Signal.wait()
            Motion_Done_Signal.clear()
            X_global = X_global + Translation[0]
            Logging_Buffer = "Moving X to  = %s"%X_global
            event.set()

            Motion_Buffer = "y" + str(-1*Translation[1])
            Motion_Request.set()
            Motion_Done_Signal.wait()
            Motion_Done_Signal.clear()
            Y_global = Y_global - Translation[1]
            Logging_Buffer = "Moving Y to  = %s"%Y_global
            event.set()

            MC.ModifyCamConfig("ExposureTime",Test_handle["Expo_Start"])
            image = MC.GrabImg()
            imgpath = self.SaveMeasureModeImg(image,MeasureModeStatus)
            self.jobthread_image_signal.emit(image)
            result = CLIENT.infer(imgpath, model_id="pcbholedetectionv3/4")

            result_unsorted_corner = LibAlg.filiter_Result(result)
            centroid,Array_CompensatedCorners = LibAlg.sort_points_anticlockwise(result_unsorted_corner)
            print(Array_CompensatedCorners)
            Array_Center[2][0] = centroid[0]
            Array_Center[2][1] = centroid[1]
        
        self.update_measuremode_UItext_signal.emit(MeasureModeStatus)

    def CollectMode(self, Test_handle):
        print("CollectMode")
        global X_global 
        global Y_global 
        global Angle_global
        global Logging_Buffer
        global Motion_Buffer
        current_dir = os.getcwd() 
        Motion_Buffer = "e1"
        Motion_Request.set()
        Motion_Done_Signal.wait()
        Motion_Done_Signal.clear()
        MC.ModifyCamConfig("AnalogueGain", float(CollectModeSetting[2][1]))
        MC.ModifyCamConfig("ExposureTime",float(CollectModeSetting[2][0]))
        n = 1
        for position in CollectModeSetting[6:]:
            #X_global = MC.GetMoveDistX(float(position[0]),X_global)
            #Y_global = MC.GetMoveDistY(float(position[1]),Y_global)
            #MC.GetMoveAngle(float(position[2]))
            
            #New Control Method: Move X
            print("Current Collecting " + str(n)) # print for check collect pogress
            n = n+1

            Motion_Buffer = "x" + str(round(float(position[0]) - X_global,1))
            Motion_Request.set()
            Motion_Done_Signal.wait()
            Motion_Done_Signal.clear()
            X_global = float(position[0])
            Logging_Buffer = "Moving X to  = %s"%X_global
            event.set()
            #New Control Method: Move Y
            Motion_Buffer = "y" + str(round(float(position[1]) - Y_global,1))
            Motion_Request.set()
            Motion_Done_Signal.wait()
            Motion_Done_Signal.clear()
            Y_global = float(position[1])
            Logging_Buffer = "Moving Y to  = %s"%Y_global
            event.set()
            #New Control Method: Move Angle
            Angle_global = round(float(position[2]),1)
            Motion_Buffer = "a" + str(round(float(position[2]),1))
            Motion_Request.set()
            Motion_Done_Signal.wait()
            Motion_Done_Signal.clear()
            Logging_Buffer = "Moving Angle to  = %s"%position[2]
            event.set()

            image = MC.GrabImg()
            self.jobthread_image_signal.emit(image)
            self.SaveImg(Test_handle,image, (str(position[0]) + "_" + str(position[1]) + "_" + str(position[2])))

    def NormalMode(self, Test_handle):
        global X_global 
        global Y_global 
        global Angle_global
        global Logging_Buffer
        global Motion_Buffer
        current_dir = os.getcwd()
        #print("NormalMode")
        MC.ModifyCamConfig("AnalogueGain", Test_handle["Gain"])
        #double for loop grab img with motion
        
        if((Test_handle["Motion"] is False) & (Test_handle["Camera"] is True)):
                Expo = Test_handle["Expo_Start"]
                Motion_Buffer = "e0"
                Motion_Request.set()
                Motion_Done_Signal.wait()
                Motion_Done_Signal.clear()
                while Expo <= Test_handle["Expo_End"]:
                    for Num in range(0, Test_handle["NumGrab"],1):
                        print(Num)
                        MC.ModifyCamConfig("ExposureTime",Expo)
                        Logging_Buffer = "Grab Image, Expo = %s"%Expo
                        event.set()
                        image = MC.GrabImg()

                        self.jobthread_image_signal.emit(image)
                        if(Test_handle["Save"] is True):
                            self.SaveImg(Test_handle,image,str(0))
                    Expo = Expo + Test_handle["Expo_Step"]
        
        elif ((Test_handle["Motion"] is True)  & (Test_handle["Camera"] is True)):
            if(Test_handle["X_Step"] == 0):
                Test_handle["X_Step"] = 1
            if(Test_handle["Y_Step"] == 0):
                Test_handle["Y_Step"] = 1
            if(Test_handle["Rot_Step"] == 0):
                Test_handle["Rot_Step"] = 1
            #TODO May need modify if add encoder for detect motor movement 
            Motion_Buffer = "e1"
            Motion_Request.set()
            Motion_Done_Signal.wait()
            Motion_Done_Signal.clear()
            X_Loc = Test_handle["X_Start"]
            #for X_Loc in range(Test_handle["X_Start"],Test_handle["X_End"]+1,Test_handle["X_Step"]):
            while X_Loc <= Test_handle["X_End"]:
                print("X_Loc   "+ str(X_Loc))
                #X_global = MC.GetMoveDistX(X_Loc,X_global)
                #New Control Method: Move X
                Motion_Buffer = "x" + str(round(X_Loc - X_global,2))
                Motion_Request.set()
                Motion_Done_Signal.wait()
                Motion_Done_Signal.clear()
                X_global = X_Loc
                Logging_Buffer = "Moving X to  = %s"%X_global
                event.set()
                Y_Loc = Test_handle["Y_Start"]
                #for Y_Loc in range(Test_handle["Y_Start"],Test_handle["Y_End"]+1,Test_handle["Y_Step"]): 
                while Y_Loc <= Test_handle["Y_End"]:
                    #Y_global = MC.GetMoveDistY(Y_Loc,Y_global)
                    Motion_Buffer = "y" + str(round(Y_Loc - Y_global,2))
                    Motion_Request.set()
                    Motion_Done_Signal.wait()
                    Motion_Done_Signal.clear()

                    Y_global = Y_Loc
                    
                    Logging_Buffer = "Moving Y to  = %s"%Y_global
                    event.set()
                    
                    Angle = Test_handle["Rot_Start"]
                    while Angle <= Test_handle["Rot_End"]:
                    #for Angle in range(Test_handle["Rot_Start"],Test_handle["Rot_End"]+1,Test_handle["Rot_Step"]): 
                        Angle_global = Angle
                        Motion_Buffer = "a" + str(round(Angle,2))
                        Motion_Request.set()
                        Motion_Done_Signal.wait()
                        Motion_Done_Signal.clear()
                    
                        Logging_Buffer = "Moving Angle to  = %s"%Angle
                        event.set()

                        Expo = Test_handle["Expo_Start"]
                        while Expo <= Test_handle["Expo_End"]:
                            MC.ModifyCamConfig("ExposureTime",Expo)
                            for Num in range(0, Test_handle["NumGrab"],1):    
                                Logging_Buffer = "Grab Image, Expo = %s"%Expo
                                event.set()
                                image = MC.GrabImg()
                                self.jobthread_image_signal.emit(image)
                                if(Test_handle["Save"] is True):
                                    self.SaveImg(Test_handle,image, (str(X_Loc)+"_"+str(Y_Loc)+"_"+str(Angle)))
                                Expo = Expo + Test_handle["Expo_Step"]
                        Angle += Test_handle["Rot_Step"]
                    Y_Loc += Test_handle["Y_Step"] 
                X_Loc += Test_handle["X_Step"]
        elif ((Test_handle["Motion"] is True) & (Test_handle["Camera"] is False)):
            if(Test_handle["X_Step"] == 0):
                Test_handle["X_Step"] = 1
            if(Test_handle["Y_Step"] == 0):
                Test_handle["Y_Step"] = 1
            if(Test_handle["Rot_Step"] == 0):
                Test_handle["Rot_Step"] = 1
            Motion_Buffer = "e1"
            Motion_Request.set()
            Motion_Done_Signal.wait()
            Motion_Done_Signal.clear()
            #TODO May need modify if add encoder for detect motor movement 
            
            X_Loc = Test_handle["X_Start"]
            while X_Loc <= Test_handle["X_End"]:
            #for X_Loc in range(Test_handle["X_Start"],Test_handle["X_End"]+1,Test_handle["X_Step"]):
                #X_global = MC.GetMoveDistX(X_Loc,X_global)
                Motion_Buffer = "x" + str(round(X_Loc - X_global,2))
                Motion_Request.set()
                Motion_Done_Signal.wait()
                Motion_Done_Signal.clear()
                X_global = X_Loc
                Logging_Buffer = "Moving X to  = %s"%X_global
                event.set()
            
                Y_Loc = Test_handle["Y_Start"]
                while Y_Loc <= Test_handle["Y_End"]:
                #for Y_Loc in range(Test_handle["Y_Start"],Test_handle["Y_End"]+1,Test_handle["Y_Step"]): 
                    #Y_global = MC.GetMoveDistY(Y_Loc,Y_global)
                    Motion_Buffer = "y" + str(round(Y_Loc - Y_global,2))
                    Motion_Request.set()
                    Motion_Done_Signal.wait()
                    Motion_Done_Signal.clear()
                    Y_global = Y_Loc
                    Motion_Request.set()

                    Logging_Buffer = "Moving Y to  = %s"%Y_global
                    event.set()
                    Angle = Test_handle["Rot_Start"]
                    while Angle <= Test_handle["Rot_End"]:
                    #for Angle in range(Test_handle["Rot_Start"],Test_handle["Rot_End"]+1,Test_handle["Rot_Step"]): 
                        Angle_global = Angle
                        Logging_Buffer = "Moving Angle to  = %s"%Angle
                        event.set()
                        #MC.GetMoveAngle(Angle)   
                        Motion_Buffer = "a" + str(round(Angle,2))
                        Motion_Request.set()
                        Motion_Done_Signal.wait()
                        Motion_Done_Signal.clear()
                        Angle += Test_handle["Rot_Step"]
                    Y_Loc += Test_handle["Y_Step"] 
                X_Loc += Test_handle["X_Step"]
        else:
            t.sleep(2) #prevent Qthread process faster than MainThread cause the loss of Qthread finish signal



############################################################################################################################################################
class MotionControlThread(QThread):
    def run(self):
        global Motion_Buffer    
        print("Motion activate")
        ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
        print("HI")
        t.sleep(0.5)
        ser.reset_input_buffer()
        print("BYE "+str(ser.in_waiting))
        MotionControlThread_request = 0
        while(True):
            line = ser.readline().decode('utf-8').rstrip()
            
            print(line)
            
            if(line == "Please input motor command:"):
                while(True):
                    Motion_Request.wait()
                    Motion_Request.clear()
                    if self.isInterruptionRequested():
                        MotionControlThread_request =1
                        break
                    ser.write(bytes(Motion_Buffer, 'utf-8'))
                    while(True):
                        line = ser.readline().decode('utf-8').rstrip()
                        print(line)
                        if(line == "Done"):
                            Motion_Done_Signal.set()
                            break
            if(MotionControlThread_request == 1 ):
                break



############################################################################################################################################################
if __name__ == '__main__':
    MC.InitLCIO()
    MC.InitCam()
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()
    MC.CleanUpLC()



