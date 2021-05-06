import json
from faceRekognitize import FaceRekognition #class
import config


def lambda_handler(event, context):
    dataModel = event

    faceRekognition = FaceRekognition(dataModel,
                                      config.aws_access_key_id,
                                      config.aws_secret_access_key,
                                      config.region_name,
                                      config.collection_id,
                                      config.sourceBucketName,
                                      config.faceBucketName,
                                      config.faceBucketSubPathList,
                                      config.memberFaceListBucketName,
                                      config.memberFaceFileName)
    faceRekognition.rekognizeFace()
    
    return faceRekognition.getModel()
