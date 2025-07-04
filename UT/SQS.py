import os
import sys
import json
import boto3
import datetime
from dotenv import load_dotenv
from datetime import date

class SQS():
    
    def __init__(self) -> None:
        # getting valuse from .env
        load_dotenv()
        self.access_key = os.getenv("ACCESS_KEY")
        self.secret_key = os.getenv("SECRET_KEY")
        self.region = "ap-south-1"
        self.sqs_url= os.getenv("SQS_URL_STD") 
    
        def getClient(self):
            return boto3.client(
                    'sqs',
                    aws_access_key_id = os.getenv("ACCESS_KEY"),
                    aws_secret_access_key = os.getenv("SECRET_KEY"),
                    region_name = "ap-south-1"
            )

    def display(self):
         return self.sqs_url
    
    def sendMessage(self):
        pass

    def receiveMessage(self):
        pass

    def deleteMessage(self):
        pass

sqs = SQS()

print(sqs.display())