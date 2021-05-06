import json
import boto3
import math
import config
# import copy

class NotMemberDataTransform:
    def __init__(self, dataModel, aws_access_key_id, aws_secret_access_key):
        self.__dataModel = dataModel
        self.__s3client = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        self.__outputModel = []
    
    def processData(self):
        if self.__dataModel["site"]!="IN":
            return 
        
        currentNotMemberCount = 0
        currentNotMemberList = []
        for person in self.__dataModel["ppeDetectResponse"]["Persons"]:
            for bodypart in person["BodyParts"]:
                if (bodypart["Name"] == "HEAD") and (len(bodypart["EquipmentDetections"]) != 0):
                    currentNotMemberCount = currentNotMemberCount + 1
                    currentNotMemberList.append({
                        "X":bodypart["EquipmentDetections"][0]["BoundingBox"]["Left"]+0.5*bodypart["EquipmentDetections"][0]["BoundingBox"]["Width"],
                        "Y":bodypart["EquipmentDetections"][0]["BoundingBox"]["Top"]+0.5*bodypart["EquipmentDetections"][0]["BoundingBox"]["Height"],
                        "matched": False
                    })
                    break
                
        preNotMemberList = self.__s3Read()
        preNotMemberCount = len(preNotMemberList)
        
        for notMember in preNotMemberList:
            notMember["matched"] = False
            notMember["crossLine"] = 0
            
        #################
        print("acurrentNotMemberList",currentNotMemberList)
        print("apreNotMemberList",preNotMemberList)
        
        
        if preNotMemberCount >= currentNotMemberCount :
            for currentNotMember in currentNotMemberList:
                nearestPreNotMemberIndex = -1
                nearestPreNotMemberDistance = 100
                for index in range(preNotMemberCount):
                    if preNotMemberList[index]["matched"] == False:
                        distanceX = preNotMemberList[index]["coordinate"]["X"]-currentNotMember["X"]
                        distanceY = preNotMemberList[index]["coordinate"]["Y"]-currentNotMember["Y"]
                        distance = math.sqrt(distanceX ** 2 + distanceY ** 2)
                        if distance < nearestPreNotMemberDistance:
                            nearestPreNotMemberDistance = distance
                            nearestPreNotMemberIndex = index
                            
                if currentNotMember["X"] <0.5 and preNotMemberList[nearestPreNotMemberIndex]["coordinate"]["X"]>=0.5:
                    preNotMemberList[nearestPreNotMemberIndex]["crossLine"] = 1
                elif currentNotMember["X"] >0.5 and preNotMemberList[nearestPreNotMemberIndex]["coordinate"]["X"]<=0.5:
                    preNotMemberList[nearestPreNotMemberIndex]["crossLine"] = 2
                preNotMemberList[nearestPreNotMemberIndex]["coordinate"]["X"] = currentNotMember["X"]
                preNotMemberList[nearestPreNotMemberIndex]["coordinate"]["Y"] = currentNotMember["Y"]
                preNotMemberList[nearestPreNotMemberIndex]["matched"] = True
                preNotMemberList[nearestPreNotMemberIndex]["missingTime"] = 0
                print("preNotMemberList",preNotMemberList)   
                
        elif currentNotMemberCount > preNotMemberCount :
            for preNotMember in preNotMemberList:
                nearestCurrentNotMemberIndex = -1
                nearestCurrentNotMemberDistance = 100
                print("bcurrentNotMemberList",currentNotMemberList)
                print("bpreNotMemberList",preNotMemberList)  
                for index in range(currentNotMemberCount):
                    if currentNotMemberList[index]["matched"] == False:
                        distanceX = currentNotMemberList[index]["X"]-preNotMember["coordinate"]["X"]
                        distanceY = currentNotMemberList[index]["Y"]-preNotMember["coordinate"]["Y"]
                        distance = math.sqrt(distanceX ** 2 + distanceY ** 2)
                        if distance<nearestCurrentNotMemberDistance:
                            nearestCurrentNotMemberDistance = distance
                            nearestCurrentNotMemberIndex = index
                        
                print("ccurrentNotMemberList",currentNotMemberList)
                print("cpreNotMemberList",preNotMemberList)     
                if currentNotMemberList[nearestCurrentNotMemberIndex]["X"] <0.5 and preNotMember["coordinate"]["X"]>=0.5:
                    preNotMember["crossLine"] = 1
                elif currentNotMemberList[nearestCurrentNotMemberIndex]["X"] >0.5 and preNotMember["coordinate"]["X"]<=0.5:
                    preNotMember["crossLine"] = 2
                preNotMember["coordinate"]["X"] = currentNotMemberList[nearestCurrentNotMemberIndex]["X"]
                preNotMember["coordinate"]["Y"] = currentNotMemberList[nearestCurrentNotMemberIndex]["Y"]
                preNotMember["matched"] = True
                preNotMember["missingTime"] = 0
                currentNotMemberList[nearestCurrentNotMemberIndex]["matched"] = True
            print("dcurrentNotMemberList",currentNotMemberList)
            print("dpreNotMemberList",preNotMemberList) 
            notMemberId = 1
            for currentNotMember in currentNotMemberList:
                if currentNotMember["matched"] == False:
                    preNotMemberList.append({
                        "notMemberId": "notMember_"+str(self.__dataModel["eventTimestamp"])+"_"+str(notMemberId),
                        "entryTime": self.__dataModel["eventTimestamp"],
                        "missingTime": 0,
                        "coordinate":{
                            "X":currentNotMember["X"],
                            "Y":currentNotMember["Y"]
                        },
                        "matched": True,
                        "crossLine":0
                    })
                    preNotMemberCount = preNotMemberCount +1
                notMemberId = notMemberId+1
            
        storeNotMemberList = []
        for index in range(preNotMemberCount):
            if preNotMemberList[index]["matched"] == False:
                preNotMemberList[index]["missingTime"] = preNotMemberList[index]["missingTime"] + 1
            
            if preNotMemberList[index]["missingTime"] <= 1/self.__dataModel["config"]["stepFunctionActivateFreqency"]:
                storeNotMemberList.append(preNotMemberList[index])
                self.__outputModel.append({
                    "frame":[{
                        "frameId": self.__dataModel["frameId"],
                        "timestamp": self.__dataModel["eventTimestamp"],
                        "imageUrl": self.__dataModel["imageUrl"],
                        "site": self.__dataModel["site"]
                    }],
                    "behaviorDetection":{
                        "personId": preNotMemberList[index]["notMemberId"],
                        "isMember": 0,
                        "inTime": preNotMemberList[index]["entryTime"],
                        "outTime": 0,
                        "stayTime": self.__dataModel["eventTimestamp"] - preNotMemberList[index]["entryTime"],
                        "coordinate_x": preNotMemberList[index]["coordinate"]["X"],
                        "coordinate_y": preNotMemberList[index]["coordinate"]["Y"],
                        "crossLine":preNotMemberList[index]["crossLine"]
                    }
                })
            
            
        response = self.__s3Write(storeNotMemberList)
        # print(response)
        
    
    def __s3Read(self):
        obj = self.__s3client.get_object(Bucket = config.s3Bucket,Key = "notMemberState.json")
        readString = obj["Body"]
        readString_utf8 = readString.read().decode('utf-8')
        return json.loads(readString_utf8)
        
    def __s3Write(self,model):
        response = self.__s3client.put_object(Bucket=config.s3Bucket, Key="notMemberState.json", Body=json.dumps(model),ACL='public-read',ContentType = 'text/json')
        return response
        
    def getModel(self):
        return self.__outputModel