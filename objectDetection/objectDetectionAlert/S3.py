import boto3
import json
import awsConfig
import base64

class S3:
    def __init__(self):
        self.__S3Region = awsConfig.S3Region
        self.__bucketName = awsConfig.bucketName
        self.__aws_access_key_id = awsConfig.aws_access_key_id
        self.__aws_secret_access_key = awsConfig.aws_secret_access_key
        self.__s3_client = boto3.client('s3', aws_access_key_id=self.__aws_access_key_id, aws_secret_access_key=self.__aws_secret_access_key,region_name=self.__S3Region)

    def storeJson(self, key, body):
        response = self.__s3_client.put_object(Bucket= self.__bucketName , Key= key , Body=json.dumps(body),ACL='public-read',ContentType = 'text/json')
        
        return response  

    def readJson(self,key):
        obj = self.__s3_client.get_object(Bucket = self.__bucketName,Key = key)
        readString = obj["Body"]
        readString_utf8 = readString.read().decode('utf-8')
        readDict = json.loads(readString_utf8)
        
        return readDict

    def storeImage(self,key, base64string):
        image = base64.b64decode(base64string)
        self.__s3_client.put_object(ACL='public-read',Body=image, Bucket=self.__bucketName, Key=key ,ContentEncoding='base64',ContentType='image/jpeg')
        imageUrl = 'https://' + self.__bucketName + '.s3-' + self.__S3Region + '.amazonaws.com/' + key 
        
        return imageUrl
