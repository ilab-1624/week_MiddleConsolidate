import cv2
import time
import copy
import threading
import boto3
import json
import base64  
import awsconfig
import config
from API.captureAPI import Capture
#from API.recogntion import Recognition

frame = None

client = boto3.client('stepfunctions', aws_access_key_id=awsconfig.access_key, aws_secret_access_key=awsconfig.secret_access_key,region_name= awsconfig.region_name)
client2 = boto3.client('s3', aws_access_key_id=awsconfig.access_key, aws_secret_access_key=awsconfig.secret_access_key,region_name= awsconfig.region_name)

def stream():

    global frame

    streamPort = 'rtsp://secom:123456@192.168.1.109/ch00/0/live.3gp'
    #streamPort = 'rtsp://192.168.1.228/'
    videoSource = cv2.VideoCapture(streamPort)
    videoSource.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    videoSource.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('ilab_entry02.avi', fourcc, 15.0, (1280, 720))


    while True:
        try:
            if videoSource.isOpened():
                ret, frame = videoSource.read()
                out.write(frame)
                Height , Width = frame.shape[:2]
                scale = None
                if Height/640 > Width/960:
                    scale = Height/640
                else:
                    scale = Width/960
                #frame = cv2.resize(frame, (int(Width/scale), int(Height/scale)), interpolation=cv2.INTER_CUBIC)
                image = cv2.line(frame.copy(), (640, 0), (640, 720), (0, 0, 255), 5)
                #out.write(frame)
                cv2.imshow("CSI",image)
                cv2.waitKey(1)
                if ret == False:
                    videoSource = cv2.VideoCapture(streamPort)
        except:
            print('Source video is unavailable! reconnecting ....')
    out.release()
    videoSource.release()


streamingThread = threading.Thread(target = stream,daemon=True)
streamingThread.start()

def main():

    global frame

    personCount = None
    model = None 

    while True:

        time.sleep(config.stepFunctionActivateFreqency)

        if frame is not None:

            begin = time.time()

            print("Streaming........")
            

            #if Recognition().YoloV4(frame) > 0:

            model  = Capture().Frame(frame)


            #if time.time() - begin > config.stepFunctionActivateFreqency
            image_binary = base64.b64decode(model["image"])
            #client2.put_object(ACL='public-read',Body=image_binary, Bucket=config.config["s3Bucket"], Key = model["id"] ,ContentEncoding='base64',ContentType='image/jpeg')
            #url = 'https://' + config.config["s3Bucket"] + '.s3-' + 'us-west-2' + '.amazonaws.com/' + model["id"]
            #print(url)
            model["config"] = config.config
            #print(model)

            response = client.start_execution(
               stateMachineArn = awsconfig.stepfunction_ARN,
               input = json.dumps(model)
            )


if __name__ == '__main__':

    main()
 