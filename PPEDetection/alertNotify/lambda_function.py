import json
from notification import SourceImageMessage, ValidationResultMessage, AlertNotify


def lambda_handler(event, context):
    dataModel = json.loads(event)
    
    if (dataModel['ppeDetection']['personCount'] > 0):
        # declare classes
        sourceImageMessage = SourceImageMessage(dataModel)
        validationResultMessage = ValidationResultMessage(dataModel)
        alertNotify = AlertNotify(sourceImageMessage, validationResultMessage)
        
        # send messages to receiver
        pushResult = alertNotify.pushMessages()
    
    else:
        pushResult = 'Not push'
    
    print(pushResult)
    
    return pushResult
