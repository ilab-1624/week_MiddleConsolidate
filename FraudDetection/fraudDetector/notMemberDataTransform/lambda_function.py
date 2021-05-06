import config
from dataTransform import NotMemberDataTransform

def lambda_handler(event, context):
    notMemberDataTransform = NotMemberDataTransform(event, config.aws_access_key_id, config.aws_secret_access_key)
    notMemberDataTransform.processData()
    return notMemberDataTransform.getModel()