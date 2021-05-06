import json
from faceSearch import S3,Rekognition,FaceSearch #class
import config


def lambda_handler(event, context):
    dataModel = event
    s3 = S3(config.regionName,
            config.bucketName,
            config.aws_access_key_id,
            config.aws_secret_access_key)
    rekognition = Rekognition(config.regionName,
                              config.aws_access_key_id,
                              config.aws_secret_access_key,
                              dataModel["frame"]["openCV"]["imageBase64"])
    faceSearch = FaceSearch(config,
                                  dataModel,
                                  s3,
                                  rekognition,
                                  config.collectionId,
                                  config.memberFaceFileName)
    faceSearch.signInFace()
    #faceRekognition = FaceRekognition()
    #faceRekognition.rekognizeFace()

    return faceSearch.getModel()
