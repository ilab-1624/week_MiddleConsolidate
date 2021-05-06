import config
from notification import ImageMessages, ValidationResultMessage, AlertNotify


def lambda_handler(event, context):
    dataModel = event
    
    if (dataModel['registrationResult']['personCount'] > 0):
        # declare classes
        memberImageMessages = ImageMessages(dataModel)
        validationResultMessage = ValidationResultMessage(dataModel)
        alertNotify = AlertNotify(memberImageMessages, validationResultMessage)
        
        # send messages to receiver
        pushResult = alertNotify.pushMessages()
    
    else:
        pushResult = 'Not push'
    
    print(pushResult)
    
    return pushResult