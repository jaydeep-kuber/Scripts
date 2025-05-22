import os 
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the environment variables

# supported Companies
NUMBER_OF_COMPANIES = os.getenv('NUMBER_OF_COMPANIES')

COMPANY=os.getenv('COMPANY').split(',')
COMPANY_ID=os.getenv('COMPANY_ID').split(',')


# miscellaneous 

ALLEGO_HOME = os.getenv('ALLEGO_HOME')
SLEEP_INTERVAL = os.getenv('SLEEP_INTERVAL')
SOURCE_PARENT_DIR = os.getenv('SOURCE_P_DIR')
TARGET_PARENT_DIR  = os.getenv('TARGET_P_DIR')

# MYSQL_CMD = os.getenv('MYSQL_CMD')

# logs environment variables
LOG_DIR_PATH = os.getenv('LOG_DIR_PATH')
MYTHRESHOLD = os.getenv('myTHRESHOLD')

SMTP_USER = os.getenv('SMTP_USER')  
SMTP_PASS = os.getenv('SMTP_PASS')

# Print all environment variables
# print("NUMBER_OF_COMPANIES:", NUMBER_OF_COMPANIES)
# print("COMPANY:", COMPANY)
# print("COMPANY_ID:", COMPANY_ID)
# print("ALLEGO_HOME:", ALLEGO_HOME)
# print("SLEEP_INTERVAL:", SLEEP_INTERVAL)
# print("SOURCE_PARENT_DIR:", SOURCE_PARENT_DIR)
# print("TARGET_PARENT_DIR:", TARGET_PARENT_DIR)