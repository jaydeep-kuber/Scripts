""" 
This is a somple script which use BOTO3 and send Error log message/file to AWS Simple Queue Service
"""

import os
import json
import boto3
import datetime
from dotenv import load_dotenv
from datetime import date

# getting valuse from .env
load_dotenv()

access_key = os.getenv("ACCESS_KEY")
secret_key = os.getenv("SECRET_KEY")
region = "ap-south-1"
sqs_url= os.getenv("SQS_URL_STD")

# client

sqs_client = boto3.client(
    'sqs',
    aws_access_key_id = access_key,
    aws_secret_access_key = secret_key,
    region_name = region
)

message = f"this is test message sent at: {datetime.datetime.now()}"

if sqs_client: 
    print("you have your client...")
    sent = sqs_client.send_message(QueueUrl=sqs_url, MessageBody=message)
    print("Message was sent to Q") if sent else print("something is wrong with message sending")
else:
    print("Something wrong!!")