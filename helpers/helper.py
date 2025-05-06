import os

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
