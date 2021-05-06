import config
from notification import ImageMessages, ValidationResultMessage, AlertNotify


def lambda_handler(event, context):
    dataModel = event
    
    # declare classes
    personImageMessages = ImageMessages(dataModel)
    validationResultMessage = ValidationResultMessage(dataModel)
    alertNotify = AlertNotify(personImageMessages, validationResultMessage)
    
    # send messages to receiver
    pushResult = alertNotify.pushMessages()
    
    print(pushResult)
    
    return pushResult