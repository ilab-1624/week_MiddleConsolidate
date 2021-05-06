import json
import cv2
import base64
import config
from objDetect import ObjDetection

def lambda_handler(event, context):
    dataModel = event
    
    objDetection = ObjDetection(dataModel, config.aws_access_key_id, config.aws_secret_access_key, config.region_name)
    objDetection.objDetect(config.objectBucketName)
    objDetection.storeImage(config.bucketName)
    objDetection.modifyDataModel()
    
    return objDetection.getModel()
