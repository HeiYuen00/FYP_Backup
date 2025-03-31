import picamera2 as Cam
import time as t

def InitCam():
    global picam2 
    picam2 = Cam.Picamera2()
    config = picam2.create_still_configuration(main={'size' : (1280,1280)})
    print(config["main"])
    picam2.configure(config)
    picam2.start()
    picam2.switch_mode(config)

def ReleaseCam():
    picam2.close()

def ModifyCamConfig(item,value):
    #picam2.close()
    picam2.set_controls({item:value})
    #picam2.set_controls({"ExposureTime":value})
    #picam2.start()

def GrabImage():
    #config = picam2.create_still_configuration({'format': 'RGB888'})

    print(t.time())
    img1 = picam2.capture_array()
    print(img1.shape)
    print(t.time())
    ####test
    #request = picam2.capture_request()
    #request.save("main", "test.jpg")
    #metadata = request.get_metadata()
    #request.release()
    #print(f"ExposureTime: {metadata['ExposureTime']}  AnalogueGain: {metadata['AnalogueGain']} DigitalGain: {metadata['DigitalGain']}")
    return img1