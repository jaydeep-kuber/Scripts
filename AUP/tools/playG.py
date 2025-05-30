""" 
-> This is a TOOL. It used to find difference in two csv file at column level, column order level, row level and row value level.

@Prams:
    OldFile: Path of the old csv file
    NewFile: Path of the new csv file

What tool does?
-> Pre-tasks:
    - short the both files by id column.

Task - 1 : compare CSV at column header level
    -> Q: Are there any new columns in the new CSV that are not in the old CSV?
    Do: Report new column added, with filename, column name, position and value.
    
    -> Q: Are there any sequence changes in new CSV compare to old CSV?
    Do: Report the changes in sequence with old order and new order.

if no changes in columns move to check row level change.

Task - 2 :compare Id columns in both file if any new Id found in new file then save this entire row in new jsonFile with ID

Task - 3 : Comapre row by row with column value.
    -> like: 
        Row-1:
            is oldCol val == newCol val for each cols in a row.
            if change in a single column then add it in jsonFile. 

        jsonFile : key = rowIndex:colIndex and value = [{"col1":"val1", "col2":"val2", "col3":"val3"}]

"""

import os 
import sys

def validation(oldFile, newFile):
    #check is file is exist
    if not os.path.isfile(oldFile):
        print("Old file not found")
        return False
    if not os.path.isfile(newFile):
        print("New file not found")
        return False

    #check if file is empty
    if os.path.getsize(oldFile) == 0:
        print("Old file is empty")
        return False
    if os.path.getsize(newFile) == 0:
        print("New file is empty")
        return False

    #check if file is csv
    if not oldFile.endswith('.csv') or not newFile.endswith('.csv'):
        print("File is not csv")
    return False

def compare_csv(oldFile, newFile):
    
    # cheking validation
    is_valid = validation(oldFile,newFile)
    
    if is_valid:
        print("Validation Failed")
        sys.exit(1)            

    # read csv files
    with open(oldFile, 'r') as f:
        oldFileColHeaders = list(next(f).split(','))
        oldData = [row for row in f.readlines()]
    with open(newFile, 'r') as f:
        newData = [row for row in f.readlines()]

    print(oldFileColHeaders)

def main():
    oldFile='../data/csv/oldFile.csv'
    newFile='../data/csv/newFile.csv'
    compare_csv(oldFile,newFile)

if __name__ == "__main__":
    main()