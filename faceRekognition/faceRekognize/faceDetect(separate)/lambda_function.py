import json
from faceDetect import S3,Rekognition,FaceDetection #class
import config


def lambda_handler(event, context):
    dataModel = event
    print(dataModel)
    print("--------------------")
    s3 = S3(config.regionName,
            config.bucketName,
            config.aws_access_key_id,
            config.aws_secret_access_key)
    rekognition = Rekognition(config.regionName,
                              config.aws_access_key_id,
                              config.aws_secret_access_key,
                              dataModel["frame"]["openCV"]["imageBase64"])
    faceDetection = FaceDetection(config,
                                  dataModel,
                                  s3,
                                  rekognition,
                                  config.collectionId,
                                  config.memberFaceFileName)
    if dataModel["config"]["register"] == True:
        faceDetection.registeredFace()
    #faceRekognition = FaceRekognition()
    #faceRekognition.rekognizeFace()

    return faceDetection.getModel()
