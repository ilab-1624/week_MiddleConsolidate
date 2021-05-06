import copy
import base64  
import cv2
import time
from datetime import datetime

class Capture():
    def __init__(self):

        self.frame = {
            "image":None,
            "timestamp":None,
            "id":None
        }   

    def Frame(self,image):

        if image is not None:

            Height , Width = image.shape[:2]

            scale = None

            if Height/640 > Width/960:
                scale = Height/640
            else:
                scale = Width/960

            image = cv2.resize(image.copy(), (int(Width/scale), int(Height/scale)), interpolation=cv2.INTER_CUBIC)
            eventTimestamp = datetime.fromtimestamp(int(time.time()))
            nowString = eventTimestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
            self.frame["image"] = base64.b64encode(cv2.imencode('.jpg', image)[1]).decode() 
            self.frame["id"] = "image_" + nowString 
            print(self.frame["id"])
            self.frame["timestamp"] = time.time()

            return self.frame
