import json 
import boto3
from datetime import datetime

def lambda_handler(event, context):

    client = boto3.client('frauddetector',
                            aws_access_key_id = config.aws_access_key_id,
                            aws_secret_access_key = config.aws_secret_access_key,
                            region_name = config.region_name)
    # emptyDict = {}
    s3_client = boto3.client('s3', 
                    aws_access_key_id=config.aws_access_key_id,
                    aws_secret_access_key=config.aws_secret_access_key)
    json_obj = s3_client.get_object(Bucket = config.s3Bucket,Key = config.memberFile)
    body = json_obj['Body']
    json_string = body.read().decode('utf-8')
    staffRecord = json.loads(json_string)
    body.close()
    
    obj = s3_client.get_object(Bucket = config.s3bucket,Key = config.notmemberFile)
    readString = obj["Body"]
    readString_utf8 = readString.read().decode('utf-8')
    notMemberRecord = json.loads(readString_utf8)
    readString.close()
    # emptyDict = {}
    
    dataModel = []
    for memberOutput in event['ParallelResultPath']:
      for person in memberOutput:
        eventTimestamp = event['eventTimestamp']
        eventTimestamp = datetime.fromtimestamp(eventTimestamp)
        eventTimestampString = eventTimestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        stayTime = person['behaviorDetection']['stayTime']

        eventData = {
          "stay_time" : str(person["behaviorDetection"]['stayTime']),
          "is_member": str(person["behaviorDetection"]["isMember"])
        }
        
        
        fraudDetectorResponse = client.get_event_prediction(detectorId=config.fraudDetectorId, 
                      detectorVersionId=config.fraudDetectorVersion,
                      eventId = '',
                      eventTypeName = config.fraudDetectorEventType, 
                      eventTimestamp = eventTimestampString,
                      entities = [{'entityType':config.fraduDetectorEntityType, 'entityId':config.fraudDetectorEntityId}],
                      eventVariables=  eventData)
        fraudDetector = {
          "isFraud" : fraudDetectorResponse['ruleResults'][0]['outcomes'][0] == 'fraud',
          "modelScore" : fraudDetectorResponse['modelScores'][0]['scores'],
          "alertMessage" : ""
        }
        person['fraudDetection'] = fraudDetector
        print(fraudDetector)
        if fraudDetector["isFraud"]==True and person["behaviorDetection"]["isMember"]==1:
          person['fraudDetection']['alertMessage'] = "成員離崗逾時"
          if person['behaviorDetection']['personId'] in staffRecord:
            if 'alert' in  staffRecord[person['behaviorDetection']['personId']]:
              if event['eventTimestamp'] -  staffRecord[person['behaviorDetection']['personId']]['alert']  >30:
                staffRecord[person['behaviorDetection']['personId']]['alert'] = event['eventTimestamp']
                s3_client.put_object(Body=json.dumps(staffRecord),Bucket = "fraud-detector-member-storage",Key = "staffRecord.json")
                #dataModel.append(person)
              else :
                if len(person['frame'])>1:
                  dataModel.append(person)
                continue
            if 'alert' not in   staffRecord[person['behaviorDetection']['personId']]:
              staffRecord[person['behaviorDetection']['personId']]['alert'] = event['eventTimestamp']
              
              s3_client.put_object(Body=str(json.dumps(staffRecord)),Bucket ="fraud-detector-member-storage",Key = "staffRecord.json")
              #dataModel.append(person)
        #   else:
            #dataModel.append(person)
              
            
        elif fraudDetector["isFraud"]==True and person["behaviorDetection"]["isMember"]==0 and person["behaviorDetection"]["crossLine"] == 0:
            if person["behaviorDetection"]["personId"] in notMemberRecord.keys():
                if person["frame"][0]["timestamp"] - notMemberRecord[person["behaviorDetection"]["personId"]] >20:
                    #dataModel.append(person)
                    person["fraudDetection"]["alertMessage"] = "非成員滯留逾時"
                    notMemberRecord[person["behaviorDetection"]["personId"]] = person["frame"][0]["timestamp"]
                    s3_client.put_object(Bucket="fraud-detector-member-storage", Key="notMemberRecord.json", Body=json.dumps(notMemberRecord),ACL='public-read',ContentType = 'text/json')
            else:
                notMemberRecord[person["behaviorDetection"]["personId"]] = person["frame"][0]["timestamp"]
                #dataModel.append(person)
                person["fraudDetection"]["alertMessage"] = "非成員滯留逾時"
                s3_client.put_object(Bucket="fraud-detector-member-storage", Key="notMemberRecord.json", Body=json.dumps(notMemberRecord),ACL='public-read',ContentType = 'text/json')
            
        elif person["behaviorDetection"]["isMember"]==0 and person["behaviorDetection"]["crossLine"] == 1:
            person["fraudDetection"]["alertMessage"] = "非成員左線逾界"
            #dataModel.append(person)
        elif person["behaviorDetection"]["isMember"]==0 and person["behaviorDetection"]["crossLine"] == 2:
            person["fraudDetection"]["alertMessage"] = "非成員右線逾界"
            #dataModel.append(person)
        dataModel.append(person)
    

    return dataModel