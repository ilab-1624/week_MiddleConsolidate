from notification import ImageMessage, DetectResultMessage, AlertNotify


def lambda_handler(event, context):
    modelList = event
    
    for dataModel in modelList:
        dataModel['alertNotify'] = {}
        
        if (dataModel['fraudDetection']['alertMessage'] != ''):
            # declare classes
            imageMessage = ImageMessage(dataModel)
            detectResultMessage = DetectResultMessage(dataModel)
            alertNotify = AlertNotify(imageMessage, detectResultMessage)
            
            # send messages to receiver
            pushResult = alertNotify.pushMessages()
            
            # put alertNotify logs into dataModel
            dataModel['alertNotify']['linePushText'] = detectResultMessage.text
            dataModel['alertNotify']['linePushResult'] = pushResult
        
        else:
            pushResult = 'Not push'
            
            # put alertNotify logs into dataModel
            dataModel['alertNotify']['linePushText'] = ''
            dataModel['alertNotify']['linePushResult'] = pushResult
    
        print(pushResult)
    
    return modelList