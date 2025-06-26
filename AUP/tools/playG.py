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
import csv
import json
import heapq
import shutil
import hashlib
import tempfile
import logging
import logging.config

from datetime import datetime

def setup_logging(config_path="logging.json"):
    """
    Load logging config from a JSON file and configure logging.
    Falls back to basicConfig if file not found.
    """
    # creaing log dir
    os.makedirs("logs", exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    log_file = f"logs/log_{date_str}.log"

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
            config["handlers"]["file"]["filename"] = log_file
        logging.config.dictConfig(config)
    else:
        # fallback
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_file)
                ]
            )
        logging.warning(f"No logging config found at {config_path}, using basicConfig.")
setup_logging()
fileName= os.path.basename(__file__)
log = logging.getLogger(fileName)

# ──────────────────────────────

def fileValidation(oldFile, newFile):
    log.info("File validation start...")

    #check is file is exist
    if not os.path.isfile(oldFile):
        log.info("Old file not found")
        return False
    if not os.path.isfile(newFile):
        log.info("New file not found")
        return False

    #check if file is empty
    if os.path.getsize(oldFile) == 0:
        log.info("Old file is empty")
        return False
    if os.path.getsize(newFile) == 0:
        log.info("New file is empty")
        return False

    #check if file is csv
    if not oldFile.endswith('.csv') or not newFile.endswith('.csv'):
        log.info("File is not csv")
        return False

    log.info("File validation end..")
    return True

def headerValidation(oldFileHeaders, newFileHeaders):
    """
    Validate that:
    - Header lengths are equal
    - All headers match exactly (case-sensitive and index-sensitive)
    """

    log.info("Header validation start...")

    if len(oldFileHeaders) != len(newFileHeaders):
        log.info(f"Header length mismatch:\nOld file: {len(oldFileHeaders)}\nNew file: {len(newFileHeaders)}\n")
        return False

    mismatches = []

    for i in range(len(oldFileHeaders)):
        if oldFileHeaders[i] != newFileHeaders[i]:
            mismatches.append((i, oldFileHeaders[i], newFileHeaders[i]))

    if mismatches:
        log.info("Header mismatches found:")
        for idx, old, new in mismatches:
            log.info(f"  Index {idx}: '{old}' != '{new}'")
        return False
    
    log.info("Header validation end...")
    return True


# ──────────────────────────────VALIDATE SORTED FILE──────────────────────────────

def validate_final_csv(input_file, output_file):
    """Validate that input and output have the same number of rows."""
    
    log.info("Validating number of rows in file after sorting...")

    input_rows = sum(1 for _ in open(input_file)) - 1  # Exclude header
    output_rows = sum(1 for _ in open(output_file)) - 1
    if input_rows != output_rows:
        raise ValueError(f"Data loss detected: Input has {input_rows} rows, output has {output_rows} rows")
    log.info(f"Validation passed: {input_rows} rows in both input and output")

def compute_checksum(file_path):
    """Compute MD5 checksum of a file for extra validation."""
    
    log.info("Computing checksum for validation, is file corrupted..")
    
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# ──────────────────────────────SORTING──────────────────────────────
""" 
    - Sort csv files based on the specified index
    - took index if it is in parameter else took the first column.
    - check type of index int or str and move accordingly.
"""

CHUNK_SIZE=10000
def process_chunk(filePath, colIndex):
    log.info(f"processing chunking with chunk  size of: {CHUNK_SIZE}")
    
    tmp_files = []
    temp_dir = tempfile.gettempdir()
    log.info(f"temp file directory: {temp_dir}")

    file_count = 0 # or any counter
    custom_name = f"chunk_{file_count}.csv"
    custom_path = os.path.join(temp_dir, custom_name)
    log.info(f"final file with path: {custom_path}")

    with open(filePath, 'r', newline='') as f:
        reader = csv.reader(f)
        headers = next(f)

        rows = []
        for rw in reader:
            rows.append(rw)
            if len(rows) >= CHUNK_SIZE:
                rows.sort(key=lambda x: x[colIndex])
                with open(custom_path, 'w', newline='') as tmp:
                    writer = csv.writer(tmp)
                    writer.writerow(headers)
                    writer.writerows(rows)
                tmp_files.append(custom_path)
                file_count += 1
                rows = []
                log.info(f"file {custom_name} sorted.")

        # sort the remainnig rows < chunk size
        if rows:
            rows.sort(key=lambda x: x[colIndex]) # lambda x: x[colIndex] col extractor
            with open(custom_path, 'w', newline='') as tmp:
                writer = csv.writer(tmp)
                writer.writerow(headers)
                writer.writerows(rows)
            tmp_files.append(custom_path)
            file_count += 1
            log.info(f"file {custom_name} sorted.")

    log.info(f"Chunking done. created {len(tmp_files)} number of temp files")
    return tmp_files

def merge_chunks(tempFiles, outFileLoc, colIndex, headers):
    log.info("Merging all chunked files...")

    # tempFile have list of temp dirs paths so below we are open all those files.
    file_handlers = [open(file, 'f', newline='') for file in tempFiles]
    readers = [csv.reader(fr) for fr in file_handlers]

    # skip headers of all files
    for reader in readers:
        next(reader)
    
    # Merge using heapq
    def sortKey(row):
        return row[colIndex]
    
    log.info(f"Merging out file location: {outFileLoc}")
    with open(outFileLoc, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(headers)

        for row in heapq.merge(*readers , key=sortKey):
            writer.writerow(row)

    for fh in file_handlers:
        fh.close()

def safelyReplaceFile(original_path, sorted_path, backup=True):
    log.info(f"Your have set backup option: {backup}")
    if backup:
        backup_path = original_path + ".bak"
        shutil.copy2(original_path, backup_path)
        log.info(f"backup done, file stored at: {backup_path}")
    shutil.move(sorted_path, original_path)
    log.info("New sorted file override.")


def cleanup(temp_files):
    for path in temp_files:
        try:
            os.remove(path)
        except Exception as e:
            log.error(f"Failed to delete temp file {path}: {e}")

#main
def sortFile(input_file, sort_key):
    setup_logging()

    try:
        # Step-1: Validate and get headers
        with open(input_file, 'r', newline='') as f:
            reader = csv.reader(f)
            headers = next(reader)
            if sort_key not in headers:
                log.error(f"Sort key '{sort_key}' not found in headers.")
                sys.exit(1)
            col_index = headers.index(sort_key)

        # Step 2: Chunk → Sort → Write
        temp_files = process_chunk(input_file, col_index)

        # Step 3: Merge sorted chunks
        sorted_path = "sorted_ildFile.csv"
        merge_chunks(temp_files, sorted_path, col_index, headers)

        # Step 4: Replace original file (with backup)
        safelyReplaceFile(input_file, sorted_path, backup=True)

        # Step 5: Cleanup
        cleanup(temp_files)
        log.info("Sorting completed successfully.")

    except:
        log.error("Error in main sort function.")
        sys.exit(1)
        
# ────────────────────────────────────────────────────────────

def filterNewUsers():
    pass

# ──────────────────────────────

def filterUpdatedUsers():
    pass

# ──────────────────────────────

def fltereDisableUsers():
    pass

# ──────────────────────────────

def compare_csv(oldFile, newFile):    
    # cheking validation
    is_valid = fileValidation(oldFile,newFile)
    log.info("file Validation Complete") if is_valid else sys.exit("Validation Failed")            

    # read csv files
    with open(oldFile, 'r', newline='') as f:
        reader = csv.reader(f)
        oldFileColHeaders = next(reader)
        oldFileData = [row for row in reader]
    with open(newFile, 'r') as f:
        reader = csv.reader(f)
        newFileColHeaders = next(reader)
        newFileData = [row for row in reader]
    
    # cheking if both files have same headers
    has_valid_headers= headerValidation(oldFileColHeaders, newFileColHeaders)
    log.info("Header Validation Complete") if has_valid_headers else sys.exit("Header validation failed!!")    

    # sort file
    # input file and sort key.
    sort_key = "id"
    sortFile(oldFile, sort_key)

# ──────────────────────────────

def main(oldFile,newFile):
    compare_csv(oldFile,newFile)


if __name__ == "__main__":
    oldFile='../data/csv/oldFile.csv'
    newFile='../data/csv/newFile.csv'

    if len(sys.argv) != 3:
        print("Usage: python csv_sorter.py <input_file.csv> <sort_column_name>")
        sys.exit(1)
    main(oldFile, newFile)