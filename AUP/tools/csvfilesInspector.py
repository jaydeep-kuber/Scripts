import os 
import sys
import csv

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
    
    return True

def headerValidation(oldFileHeaders, newFileHeaders):
    """
    Validate that:
    - Header lengths are equal
    - All headers match exactly (case-sensitive and index-sensitive)
    """
    if len(oldFileHeaders) != len(newFileHeaders):
        print(f"Header length mismatch:\nOld file: {len(oldFileHeaders)}\nNew file: {len(newFileHeaders)}\n")
        return False

    mismatches = []

    for i in range(len(oldFileHeaders)):
        if oldFileHeaders[i] != newFileHeaders[i]:
            mismatches.append((i, oldFileHeaders[i], newFileHeaders[i]))

    if mismatches:
        print("Header mismatches found:")
        for idx, old, new in mismatches:
            print(f"  Index {idx}: '{old}' != '{new}'")
        return False
    return True

def compare_csv(oldFile, newFile):
    
    # cheking validation
    is_valid = validation(oldFile,newFile)
    print(">>> file Validation Complete") if is_valid else sys.exit("Validation Failed")            

    # read csv files
    with open(oldFile, 'r', newline='') as f:
        reader = csv.reader(f)
        oldFileColHeaders = next(reader)
        oldData = [row for row in reader]
    with open(newFile, 'r') as f:
        reader = csv.reader(f)
        newFileColHeaders = next(reader)
        newData = [row for row in reader]
    
    # cheking if both files have same headers
    has_valid_headers= headerValidation(oldFileColHeaders, newFileColHeaders)
    print(">>> Header Validation Complete") if has_valid_headers else sys.exit("Header validation failed!!")

    # processing on csv data.
    """ need to check
    - number of rows are same
        - if not then
            - detect entire new row
            - detect rows which have changes in some columns along with index and colName
    - filter entire new rows and store it 
    - filter changes and store it
    - filter same rows and store it
    """ 
    # check if number of rows are same
    if len(oldData) != len(newData):
        print(">>> Number of rows are not same")
    else:
        print(">>> Number of rows are same")

def main():
    oldFile='../data/csv/oldFile.csv'
    newFile='../data/csv/newFile.csv'
    compare_csv(oldFile,newFile)

if __name__ == "__main__":
    main()