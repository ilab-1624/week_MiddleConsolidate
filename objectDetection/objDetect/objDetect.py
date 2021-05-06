import boto3
import base64
import numpy as np
import cv2
import time

class ObjDetection:
    def __init__(self, dataModel, aws_access_key_id, aws_secret_access_key, region_name):
        self.__dataModel = dataModel
        self.__client = boto3.client('rekognition',
                                    aws_access_key_id =  aws_access_key_id,
                                    aws_secret_access_key = aws_secret_access_key, 
                                    region_name = region_name)
        self.__s3Client = boto3.client('s3',
                                    aws_access_key_id =  aws_access_key_id,
                                    aws_secret_access_key = aws_secret_access_key, 
                                    region_name = region_name)
        self.__region_name = region_name
        
    def objDetect(self,objectBucketName):
        client = self.__client
        maxLabels = 15
        minConfidence = 30
        objectCount = 0
        objectList = []
        objectImageUrlList = []
        objectBucketName = objectBucketName
        binaryImage = base64.b64decode(self.__dataModel["frame"]["openCV"]["imageBase64"])
        
        originalImage = np.fromstring(binaryImage,np.uint8)
        originalImage = cv2.imdecode(originalImage,cv2.IMREAD_COLOR)
        size = originalImage.shape
        height , width = size[0] , size[1]
        self.__dataModel["objectDetection"] = {}
        
        response = self.__client.detect_labels(Image = {'Bytes':binaryImage},
                                              MaxLabels = maxLabels,
                                              MinConfidence = minConfidence)
        if len(response["Labels"]) == 0:
            objectCount = 0
            objectList = []
        elif len(response["Labels"]) > 0:
            for obj in response["Labels"]:
                try:
                    if "BoundingBox" in obj["Instances"][0]:
                        objectCount += 1
                        obj["boundingBox"] = []
                        obj["confidence"] = []
                        for target in obj["Instances"]:
                            obj["boundingBox"].append(target["BoundingBox"])
                            obj["confidence"].append(target["Confidence"])

                        imageList = self.spliteImage(binaryImage,obj["boundingBox"])

                        objectImageUrlList = self.storeObjectImage(obj["Name"],imageList,objectBucketName)

                        obj["coordination"] = []
                        for coord in obj["boundingBox"]:
                            obj["coordination"].append({"X":coord["Left"] + coord["Width"] / 2,
                                                        "Y":coord["Top"] + coord["Height"] / 2})

                        del obj["Parents"]
                        del obj["Instances"]
                        obj["name"] = obj["Name"]
                        del obj["Name"]
                        del obj["Confidence"]
                        obj["objectImageUrl"] = objectImageUrlList
                        objectList.append(obj)
                except Exception as e:
                    print(e)
        self.__dataModel["objectDetection"]["detectionResult"] = {"objectCount":objectCount,"objectList":objectList}
    def spliteImage(self,frame,boundingboxes):
        imagelist = []
        image = np.fromstring(frame,np.uint8)
        image = cv2.imdecode(image,cv2.IMREAD_COLOR)
        size = image.shape
        height , width = size[0],size[1]
        for BBox in boundingboxes:
            print("---------------")
            #print(BBox)
            upperLeftPointX = int(BBox['Left']*width)
            upperLeftPointY = int(BBox['Top']*height)               
            lowerRightPointX = int((BBox['Left']+BBox['Width'])*width)
            lowerRightPointY = int((BBox['Top']+BBox['Height'])*height)
            
            cut_image = copy.deepcopy(image)[upperLeftPointY:lowerRightPointY,upperLeftPointX:lowerRightPointX]

            cut_image = base64.b64encode(cv2.imencode('.jpg', cut_image)[1]).decode() 
            cut_image = base64.b64decode(cut_image)

            imagelist.append(cut_image) 

        print(len(imagelist))
        return imagelist
    def storeObjectImage(self,objectName,imageList,objectBucketName):
        client = self.__s3Client
        serialNo = 1
        objectImageUrlList = []
        for image in imageList:
            
            objectName = objectName.replace(" ", "_")
            timeStr = str(time.time())
            fileName = objectName + timeStr + '_' +str(serialNo) + '.jpg'
            bucketName = objectBucketName
            response=client.put_object(ACL='public-read',Body=image, Bucket=bucketName, Key=fileName ,ContentEncoding='base64',ContentType='image/jpeg')
            serialNo += 1
            objectImageUrlList.append('https://' + objectBucketName + '.s3-' + self.__region_name + '.amazonaws.com/' + fileName)
        return objectImageUrlList
    def storeImage(self, bucketName):
        client = self.__s3Client
        image = self.__dataModel["frame"]["openCV"]["imageBase64"]
        image = base64.b64decode(image)
        
        fileName = self.__dataModel["frame"]["captureResult"]["id"]
        
        client.put_object(ACL='public-read',Body=image, Bucket=bucketName, Key=fileName ,ContentEncoding='base64',ContentType='image/jpeg')
        self.__dataModel["objectDetection"]["s3"] = {}
        self.__dataModel["objectDetection"]["s3"]["sourceImageUrl"] = 'https://' + bucketName + '.s3-' + self.__region_name + '.amazonaws.com/' + fileName
    def modifyDataModel(self):
        dataModel = self.__dataModel
        newObjectList = []
        for obj in dataModel["objectDetection"]["detectionResult"]["objectList"]:
            for i in range(len(obj["boundingBox"])):
                newDataModel = {}
                newDataModel["name"] = obj["name"]
                newDataModel["boundingBox"] = obj["boundingBox"][i]
                newDataModel["coordination"] = obj["coordination"][i]
                newDataModel["confidence"] = obj["confidence"][i]
                newDataModel["objectImageUrl"] = obj["objectImageUrl"][i]
                newObjectList.append(newDataModel)
        self.__dataModel["objectDetection"]["detectionResult"]["objectList"] = newObjectList
    def getModel(self):
        self.__dataModel["frame"]["openCV"]["imageBase64"] = ""
        
        return self.__dataModel
