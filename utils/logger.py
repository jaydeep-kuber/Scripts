""" 
logs
  |
  |--/filewatcher.log.<current_date>
      |--/filewatcher.log.<Company1>.<current_date>
      |--/filewatcher.log.<Company2>.<current_date>

format: [LEVEL][DD/MM/YYYY HH][FILE: Line Number] - [Message]
    format='[%(levelname)s][%(asctime)s][%(filename)s: %(lineno)d] - %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S'
"""

""" 
-- What i want;
-- 1. Create a `logs` directory only one in project if it exist then use it and skip creating.
-- 2. Create a '<pythonScript_name>.log.<current_date>' directory in the `logs` directory if it exist then use it and skip creating.
        this dir will create one for each day. this dir contains company level log files.
-- 3. Create company log file for each company in the `<pythonScript_name>.log.<current_date>` directory.
        this log file will be created for each company. the name of the log file will be `<pythonScript_name>.log.<compan>.<current_date>`.
        only one log file will be created for each company.
"""

import os
import logging
import utils.env_conf as env_conf
from datetime import datetime

date_str = datetime.now().strftime('%d.%m.%Y')
logDirPath = env_conf.LOG_DIR_PATH

def checkLogDirExists():
    """
    Check if the logs directory exists. If not, create it.
    """
    if not os.path.exists(logDirPath):
        os.makedirs(logDirPath)
    else:
        pass # Directory already exists, no need to create it again
    return logDirPath

def createScriptLogDir(script_name):
    """
    Create a script-level log directory for today.
    """
    # check if the parent logs directory exists if not create it
    checkLogDirExists()
    dir_name = f"{script_name}.log.{date_str}"
    full_path = os.path.join(logDirPath, dir_name)
    
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    else:
        pass # Directory already exists, no need to create it again
    return full_path

def createCompanyLogFile(script_name, company):
    """
    Create a company-level log file in the script-level log directory.
    """
    # check if the script level directory exists if not create it
    scriptLvlLogDir = createScriptLogDir(script_name)
    # company level log file: ./logs/test3.log.30.04.2025/test3.log.<company>.<current_date>
    companyLvlLogFile = os.path.join(scriptLvlLogDir, f"{script_name}.log.{company}.{date_str}")
    
    if not os.path.exists(companyLvlLogFile):
        open(companyLvlLogFile, 'w').close()  # Create an empty file
    else:
        pass # File already exists, no need to create it again
    return companyLvlLogFile


def setup_logger(script_name, company):
    """ 
    this is the main function to setup the logger 
    """    

    # check if the script level directory exists if not create it
    scriptLvlLogDir = createScriptLogDir(script_name)
    
    # check if the company level log file exists if not create it
    companyLvlLogFile = createCompanyLogFile(script_name, company)

    # create a logger
    logger = logging.getLogger(company)
    logger.setLevel(logging.DEBUG) 

    if not logger.handlers:
       handler = logging.FileHandler(companyLvlLogFile)
       formatter = logging.Formatter(
           '[%(levelname)s][%(asctime)s][%(filename)s: %(lineno)d] - %(message)s',
           datefmt='%d/%m/%Y %H:%M'
        )
       handler.setFormatter(formatter)
       logger.addHandler(handler)

    return logger