import boto3
import uuid
import json
import numpy as np
import cv2
import base64


class FaceRekognition:
    def __init__(self, dataModel, aws_access_key_id, aws_secret_access_key, region_name , collection_id,sourceBucketName,faceBucketName,faceBucketSubPathList,memberFaceListBucketName,memberFaceFileName):
        self.__dataModel = dataModel
        self.__client = boto3.client('rekognition',
                                     aws_access_key_id = aws_access_key_id,
                                     aws_secret_access_key = aws_secret_access_key,
                                     region_name = region_name)
        self.__s3Client = boto3.client('s3',
                                       aws_access_key_id=aws_access_key_id,
                                       aws_secret_access_key=aws_secret_access_key,
                                       region_name=region_name)
        self.__sourceBucketName = sourceBucketName
        self.__faceBucketName = faceBucketName
        self.__faceBucketSubPathList = faceBucketSubPathList
        self.__memberFaceListBucketName = memberFaceListBucketName
        self.__memberFaceFileName = memberFaceFileName + ".json"
        self.__memberFaceList = self._getMemberFaceList()
    def rekognizeFace(self):
        if self.__dataModel["config"]["rekognize"]["mode"] == "0": #註冊模式
            if self.__dataModel["config"]["rekognize"]["register"] == True: #source端當按下按鈕(register變成True)才進行註冊
                self._storeSourceImage() #_只能由class內部呼叫
                self._registeredFace() #_只能由class內部呼叫
            else:
                return "ignore"
        elif self.__dataModel["config"]["rekognize"]["mode"] == "1": #簽到模式
            self._storeSourceImage()
            self._signInFace()
    def _registeredFace(self):
        binaryImage = base64.b64decode(self.__dataModel["frame"]["openCV"]["imageBase64"])
        faceDetectResponse = self.__client.detect_faces(Image={'Bytes': binaryImage})
        
        threshold = self.__dataModel["config"]["threshold"]
        faceCount = len(response["FaceDetails"])
        imageList = []
        memeberCounter = 0
        sumSimilarity = 0
        self.__dataModel["frame"]["memberList"] = [] #建立list
        for face in faceDetectResponse["FaceDetails"]:
            faceModel = {}
            imageList = self._spliteImage([face["BoundingBox"]])
            
            faceMatchResponse = self.__client.search_faces_by_image(CollectionId = self.__collectionId,
                            Image={'Bytes':imageList[0]},
                            FaceMatchThreshold=threshold,
                            MaxFaces=3)
            if len(faceMatchResponse["FaceMatches"]) == 0:  #新成員
                uid = str(uuid.uuid1()) #產生新成員的memberId
                faceIdList = self._createFaceData(imageList[0],uid)
                faceImageUrlList = self._storeFaceImage(faceIdList[0],imageList,uid)
                memberFaceModel = {
                    "uid":uid,
                    "faceId":faceIdList[0],
                    "faceImageUrl":faceImageUrlList[0],
                    "timestamp":self.__dataModel["frame"]["captureResult"]["timestamp"]
                }
                self.__memberFaceList["imageData"].append(memberFaceModel)
                self.__memberFaceList["memberIdList"].append(faceModel["uid"])
                self.__s3Client.put_object(Body=str(json.dumps(self.__memberFaceList)),
                                    Bucket = self.__memberFaceListBucketName,
                                    Key = self.__memberFaceFileName)
                faceModel["sourceFaceImage"] = {
                                                "imageUrl":faceImageUrlList[0],
                                                "averageSimilarity":100
                                            }
                faceModel["registrationImageList"].append({
                                                        "imageUrl":imageUrl,
                                                        "faceId":faceImageUrlList[0],
                                                        "similarity":[100.0],#新成員第一張人臉直接給定相似度100%(因為在search_faces_by_image時沒有該成員的人臉)
                                                        "timestamp":self.__dataModel["frame"]["captureResult"]["timestamp"]
                                                    })
                self.__dataModel["frame"]["memberList"].append(faceModel)
                self.__dataModel["frame"]["registrationResult"] = {}
                self.__dataModel["frame"]["registrationResult"] = {
                                                                    "memberCount":len(self.__memberFaceList["memberList"]),    #成員總數
                                                                    "personCount":len(faceDetectResponse["FaceDetails"]),    #來源人數
                                                                    "memberList":[]
                                                                }
                self.__dataModel["frame"]["registrationResult"]["memberList"].append({
                                                                                        "memberId":uid,
                                                                                        "registrationImageCount":1,
                                                                                        "matchedImageCount":1,
                                                                                        "averageSimilarity":100.0,
                                                                                        "registrationImageList":[{
                                                                                            "faceId":faceIdList[0],
                                                                                            "similarity":100.0,
                                                                                            "timestamp":self.__dataModel["frame"]["captureResult"]["timestamp"]
                                                                                        }]
                                                                                    }
            else: #已經註冊過
                faceIdList = [] #先清空
                faceImageIdList = []
                faceImageUrlList = []
                faceModel["uid"] = faceMatchResponse["FaceMatches"][0]["Face"]["ExternalImageId"] #取出匹配到的成員id
                
                faceImageIdList = self._createFaceData(imageList[0],faceModel["uid"])
                faceImageUrlList = self._storeFaceImage(faceModel["newFaceId"],imageList,faceModel["uid"])
                memberFaceModel = {
                    "uid":faceModel["uid"],
                    "faceId":faceImageIdList[0],
                    "faceImageUrl":faceImageUrlList[0],
                    "timestamp":self.__dataModel["frame"]["captureResult"]["timestamp"]
                }
                self.__memberFaceList["imageData"].append(memberFaceModel)
                memberFaceListResponse = self.__s3Client.list_objects_v2(Bucket=self.__faceBucketName,
                                                                     StartAfter=self.__faceBucketSubPathList[0] + faceModel["uid"])
                registrationImageList = []
                faceModel["registrationResult"] = {}
                
                for face in memberFaceListResponse["Contents"]:
                    uid,faceImageId = face["Key"].split('_')[0],face["Key"].split('_')[1]
                    uid = uid.split('/')[1]
                    if uid ==faceModel["uid"]:
                        faceImageIdList.append(faceImageId)
                faceModel["registrationImageCount"] = len(faceImageIdList)
                for face in faceMatchResponse["FaceMatches"]:
                    if face["Similarity"] > 90 and face["Face"]["FaceId"] + '.jpg' in faceImageIdList: #相似度90以上且檔案名稱含有該成員uid才加入至list中
                        faceImageUrl = 'https://' + self.__faceBucketName + '.s3-' + self.__region_name + '.amazonaws.com/' + self.__faceBucketSubPathList[0] + '/' + faceModel["uid"] + '_' + face["Face"]["FaceId"] + ".jpg"
                        faceImageUrlList.append(faceImageUrl)
                        faceIdList.append(face["Face"]["FaceId"])
                        sumSimilarity += face["Similarity"]
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
                        
                        faceModel["registrationResult"]["memberList"].append({
                                                                            "memberId":faceMatchResponse["FaceMatches"][0]["Face"]["ExternalImageId"],
                                                                            "registrationImageCount":len(faceMatchResponse["FaceMatches"]),
                                                                            "matchedImageCount":len(faceIdList),
                                                                            "averageSimilarity":sumSimilarity / len(faceIdList),
                                                                            "registrationImageList":[{
                                                                                "faceId":face["Face"]["FaceId"],
                                                                                "similarity":face["Similarity"],
                                                                                "timestamp":next(member for member in self.__memberFaceList["imageData"] if member["faceId"] == regModel["faceId"])["timestamp"]
                                                                        })
                    faceModel["memberList"].append({
                                                        "sourceFaceImage":{
                                                            "imageUrl":faceImageUrlList[0],
                                                            "averageSimilarity":sumSimilarity / len(faceIdList)
                                                        },
                                                        "registrationImageList":registrationImageList
                                                    })
                faceModel["registrationResult"]["memberCount"] = len(self.__memberFaceList["memberIdList"])
                faceModel["registrationResult"]["personCount"] = len(faceDetectResponse["FaceDetails"])
            self.__dataModel["frame"]["registrationResult"] = faceModel
            
    def _signInFace(self):
        image = self.__dataModel["frame"]["openCV"]["imageBase64"]
        binaryImage = base64.b64decode(self.__dataModel["frame"]["openCV"]["imageBase64"])
        faceDetectResponse = self.__client.detect_faces(Image={'Bytes': binaryImage})

        personList = []
        personCounter = len(faceDetectResponse["FaceDetails"])
        
        faceIdList = []
        faceBoundingBoxList = []
        faceImageIdList = []
        faceImageUrlList = []
        registrationImageList = [] #成員已註冊的人臉資料
        registrationImageCounter = 0 #成員已註冊的人臉數
        matchedImageCounter = 0 #匹配到的成員已註冊人臉數
        memberCounter = 0
        sumSimilarity = 0
        averageSimilarity = 0
        serialNo = 0 #多張人臉需要編號
        
        self.__dataModel["signInResult"] = {}
        self.__dataModel["signInResult"]["personList"] = []
        self.__dataModel["frame"]["personList"] = []
        self.__dataModel["frame"]["sourceImage"]["personCount"] = personCounter
        
        if len(faceDetectResponse["FaceDetails"]) >= 1: #複數人臉
            for face in faceDetectResponse["FaceDetails"]:
                faceBoundingBoxList.append(face["BoundingBox"])
            binaryImage = base64.b64decode(image)
            faceImageList = self._spliteImage(faceBoundingBoxList) #切割
            faceImageUrlList = self._storeFaceImage(faceImageList)
            
            for faceImage in faceImageList: 
                searchFaceResponse=self.__client.search_faces_by_image(CollectionId=self.__collectionId, #成員與簽到人臉匹配
                                    Image={'Bytes':faceImage},
                                    FaceMatchThreshold=80,
                                    MaxFaces=10)
                faceImageIdList = [] #清空
                personList = {} #清空
                matchedImageCounter = len(searchFaceResponse["FaceMatches"]) #重新判斷
                registrationImageList = [] #清空
                if len(searchFaceResponse["FaceMatches"]) != 0:
                    memberFaceListResponse = self.__s3Client.list_objects_v2(Bucket=self.__sourceBucketName,StartAfter = self.__faceBucketSubPathList[0] + '/' + searchFaceResponse["FaceMatches"][0]["Face"]["ExternalImageId"])
                    for face in memberFaceListResponse["Contents"]: #成員所有已註冊的人臉數
                        uid,faceImageId = face["Key"].split('_')[0],face["Key"].split('_')[1]
                        uid = uid.split('/')[1]
                        if uid == searchFaceResponse["FaceMatches"][0]["Face"]["ExternalImageId"]: #根據對應的成員id將對應成員的人臉加入list
                            faceImageIdList.append(faceImageId)
                    registrationImageCounter = len(faceImageIdList)
                    sumSimilarity = 0 #重新計算
                    for face in searchFaceResponse["FaceMatches"]: #成員與簽到人臉匹配(條件)
                        if face["Similarity"] > 70 and face["Face"]["FaceId"] + '.jpg' in faceImageIdList:
                            registrationModel = {}
                            faceImageUrl = 'https://' + self.__sourceBucketName + '.s3-' + self.__region_name + '.amazonaws.com/' + self.__faceBucketSubPathList[0] + '/' + searchFaceResponse["FaceMatches"][0]["Face"]["ExternalImageId"] + '_' + face["Face"]["FaceId"] + ".jpg"
                            faceImageUrlList.append(faceImageUrl)
                            faceIdList.append(face["Face"]["FaceId"])
                            sumSimilarity += face["Similarity"]
                            try:
                                timestamp = next(member for member in self.__memberFaceList["imageData"] if member["faceId"] == face["Face"]["FaceId"])["timestamp"]
                            except StopIteration: #上面的寫法會剛好超出list長度1 所以用try-except去忽略此錯誤
                                print("StopIteration stop")
                            registrationModel["imageUrl"] = faceImageUrl #faceImageUrlList[serialNo]
                            registrationModel["faceId"] = face["Face"]["FaceId"]
                            registrationModel["similarity"] = face["Similarity"]
                            registrationModel["timestamp"] = timestamp
                            registrationImageList.append(registrationModel)
                        """if searchFaceResponse["FaceMatches"][0]["Face"]["ExternalImageId"] not in memberList:
                            memberList.append(searchFaceResponse["FaceMatches"][0]["Face"]["ExternalImageId"])"""
                        
                    averageSimilarity = sumSimilarity / len(registrationImageList)    
                    self.__dataModel["signInResult"]["personList"].append({
                                                                            "isMember":True,
                                                                            "memberId":searchFaceResponse["FaceMatches"][0]["Face"]["ExternalImageId"],
                                                                            "registrationImageCount":len(faceImageIdList),
                                                                            "matchedImageCount":matchedImageCounter,
                                                                            "averageSimilarity":averageSimilarity
                                                                        })
                    
                    fileName = self.__faceBucketSubPathList[1] + '/face' + str(self.__dataModel["frame"]["captureResult"]["timestamp"]) + str(serialNo) + '.jpg'
                    serialNo += 1
                    memberCounter += 1
                    personList={
                                "sourceFaceImage":{"imageUrl":'https://' + self.__sourceBucketName + '.s3-' + self.__region_name + '.amazonaws.com/' + fileName,
                                                    "averageSimilarity": averageSimilarity},
                                "registrationImageList":registrationImageList,
                                }
                    self.__dataModel["frame"]["personList"].append(personList)
                elif len(searchFaceResponse["FaceMatches"]) ==0:
                    self.__dataModel["signInResult"]["personList"].append({
                                                                            "isMember":False
                                                                        })
                    serialNo += 1
            self.__dataModel["signInResult"]["personCount"] = personCounter
            self.__dataModel["signInResult"]["memberCount"] = memberCounter
            self.__dataModel["signInResult"]["notMemberCount"] = self.__dataModel["signInResult"]["personCount"] - self.__dataModel["signInResult"]["memberCount"]
            self.__dataModel["signInResult"]["timestamp"] = self.__dataModel["frame"]["captureResult"]["timestamp"]
            self.__dataModel["frame"]["sourceImage"]["personCount"] = len(faceDetectResponse["FaceDetails"])
    def _spliteImage(self,boundingboxes):
        imagelist = []
        image = np.fromstring(self.__dataModel["frame"]["openCV"]["imageBase64"],np.uint8)
        image = cv2.imdecode(image,cv2.IMREAD_COLOR)
        size = image.shape
        height , width = size[0],size[1]
        for BBox in boundingboxes:
            print("---------------")
            print(BBox)
            upperLeftPointX = int(BBox['Left']*width)
            upperLeftPointY = int(BBox['Top']*height)               
            lowerRightPointX = int((BBox['Left']+BBox['Width'])*width)
            lowerRightPointY = int((BBox['Top']+BBox['Height'])*height)
            cut_image = copy.deepcopy(image)[upperLeftPointY:lowerRightPointY,upperLeftPointX:lowerRightPointX]
            cut_image = base64.b64encode(cv2.imencode('.jpg', cut_image)[1]).decode() 
            cut_image = base64.b64decode(cut_image)

            imagelist.append(cut_image)

        print(len(imagelist))
        print("cut finish")
        return imagelist
    def _storeFaceImage(self,faceId,imageList,uid):
        faceImageUrlList = []
        serialNo = 0 #非註冊模式下儲存人臉的順序
        if self.__dataModel["config"]["rekognize"]["mode"] == "0":
            subPath = self.__faceBucketSubPathList[0]
        else:
            subPath = self.__faceBucketSubPathList[1]
        for image in imageList:
            if self.__dataModel["config"]["rekognize"]["mode"] == "0":
                fileName = subPath + '/' + uid + '_' + faceId + '.jpg' #註冊的照片名稱(含子路徑位置)
            else:
                fileName = subPath + '/face' + str(self.__dataModel["frame"]["captureResult"]["timestamp"]) + str(serialNo) + '.jpg' #簽到的照片名稱(含子路徑位置)
            response=self.__s3Client.put_object(ACL='public-read',
                                                Body=image,
                                                Bucket=self.__faceBucketName,
                                                Key=fileName,
                                                ContentEncoding='base64',
                                                ContentType='image/jpeg')
            faceImageUrlList.append('https://' + self.__faceBucketName + '.s3-' + self.__region_name + '.amazonaws.com/' + fileName)
            serialNo += 1
        return faceImageUrlList
    def _storeSourceImage(self):
        image = self.__dataModel["frame"]["openCV"]["imageBase64"]
        image = base64.b64decode(image)
        fileName = self.__dataModel["frame"]["captureResult"]["id"]
        self.__client.put_object(ACL='public-read',
                                 Body=image,
                                 Bucket=self.__sourceBucketName,
                                 Key=fileName ,
                                 ContentEncoding='base64',
                                 ContentType='image/jpeg')
        self.__dataModel["frame"]["sourceImage"] = {}
        self.__dataModel["frame"]["sourceImage"]["imageUrl"] = 'https://' + self.__sourceBucketName + '.s3-' + self.__region_name + '.amazonaws.com/' + fileName
        self.__dataModel["frame"]["sourceImage"]["timestamp"] = self.__dataModel["frame"]["captureResult"]["timestamp"]
    def _createFaceData(self,binaryImage,uid):
        faceIdList = []
        response=self.__client.index_faces(CollectionId=self.__collectionId,
                                    Image={'Bytes':binaryImage},
                                    MaxFaces=1,
                                    ExternalImageId=uid,
                                    QualityFilter="AUTO",
                                    DetectionAttributes=['ALL'])
        for face in response['FaceRecords']:
            faceIdList.append(face['Face']['FaceId'])
        return faceIdList
    def _getMemberFaceList(self):
        body = self.__s3Client.get_object(Bucket = self.__memberFaceListBucketName,
                                          Key = self.__memberFaceFileName)['Body']
        jsonString = body.read().decode('utf-8')
        faceList = json.loads(jsonString) #{"imageData":[],memberIdList}
        body.close()
        return faceList
    def getModel(self):
        self.__datamodel["frame"]["openCV"]["imageBase64"] = "" #影像資料過長因此在最後清空
        return self.__datamodel
