import boto3
from dotenv import load_dotenv
import os

# consts 
env_file = '.env.dev'
load_dotenv(env_file)
region = os.environ.get('REGION')
keyPair = os.environ.get('KEY_PAIR_NAME')
if not region or not keyPair:
    raise ValueError("REGION and KEY_PAIR_NAME must be set in the environment variables")
img_id = 'ami-0c55b159cbfafe1f0'  # Amazon Linux 2 AMI (HVM), SSD Volume Type

# getting the ec2 client
EC2_client = boto3.client('ec2')

# launching an instance
def launch_instance():
    try:
        response = EC2_client.run_instances(
            ImageId = img_id,
        )
    except Exception as e:
        print(f"Error launching instance: {e}")
        return None
