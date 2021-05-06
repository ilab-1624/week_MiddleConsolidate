import cv2
import base64
from cutImage import image_splite
import time
import config
import boto3
# from toElastic import storeToElastic

def lambda_handler(event, context):
    client = boto3.client('s3', aws_access_key_id=config.aws_access_key_id, aws_secret_access_key=config.aws_secret_access_key,region_name=config.region_name)
    image = event["image"]
    image_binary = base64.b64decode(image)
    fileName = event['id'] + '.jpg'
    bucketName = event['config']['s3Bucket']
    client.put_object(ACL='public-read',Body=image_binary, Bucket=bucketName, Key=fileName ,ContentEncoding='base64',ContentType='image/jpeg')
    imageUrl = 'https://' + bucketName + '.s3-' + config.region_name + '.amazonaws.com/' + fileName
    
    outputModel = {}
    outputModel["eventTimestamp"] = event["timestamp"]
    outputModel["searchFaceResponse"] = []
    # image = event["image"]
    # image_binary = base64.b64decode(image)
    photo = event["id"] + '.jpg'
    bucket = event["config"]["s3Bucket"]
    client = boto3.client('rekognition', aws_access_key_id=config.aws_access_key_id, aws_secret_access_key=config.aws_secret_access_key,region_name=config.region_name)
    detectFaceResponse = client.detect_faces(Image={'S3Object':{'Bucket':bucket,'Name':photo}},Attributes=['ALL'])
    faceCount = len(detectFaceResponse["FaceDetails"])
    outputModel["detectFaceResponse"] = detectFaceResponse
    
    if faceCount == 1:
        searchFaceResponse=client.search_faces_by_image(CollectionId=config.collectionId,
                                Image={'S3Object':{'Bucket':bucket,'Name':photo}},
                                FaceMatchThreshold=70,
                                MaxFaces=10)
        outputModel["searchFaceResponse"].append(searchFaceResponse)
        
    elif faceCount > 1:
        faceBoundingBox = []
        for face in detectFaceResponse["FaceDetails"]:
            faceBoundingBox.append(face["BoundingBox"])
        # image_binary = base64.b64decode(image)
        faceImageList = image_splite(image_binary,faceBoundingBox)
    
        for faceImage in faceImageList:
            searchFaceResponse=client.search_faces_by_image(CollectionId=config.collectionId,
                                Image={'Bytes':faceImage},
                                FaceMatchThreshold=70,
                                MaxFaces=10)
            outputModel["searchFaceResponse"].append(searchFaceResponse)
    ppeDetectResponse = client.detect_protective_equipment(Image={'S3Object':{'Bucket':bucket,'Name':photo}},SummarizationAttributes={'MinConfidence':70, 'RequiredEquipmentTypes':['FACE_COVER', 'HAND_COVER', 'HEAD_COVER']})
    outputModel["ppeDetectResponse"] = ppeDetectResponse
    outputModel["site"] = event["config"]["site"]
    outputModel["imageUrl"] = imageUrl
    outputModel["frameId"] = event["id"] 
    outputModel["config"] = event["config"]
    # storeToElastic(outputModel, event["config"]["site"])
    # print(outputModel)
    return outputModel