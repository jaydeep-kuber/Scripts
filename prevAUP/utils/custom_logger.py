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
from datetime import datetime

date_str = datetime.now().strftime('%Y.%m.%d')
logDirPath = './logs/'

def checkLogDirExists():
    """
    Check if the logs directory exists. If not, create it.
    """
    os.makedirs(logDirPath, exist_ok=True)
    return logDirPath

def createScriptLogDir(script_name):
    """
    Create a script-level log directory for today.
    E.g., logs/fwExpress.log.2025.05.08/
    """
    checkLogDirExists()
    dir_name = f"{script_name}.log.{date_str}"
    full_path = os.path.join(logDirPath, dir_name)
    os.makedirs(full_path, exist_ok=True)
    return full_path

def createCompanyLogFile(script_name, company):
    """
    Return the company-level log file path in the script-level log directory.
    File is created automatically when logger writes.
    """
    scriptLvlLogDir = createScriptLogDir(script_name)
    companyLvlLogFile = os.path.join(scriptLvlLogDir, f"{script_name}.log.{company}.{date_str}")
    return companyLvlLogFile

def setup_logger(script_name, company, level=logging.INFO):
    """ 
    Setup logger for company in script-level dir.
    Keeps your log format but simplifies file creation.
    """    
    companyLvlLogFile = createCompanyLogFile(script_name, company)

    logger = logging.getLogger(f"{script_name}_{company}")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.FileHandler(companyLvlLogFile, mode='a')  # append mode
        formatter = logging.Formatter(
            '[%(levelname)s][%(asctime)s][%(filename)s: %(lineno)d] - %(message)s',
            datefmt='%d/%m/%Y %H:%M'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger