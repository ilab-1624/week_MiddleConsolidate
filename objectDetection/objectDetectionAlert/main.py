import psycopg2
import boto3
from datetime import datetime
import json
import time
import Alert
import S3

def lambda_handler(event, context):
    dataModel = event
    alert = Alert.Alert(dataModel)
    s3 = S3.S3()

    resultList = []

    if dataModel["config"]["initObject"]:
        resultList.append(alert.backgroundObjectRegister())

    backgroundEvent = s3.readJson("backgroundEvent.json")
    lastNotificationTimestamp = s3.readJson("lastNotificationTimestamp.json")
    result = alert.cameraCoveredDetect(lastNotificationTimestamp,backgroundEvent)
    if result is not None:
        resultList.append(result)
    backgroundObjectList = s3.readJson("backgroundObjectList.json")

    result = alert.cameraMovedDetect(lastNotificationTimestamp, backgroundEvent, backgroundObjectList)
    if result is not None:
        resultList.append(result)

    result = alert.backgroundObjectLostDetect(backgroundObjectList, backgroundEvent)
    if result is not None:
        resultList.append(result)

    result = alert.abnormalObjectStayDetect(backgroundObjectList, backgroundEvent)
    if result is not None:
        resultList.append(result)

    dataModel["result"] = resultList

    return dataModel 
    
    


