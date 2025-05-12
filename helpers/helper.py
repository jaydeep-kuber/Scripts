import os

import os
import logging

def touchFile(dir_path, file_name, logger=None):
    """
    Ensures that the specified file exists in the given directory.
    If not present, it creates an empty file and logs the absolute path.
    
    Args:
        dir_path (str): The directory path.
        file_name (str): The file name.
        logger (logging.Logger): Optional logger to log actions.
        
    Returns:
        str: Absolute path of the file.
    """
    try:
        # Ensure the directory exists
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            if logger:
                logger.info(f"Directory created: {os.path.abspath(dir_path)}")
            else:
                print(f"Directory created: {os.path.abspath(dir_path)}")

        # Full file path
        file_path = os.path.join(dir_path, file_name)

        # Check if file exists
        if not os.path.isfile(file_path):
            # Create an empty file
            with open(file_path, 'w') as f:
                pass
            msg = f"File created: {os.path.abspath(file_path)}"
        else:
            msg = f"File already exists: {os.path.abspath(file_path)}"

        # Log or print the message
        if logger:
            logger.info(msg)
        else:
            print(msg)

        return os.path.abspath(file_path)

    except Exception as e:
        error_msg = f"Error ensuring file exists at {dir_path}/{file_name}: {str(e)}"
        if logger:
            logger.error(error_msg)
        else:
            print(error_msg)

def makeCSV(path, fileName):
    
    file = os.path.join(path, f'{fileName}.csv')

    if not os.path.exists(file):
        open(file, 'w').close()
        print(f"File [{fileName}] created successfully.")
    
    return file

def make_cmpFile(path, fileName):
    
    file = os.path.join(path, fileName)

    if not os.path.exists(file):
        open(file, 'w').close()
        print(f"File [{fileName}] created successfully.")
    
    return file

import random

def CSVfiller(master_path, target_path):
    """
    Write n random lines from master CSV to target CSV.
    
    Args:
    - master_path (str): Path to the master CSV.
    - target_path (str): Path where sampled lines will be written.
    - n (int): Number of lines to sample and write.

    Raises:
    - ValueError: If n is greater than total lines in master.
    """
    # genereate random number between 5 to 20
    number = random.randint(5, 30)
    # Read all lines from master
    with open(master_path, 'r') as master_file:
        lines = master_file.readlines()

    total_lines = len(lines)

    if number > total_lines:
        raise ValueError(f"Requested {number} lines, but master file has only {total_lines} lines.")

    # Pick n random lines (no replacement)
    sampled_lines = random.sample(lines, number)

    # Write sampled lines to target
    with open(target_path, 'w') as target_file:
        target_file.writelines(sampled_lines)

    print(f"{number} random lines written to {target_path}")


def makeCompleteFile(fileName, dirPath):
    file = f'{fileName}_complete'
    filePath = os.path.join(dirPath, file)

    # check if the directory exists
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)
        print(f'LOG: helper > makeCompleteFile: Directory {dirPath} created')
    else:
        print(f'LOG: helper > makeCompleteFile: Directory {dirPath} already exists')
    
    # check if the file exists
    if not os.path.exists(filePath):
        open(filePath, 'w').close()
        print(f'LOG: helper > makeCompleteFile: file {os.path.basename(filePath)} created at {filePath}')
    else:
        print(f'LOG: helper > makeCompleteFile: file {os.path.basename(filePath)} already exists at {filePath}')