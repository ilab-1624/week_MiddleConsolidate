import json
from ppeDetection import PpeDetect
import config

def lambda_handler(event, context):
    # dataModel = json.loads(event)
    ppeDetection =  PpeDetect(dataModel, config.aws_access_key_id, config.aws_secret_access_key, config.region_name)
    ppeDetection.storeImage()
    ppeDetection.ppeDetect()
    ppeDetection.redshiftInject()
    
    return ppeDetection.getModel()
