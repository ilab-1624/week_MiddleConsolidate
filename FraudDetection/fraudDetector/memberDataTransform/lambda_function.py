import boto3
import json
from member_model import Member
import config


def lambda_handler(event, context):
    member = Member(config.AWS_ACCESS_KEY,config.AWS_SECRET_KEY,config.recordBucket,config.recordFile,config.memberBucket,config.memberFile)
    member.memberDataTransform()
    outputModel = member.getModel()
    return outputModel