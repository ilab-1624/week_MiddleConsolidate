import S3
import uuid
from datetime import datetime
import time


class Alert:
    def __init__(self, dataModel):
        self.__s3 = S3.S3()
        self.__dataModel = dataModel

    def backgroundObjectRegister(self):
        backgroundObjectList = []

        for detectedObject in self.__dataModel["objectDetection"]["detectionResult"]["objectList"]:
            count = 0
            if detectedObject["name"] != "Person":
                detectedObject.update({
                    "id":str(uuid.uuid4()),
                    "eventTime":str(datetime.utcfromtimestamp(int(self.__dataModel["frame"]["captureResult"]['timestamp']) + 28800).strftime('%Y-%m-%d %H:%M:%S')),
                    "stayTime":0,
                    "longLost":True,
                    "misjudgmentTime":0
                })
                
                for shortLostObject in self.__dataModel["config"]["shortLostObjectList"]:
                    if shortLostObject == detectedObject["name"]:
                        detectedObject["longLost"] = False
                backgroundObjectList.append(detectedObject)   
                
        response = self.__s3.storeJson("backgroundObjectList.json", backgroundObjectList)
        print(response)
        
        backgroundEvent = {
            "sourceImageUrl":self.__dataModel["objectDetection"]["s3"]["sourceImageUrl"],
            "eventTime":str(datetime.utcfromtimestamp(int(self.__dataModel["frame"]["captureResult"]['timestamp']) + 28800).strftime('%Y-%m-%d %H:%M:%S'))
        }
        
        response = self.__s3.storeJson("backgroundEvent.json", backgroundEvent)
        print(response)
        
        lastNotificationTimestamp={
            "cameraCovered":0,
            "cameraMoved":0,
            "longObjectStay":0,
            "shortObjectStay":0
        }
        
        response = self.__s3.storeJson("lastNotificationTimestamp.json", lastNotificationTimestamp)
        print(response)
        
        alertNotifyModel={
            "code":0,
            "event":"背景註冊",
            "sourceImageUrl":self.__dataModel["objectDetection"]["s3"]["sourceImageUrl"],
            "objectCount":len(backgroundObjectList),
            "eventTime":str(datetime.utcfromtimestamp(int(self.__dataModel["frame"]["captureResult"]['timestamp']) + 28800).strftime('%Y-%m-%d %H:%M:%S')),
            "objectList":backgroundObjectList
        }
        
        return alertNotifyModel

    def cameraCoveredDetect(self,lastNotificationTimestamp, backgroundEvent):
        if self.__dataModel["objectDetection"]["detectionResult"]["objectCount"]==0 and time.time() - lastNotificationTimestamp["cameraCovered"] >= self.__dataModel["config"]["cameraCoveredThreshold"]:
            alertNotifyModel={
                "code":1,
                "event":"鏡頭遮蔽",
                "normalSceneImageUrl":backgroundEvent["sourceImageUrl"],
                "normalSceneTime":backgroundEvent["eventTime"],
                "sourceImageUrl":self.__dataModel["objectDetection"]["s3"]["sourceImageUrl"],
                "eventTime":str(datetime.utcfromtimestamp(int(self.__dataModel["frame"]["captureResult"]['timestamp']) + 28800).strftime('%Y-%m-%d %H:%M:%S'))
            }

            lastNotificationTimestamp["cameraCovered"] = time.time()
            response = self.__s3.storeJson("lastNotificationTimestamp.json", lastNotificationTimestamp)

            return alertNotifyModel

    def cameraMovedDetect(self,lastNotificationTimestamp, backgroundEvent, backgroundObjectList):
        offsetObjectCount = 0
        for detectedObject in self.__dataModel["objectDetection"]["detectionResult"]["objectList"]:
            for backgroundObject in backgroundObjectList:
                if detectedObject["name"] == backgroundObject["name"]:
                    x1 = detectedObject["coordination"]["X"]
                    y1 = detectedObject["coordination"]["Y"]
                    x2 = backgroundObject["coordination"]["X"]
                    y2 = backgroundObject["coordination"]["Y"]
                    if ((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2))**0.5 >= self.__dataModel["config"]["seceneOffsetThreshold"]:
                        offsetObjectCount +=1
                        
        if offsetObjectCount <= self.__dataModel["objectDetection"]["detectionResult"]["objectCount"] and offsetObjectCount >= self.__dataModel["objectDetection"]["detectionResult"]["objectCount"]-1 and offsetObjectCount !=0:
            if time.time() - lastNotificationTimestamp["cameraMoved"] >= self.__dataModel["config"]["cameraMovedThreshold"]:
                alertNotifyModel={
                    "code":2,
                    "event":"鏡頭偏移",
                    "normalSceneImageUrl":backgroundEvent["sourceImageUrl"],
                    "normalSceneTime":backgroundEvent["eventTime"],
                    "sourceImageUrl":self.__dataModel["objectDetection"]["s3"]["sourceImageUrl"],
                    "eventTime":str(datetime.utcfromtimestamp(int(self.__dataModel["frame"]["captureResult"]['timestamp']) + 28800).strftime('%Y-%m-%d %H:%M:%S'))
                }
                
                lastNotificationTimestamp["cameraMoved"] = time.time()
                response = self.__s3.storeJson("lastNotificationTimestamp.json", lastNotificationTimestamp)

                return alertNotifyModel

    def backgroundObjectLostDetect(self,backgroundObjectList, backgroundEvent):
        lostObjectList=[]
        
        for backgroundObject in backgroundObjectList:
            count = 0
            index = backgroundObjectList.index(backgroundObject)
            for detectedObject in self.__dataModel["objectDetection"]["detectionResult"]["objectList"]:
                if detectedObject["name"] != backgroundObject["name"] :
                    count += 1
                    
            if count == self.__dataModel["objectDetection"]["detectionResult"]["objectCount"]:
                if self.__dataModel["objectDetection"]["detectionResult"]["objectCount"]!=0 :
                    backgroundObjectList[index]["stayTime"] -=1
                    threshold = 0
                    if backgroundObject["longLost"]:
                        threshold = self.__dataModel["config"]["objectLongLostThreshold"]
                    else:
                        threshold = self.__dataModel["config"]["objectShortLostThreshold"]
                    if backgroundObject["stayTime"] == -(threshold - 1):
                        backgroundObjectList[index]["stayTime"] = 0 
                        lostObjectList.append(backgroundObject)
            else:
                backgroundObject["misjudgmentTime"]+=1
                if backgroundObject["misjudgmentTime"]==3:
                    backgroundObject["stayTime"] = 0
                    backgroundObject["misjudgmentTime"] = 0

        response = self.__s3.storeJson("backgroundObjectList.json", backgroundObjectList)

        if len(lostObjectList)!=0:
            alertNotifyModel={
                "code":3,
                "event":"設備遺失",
                "normalSceneImageUrl":backgroundEvent["sourceImageUrl"],
                "normalSceneTime":backgroundEvent["eventTime"],
                "sourceImageUrl":self.__dataModel["objectDetection"]["s3"]["sourceImageUrl"],
                "eventTime":str(datetime.utcfromtimestamp(int(self.__dataModel["frame"]["captureResult"]['timestamp']) + 28800).strftime('%Y-%m-%d %H:%M:%S')),
                "objectList":lostObjectList
            }
            
            return alertNotifyModel

    def abnormalObjectStayDetect(self,backgroundObjectList, backgroundEvent):
        newObjectList=[] 
        for detectedObject in self.__dataModel["objectDetection"]["detectionResult"]["objectList"]:
            count = 0
            for backgroundObject in backgroundObjectList:
                if backgroundObject["name"] != detectedObject["name"] and detectedObject["name"] != "Person":
                    count +=1
            if count == len(backgroundObjectList) and len(backgroundObjectList)!=0:
                detectedObject.update({
                    "stayTime":0,
                    "misjudgmentTime":0
                })            
                newObjectList.append(detectedObject)
                    
        stayObjectList = self.__s3.readJson("stayObjectList.json")
            
        if len(stayObjectList) == 0:
            self.__s3.storeJson("stayObjectList.json", newObjectList)
        else:
            newStayObjectList = []
            for stayObject in stayObjectList:
                exist = False
                for newObject in newObjectList:
                    if stayObject["name"] == newObject["name"] and newObject["name"] != "Person":
                        exist = True
                        newObjectList.remove(newObject)

                if exist:
                    stayObject["stayTime"]+=1
                    newStayObjectList.append(stayObject)
                    for newObject in newObjectList:
                        if newObject["name"] == stayObject["name"]:
                            newObjectList.remove(newObject)
                else:
                    if stayObject["misjudgmentTime"] <2:
                        stayObject["misjudgmentTime"] +=1
                        newStayObjectList.append(stayObject)

            for newObject in newObjectList:
                newStayObjectList.append(newObject)

                        
            longStayObjectList = []
            shortStayObjectList = []
            notificationObjectList = []
            threshold=0
            for newStayObject in newStayObjectList:
                longStay = True
                for shortStayObject in self.__dataModel["config"]["shortStayObjectList"]:
                    if shortStayObject == newStayObject["name"]:
                        longStay = False
                
                newStayObject.update({
                    "longStay":longStay
                })
                
                if longStay:
                    threshold = self.__dataModel["config"]["objectLongStayThreshold"]
                else:
                    threshold = self.__dataModel["config"]["objectShortStayThreshold"]

                if newStayObject["stayTime"]>= threshold:
                    newStayObjectList[newStayObjectList.index(newStayObject)]["stayTime"] = 0
                    notificationObjectList.append(newStayObject)

            self.__s3.storeJson("stayObjectList.json", newStayObjectList)

            if len(notificationObjectList) !=0:
                alertNotifyModel={
                    "code":4,
                    "event":"物件置留",
                    "normalSceneImageUrl":backgroundEvent["sourceImageUrl"],
                    "normalSceneTime":backgroundEvent["eventTime"],
                    "sourceImageUrl":self.__dataModel["objectDetection"]["s3"]["sourceImageUrl"],
                    "eventTime":str(datetime.utcfromtimestamp(int(self.__dataModel["frame"]["captureResult"]['timestamp']) + 28800).strftime('%Y-%m-%d %H:%M:%S')),
                    "objectList":notificationObjectList
                }

                return alertNotifyModel

                

        