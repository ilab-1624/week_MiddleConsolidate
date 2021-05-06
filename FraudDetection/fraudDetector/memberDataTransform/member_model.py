import boto3
from datetime import datetime
import time
import json
import os
import io
import config
import api


class Member:
    def __init__(dataModel,aws_access_key_id,aws_secret_access_key,recordBucket,recordFile,memberBucket,memberFile):
        self.__aws_access_key_id = aws_access_key_id
        self.__aws_secret_access_key = aws_secret_access_key
        self.__recordBucket = recordBucket
        self.__recordFile = recordFile
        self.__memberBucket = memberBucket
        self.__memberFile = memberFile
        self.__dataModel = dataModel

        self.__ouputModel = []

    def memberDataTransform(self):
        s3_client = boto3.client('s3', 
                    aws_access_key_id=self.__aws_access_key_id,
                    aws_secret_access_key=self.__aws_secret_access_key)
        # get Record
        staffRecord_obj = s3_client.get_object(Bucket = self.__recordBucket,
                                            Key = self.__recordFile)
        body = staffRecord_obj['Body']
        staffRecord = json.loads(body.read().decode('utf-8'))
        body.close()
        #get member list
        memberList_obj  = s3_client.get_object(Bucket = self.__memberBucket,
                                            self.__memberFile)
        memberListBody = memberList_obj['Body']
        memberList = json.loads(memberListBody.read().decode('utf-8'))['memberIdList']
        memberListBody.close()


        frame = {
        "frameId" : event['frameId'],
        "timestamp" : event['eventTimestamp'],
        "imageUrl" : event['imageUrl'],
        "site" : event['site']
        }

        #pharse rekognition Response
        eventList = []
        faceCount = len(event['searchFaceResponse'])
        for i in range(faceCount):
            if len(event['searchFaceResponse'][i]['FaceMatches'])>0:
                eventTimestamp = event['eventTimestamp']
                eventList.append([event['frameId'],eventTimestamp,event['searchFaceResponse'][i]['FaceMatches'][0]['Face']['ExternalImageId'],event['imageUrl'],event['site']])

        # find person if person not in image
        for member in memberList:
            flag = 0
            for i in eventList:
                if member in i:
                    flag = 1
                    print('yes')
            if flag ==1:
                continue
            if  member not in staffRecord:
                continue
            memberLastStatus = staffRecord[member]
            # site out不觸發此function
         if event['site'] == 'OUT':
                continue
            # member last Record In not trigger this function
            if memberLastStatus['site'] == 'IN':
                continue
            else:
                frame2 = {
                "frameId" :  memberLastStatus['frameId'],
                "timestamp" :memberLastStatus['eventTimestamp'],
                "imageUrl" : memberLastStatus['frameUrl'],
                "site" : memberLastStatus['site']
            }

                behaviorDetection = {
                "personId" : member,
                "inTime" : 0,
                "outTime" : memberLastStatus['eventTimestamp'],
                "isMember" :1,
                "stayTime" : memberLastStatus['eventTimestamp']- event['eventTimestamp'],
                "coordinate_x" : 0.0,
                "coordinate_y" : 0.0
            }

                fraudModel = {
                "frame" :[frame2],
                "behaviorDetection" : behaviorDetection}

                self.__outputModel.append(fraudModel)
        
        if len(eventList) !=0:

            for count in range(len(eventList)):
            
                eventProfile = {
                "frameId" : eventList[count][0],
                "eventTimestamp" : eventList[count][1],
                "name" : eventList[count][2],
                "frameUrl":eventList[count][3],
                "site" :eventList[count][4]
            }

                if eventProfile['name'] not in staffRecord:
                    staffRecord[eventProfile['name']] = eventProfile
                    s3_client.put_object(Body=str(json.dumps(staffRecord)),Bucket = self.__recordBucket,Key = self.__recordFile)
                    continue 
                recordProfile = staffRecord[eventProfile['name']]

                frame2 = {
                        "frameId" :  recordProfile['frameId'],
                        "timestamp" :recordProfile['eventTimestamp'],
                        "imageUrl" : recordProfile['frameUrl'],
                        "site" : recordProfile['site']
                    }
            

                if eventProfile['site'] == recordProfile['site']:
                #上次和這次依樣
                    print('same')
                    if eventProfile['site'] == 'IN':
                        pass
                    else:
                        staffRecord[eventProfile['name']] = eventProfile
                        s3_client.put_object(Body=str(json.dumps(staffRecord)),Bucket = self.__recordBucket,Key = self.__recordFile)
                
                else:
                    if eventProfile['site'] == 'IN':
                        # last Time  is "OUT"
                        # stay Time = in -out
                        #[frame,frame2] = [IN,OUT]
                        behaviorDetection = {
                        "personId" : eventProfile['name'],
                        "inTime" : eventProfile['eventTimestamp'],
                        "outTime" : recordProfile['eventTimestamp'],
                        "isMember" :1,
                        "stayTime" : recordProfile['eventTimestamp'] - eventProfile['eventTimestamp'],
                        "coordinate_x" : 0.0,
                        "coordinate_y" : 0.0
                        }

                        fraudModel = {
                        "frame" :[frame,frame2],
                        "behaviorDetection" : behaviorDetection
                        }
                        staffRecord[eventProfile['name']] = eventProfile
                        s3_client.put_object(Body=str(json.dumps(staffRecord)),Bucket = self.__recordBucket,Key = self.__recordFile)
                        self.__outputModel.append(fraudModel)
                    else:
                        # last Time is "IN"
                        # stay Time = out - in 
                        #[frame,frame2] = [OUT,IN]
                        behaviorDetection = {
                        "personId" : eventProfile['name'],
                        "inTime" : recordProfile['eventTimestamp'],
                        "outTime" : eventProfile['eventTimestamp'],
                        "isMember" :1,
                        "stayTime" : eventProfile['eventTimestamp']-recordProfile['eventTimestamp'],
                        "coordinate_x" : 0.0,
                        "coordinate_y" : 0.0
                        }
                        fraudModel = {
                        "frame" :[frame,frame2],
                        "behaviorDetection" : behaviorDetection
                        }
                        staffRecord[eventProfile['name']] = eventProfile
                        s3_client.put_object(Body=str(json.dumps(staffRecord)),Bucket = self.__recordBucket,Key = self.__recordFile)
                        self.__outputModel.append(fraudModel)
    def getModel(self):
        return self.__outputModel










