import boto3
import uuid
import json
import numpy as np
import cv2
import base64
import copy

class S3:
    def __init__(self,regionName,bucketName,aws_access_key_id,aws_secret_access_key):
        self.__regionName = regionName
        self.__bucketName = bucketName
        self.__aws_access_key_id = aws_access_key_id
        self.__aws__secret_access_key = aws_secret_access_key
        self.__client = boto3.client('s3',
                                     aws_access_key_id=aws_access_key_id,
                                     aws_secret_access_key=aws_secret_access_key,
                                     region_name=regionName)
    def storeJson(self,key,body):
        self.__client.put_object(Body=str(json.dumps(body)),
                                Bucket = self.__bucketName,
                                Key = key)
    def readJson(self,key):
        body = self.__client.get_object(Bucket = self.__bucketName,
                                          Key = key)['Body']
        jsonString = body.read().decode('utf-8')
        jsonData = json.loads(jsonString) #{"imageData":[],memberIdList}
        body.close()
        return jsonData
    def listObjects(self,keyword):
        listObjectsResponse = self.__client.list_objects_v2(Bucket=self.__bucketName,
                                                                 StartAfter=keyword)
        return listObjectsResponse
    def storeImage(self,image,fileName):
        #image = self.__dataModel["frame"]["openCV"]["imageBase64"]
        #image = base64.b64decode(image)
        #fileName = "image" + self.__dataModel["frame"]["captureResult"]["id"]
        self.__client.put_object(ACL='public-read',
                                 Body=image,
                                 Bucket=self.__bucketName,
                                 Key=fileName ,
                                 ContentEncoding='base64',
                                 ContentType='image/jpeg')
        imageUrl = ['https://' + self.__bucketName + '.s3-' + self.__regionName + '.amazonaws.com/' + fileName]
        return imageUrl
    def getBucketName(self):
        return self.__bucketName
    def getRegionName(self):
        return self.__regionName
class Rekognition:
    def __init__(self,regionName,aws_access_key_id,aws_secret_access_key,image):
        self.__regionName = regionName
        self.__aws_access_key_id = aws_access_key_id
        self.__aws_secret_access_key = aws_secret_access_key
        self.__client = boto3.client('rekognition',
                                     aws_access_key_id=aws_access_key_id,
                                     aws_secret_access_key=aws_secret_access_key,
                                     region_name=regionName)
        self.__image = image
        self.__rekognitionModel = {}
    def faceDetect(self):
        binaryImage = base64.b64decode(self.__image)
        faceDetectResponse = self.__client.detect_faces(Image={'Bytes': binaryImage})
        #print(faceDetectResponse)
        return faceDetectResponse
    def faceSearch(self,collectionId,image,threshold):
        faceMatchResponse = {}
        try:
            faceMatchResponse = self.__client.search_faces_by_image(CollectionId = collectionId,
                                                                    Image={'Bytes':image},
                                                                    FaceMatchThreshold=threshold,
                                                                    MaxFaces=1)
        except:
            faceMatchResponse["FaceMatches"] = []
        return faceMatchResponse
    def faceCreate(self,collectionId,image,uid):
        #print("create")
        #print(collectionId)
        #print(image)
        #print(uid)
        faceCreateResponse=self.__client.index_faces(CollectionId=collectionId,
                                                    Image={'Bytes':image},
                                                    MaxFaces=3,
                                                    ExternalImageId=uid,
                                                    QualityFilter="AUTO",
                                                    DetectionAttributes=['ALL'])
        #print(faceCreateResponse)
        #print("line88")
        return faceCreateResponse
    def getModel(self):
        return self.__rekognitionModel

class FaceDetection:
    def __init__(self,config,dataModel,s3,rekognition,collectionId,memberFaceFileName):
        self.__config = config
        self.__dataModel = dataModel
        self.__s3 = s3
        self.__rekognition = rekognition
        self.__collectionId = collectionId
        self.__memberFaceFileName = memberFaceFileName
        self.__memberFaceList = {}
    def registeredFace(self):
        binaryImage = base64.b64decode(self.__dataModel["frame"]["openCV"]["imageBase64"])
        #faceDetectResponse = self.__client.detect_faces(Image={'Bytes': binaryImage})
        faceDetectResponse = self.__rekognition.faceDetect()

        threshold = 80 #等待config的threshold
        faceCount = len(faceDetectResponse["FaceDetails"])
        #print("faceCount:"+str(faceCount))
        imageList = []
        memeberCounter = 0
        sumSimilarity = 0
        #self.__dataModel["memberList"] = [] #建立list
        self.__memberFaceList = self.__s3.readJson(self.__memberFaceFileName)
        #self.__memberFaceList["memberIdList"] = self.__s3.readJson(self.__memberFaceFileName)["memberIdList"]
        #self.__memberFaceList["imageData"] = self.__s3.readJson(self.__memberFaceFileName)["imageData"]
        #print(type(self.__memberFaceList))
        #print("listhere")
        for face in faceDetectResponse["FaceDetails"]:
            faceModel = {}
            imageList = self.spliteImage([face["BoundingBox"]])

            """faceMatchResponse = self.__client.search_faces_by_image(CollectionId = self.__collectionId,
                            Image={'Bytes':imageList[0]},
                            FaceMatchThreshold=threshold,
                            MaxFaces=3)"""
            faceMatchResponse = self.__rekognition.faceSearch(self.__collectionId,imageList[0],threshold)
            if len(faceMatchResponse["FaceMatches"]) == 0:  #新成員
                uid = str(uuid.uuid1()) #產生新成員的memberId
                faceIdList = self._createFaceData(imageList[0],uid)
                #print("list")
                #print(faceIdList)
                fileName = uid + '_' + faceIdList[0] + '.jpg'
                faceImageUrlList = self.__s3.storeImage(imageList[0],fileName)
                #print(faceImageUrlList)
                memberFaceModel = {
                    "uid":uid,
                    "faceId":faceIdList[0],
                    "faceImageUrl":faceImageUrlList[0],
                    "timestamp":self.__dataModel["frame"]["captureResult"]["timestamp"]
                }
                self.__memberFaceList["imageData"].append(memberFaceModel)
                self.__memberFaceList["memberIdList"].append(uid)
                '''self.__s3Client.put_object(Body=str(json.dumps(self.__memberFaceList)),
                                    Bucket = self.__memberFaceListBucketName,
                                    Key = self.__memberFaceFileName)'''
                #
                self.__s3.storeJson(self.__memberFaceFileName,self.__memberFaceList)
                faceModel["sourceFaceImage"] = {
                                                "imageUrl":faceImageUrlList[0],
                                                "averageSimilarity":100
                                            }
                faceModel["registrationImageList"] = []
                faceModel["registrationImageList"].append({
                                                        "imageUrl":faceImageUrlList[0],
                                                        "faceId":faceIdList[0],
                                                        "similarity":[100.0],#新成員第一張人臉直接給定相似度100%(因為在search_faces_by_image時沒有該成員的人臉)
                                                        "timestamp":self.__dataModel["frame"]["captureResult"]["timestamp"]
                                                    })
                self.__dataModel["memberList"].append(faceModel)
                self.__dataModel["validationResult"] = {}
                self.__dataModel["validationResult"] = {
                                                        "memberCount":len(self.__memberFaceList["memberIdList"]),    #成員總數
                                                        "personCount":len(faceDetectResponse["FaceDetails"]),    #來源人數
                                                        "memberList":[]
                                                        }
                self.__dataModel["validationResult"]["memberList"].append({
                                                                                        "memberId":uid,
                                                                                        "registrationImageCount":1,
                                                                                        "matchedImageCount":1,
                                                                                        "averageSimilarity":100.0,
                                                                                        "registrationImageList":[{
                                                                                            "faceId":faceIdList[0],
                                                                                            "similarity":100.0,
                                                                                            "timestamp":self.__dataModel["frame"]["captureResult"]["timestamp"]
                                                                                        }]
                                                                                    })
            else: #已經註冊過
                faceIdList = [] #先清空
                faceImageIdList = []
                faceImageUrlList = []
                faceModel["uid"] = faceMatchResponse["FaceMatches"][0]["Face"]["ExternalImageId"] #取出匹配到的成員id
                faceModel["memberList"] = []
                faceImageIdList = self._createFaceData(imageList[0],faceModel["uid"])
                fileName = faceModel["uid"] + '_' + faceImageIdList[0] + '.jpg'
                faceImageUrlList = self.__s3.storeImage(imageList[0],fileName) ###
                memberFaceModel = {
                    "uid":faceModel["uid"],
                    "faceId":faceImageIdList[0],
                    "faceImageUrl":faceImageUrlList[0],
                    "timestamp":self.__dataModel["frame"]["captureResult"]["timestamp"]
                }
                #print(memberFaceModel)
                #print(self.__memberFaceList)
                #print(type(self.__memberFaceList))
                #print(type(json.loads(self.__memberFaceList)))
                self.__memberFaceList["imageData"].append(memberFaceModel)
                """memberFaceListResponse = self.__s3Client.list_objects_v2(Bucket=self.__faceBucketName,
                                                                     StartAfter=self.__faceBucketSubPathList[0] + faceModel["uid"])"""
                ###
                #print("------line201")
                #print(self.__memberFaceList)
                self.__s3.storeJson(self.__memberFaceFileName,self.__memberFaceList)
                memberFaceListResponse = self.__s3.listObjects(faceModel["uid"])
                registrationImageList = []
                faceModel["validationResult"] = {}
                faceModel["validationResult"]["memberList"] = []
                for face in memberFaceListResponse["Contents"]:
                    #print("face[]")
                    #print(face["Key"])
                    try:
                        uid,faceImageId = face["Key"].split('_')[0],face["Key"].split('_')[1]
                        #uid = uid.split('/')[1]
                        if uid == faceModel["uid"]:
                            faceImageIdList.append(faceImageId)
                    except Exception as e:
                        print(e)
                        break
                faceModel["registrationImageCount"] = len(faceImageIdList)
                #print(faceImageIdList)
                #print("registration------")
                #print(faceMatchResponse["FaceMatches"])
                for face in faceMatchResponse["FaceMatches"]:
                    if face["Similarity"] > 90 and face["Face"]["FaceId"] + '.jpg' in faceImageIdList: #相似度90以上且檔案名稱含有該成員uid才加入至list中
                        faceImageUrl = 'https://' + self.__s3.getBucketName() + '.s3-' + self.__s3.getRegionName() + '.amazonaws.com/' + faceModel["uid"] + '_' + face["Face"]["FaceId"] + ".jpg"
                        faceImageUrlList.append(faceImageUrl)
                        faceIdList.append(face["Face"]["FaceId"])
                        sumSimilarity += face["Similarity"]
                        timestamp = ""
                        #print("member[faceId]")
                        #print(self.__memberFaceList["imageData"])
                        try:
                            timestamp = next(member for member in self.__memberFaceList["imageData"] if member["faceId"] == face["Face"]["FaceId"])["timestamp"]
                        except StopIteration: #上面的寫法會剛好超出list長度1 所以用try-except去忽略此錯誤
                            print("StopIteration stop")
                        registrationImageList.append({
                                                        "imageUrl":faceImageUrl,
                                                        "faceId":face["Face"]["FaceId"],
                                                        "similarity":face["Similarity"],
                                                        "timestamp":timestamp
                                                    })

                        faceModel["validationResult"]["memberList"].append({
                                                                            "memberId":faceMatchResponse["FaceMatches"][0]["Face"]["ExternalImageId"],
                                                                            "registrationImageCount":len(faceMatchResponse["FaceMatches"]),
                                                                            "matchedImageCount":len(faceIdList),
                                                                            "averageSimilarity":sumSimilarity / len(faceIdList),
                                                                            "registrationImageList":[{
                                                                                "faceId":face["Face"]["FaceId"],
                                                                                "similarity":face["Similarity"],
                                                                                "timestamp":timestamp
                                                                                }]
                                                                        })
                    faceModel["memberList"].append({
                                                        "sourceFaceImage":{
                                                            "imageUrl":faceImageUrlList[0],
                                                            "averageSimilarity":sumSimilarity / len(faceIdList)
                                                        },
                                                        "registrationImageList":registrationImageList
                                                    })
                faceModel["validationResult"]["memberCount"] = len(self.__memberFaceList["memberIdList"])
                faceModel["validationResult"]["personCount"] = len(faceDetectResponse["FaceDetails"])
            self.__dataModel["validationResult"] = faceModel
            break ###
    def spliteImage(self,boundingboxes):
        imagelist = []
        image = np.fromstring(base64.b64decode(self.__dataModel["frame"]["openCV"]["imageBase64"]),np.uint8)
        image = cv2.imdecode(image,cv2.IMREAD_COLOR)
        size = image.shape
        height , width = size[0],size[1]
        for BBox in boundingboxes:
            #print("---------------")
            #print(BBox)
            upperLeftPointX = int(BBox['Left']*width)
            upperLeftPointY = int(BBox['Top']*height)
            lowerRightPointX = int((BBox['Left']+BBox['Width'])*width)
            lowerRightPointY = int((BBox['Top']+BBox['Height'])*height)
            cut_image = copy.deepcopy(image)[upperLeftPointY:lowerRightPointY,upperLeftPointX:lowerRightPointX]
            cut_image = base64.b64encode(cv2.imencode('.jpg', cut_image)[1]).decode()
            cut_image = base64.b64decode(cut_image)

            imagelist.append(cut_image)

        #print(len(imagelist))
        #print("cut finish")
        return imagelist
    def _createFaceData(self,binaryImage,uid):
        faceIdList = []
        response = self.__rekognition.faceCreate(self.__collectionId,binaryImage,uid)
        for face in response['FaceRecords']:
            faceIdList.append(face['Face']['FaceId'])
        return faceIdList
    def getModel(self):
        self.__dataModel["frame"]["openCV"]["imageBase64"] = ""
        print(self.__dataModel)
        return self.__dataModel

