import os 
import sys
import csv
import json
import heapq
import shutil
import random
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

CHUNK_SIZE=200

def infer_column_type(file_path, column_name):
    with open(file_path, newline='') as csvfile:
        reader = list(csv.DictReader(csvfile))

        if column_name not in reader[0].keys():
            print("Columnn is not Exist")
            return

    if len(reader) < 10:
        sample_rows = reader  # use all rows if < 10
    else:
        sample_rows = random.sample(reader, 10)

    type_counts = {"int": 0, "float": 0, "str": 0}
    missing_count = 0

    for row in sample_rows:
        value = row.get(column_name, "").strip()

        if value == "" or value.lower() in ("na", "null", "none"):
            missing_count += 1
            continue

        try:
            int(value)
            type_counts["int"] += 1
        except ValueError:
            try:
                float(value)
                type_counts["float"] += 1
            except ValueError:
                type_counts["str"] += 1

    # Choose the most frequent type
    if all(count == 0 for count in type_counts.values()):
        final_type = "unknown"
    else:
        final_type = max(type_counts, key=type_counts.get) # type: ignore

    return final_type

def process_chunk(filePath, col_index):
    log.info(f"processing chunking with chunk  size of: {CHUNK_SIZE}")
    
    temp_files = []

    with open(filePath, "r", newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = []
        chunk_counter = 0

        for row in reader:
            rows.append(row)
            if len(rows) >= CHUNK_SIZE:
                rows.sort(key=lambda x: x[col_index]) if COL_KY_DTYP == 'str' else rows.sort(key=lambda x: int(x[col_index])) 
                temp = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='', suffix='.csv')
                writer = csv.writer(temp)
                writer.writerow(headers)
                writer.writerows(rows)
                temp_files.append(temp.name)
                temp.close()
                rows = []
                log.info(f"processing done for chunk: {chunk_counter+1}")
                chunk_counter += 1
            

        if rows:  # handle last chunk
            rows.sort(key=lambda x: x[col_index]) if COL_KY_DTYP == 'str' else rows.sort(key=lambda x: int(x[col_index]))
            temp = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='', suffix='.csv')
            writer = csv.writer(temp)
            writer.writerow(headers)
            writer.writerows(rows)
            temp_files.append(temp.name)
            temp.close()
            log.info(f"processing done for chunk: {chunk_counter+1}")

    log.info(f"Chunking process done")
    return temp_files

def merge_chunks(temp_files, output_path, col_index, headers):
    log.info("Merging all chunked files...")

    # tempFile have list of temp dirs paths so below we are open all those files.
    file_handles = [open(f, "r", newline='', encoding='utf-8') for f in temp_files]
    readers = [csv.reader(fh) for fh in file_handles]

    for reader in readers:
        next(reader)

    def sort_key(row):
        return row[col_index] if COL_KY_DTYP == 'str' else int(row[col_index]) 

    with open(output_path, "w", newline='', encoding='utf-8') as out_file:
        writer = csv.writer(out_file)
        writer.writerow(headers)

        for row in heapq.merge(*readers, key=sort_key):
            writer.writerow(row)

    for fh in file_handles:
        fh.close()

def safelyReplaceFile(original_path, sorted_path, backup=True):
    log.info(f"Your have set backup option: {backup}")
    if backup:
        backup_path = os.path.join("backups", f"{os.path.basename(original_path)}.bck")
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

    extras = ['../data/csv/add_users.csv', '../data/csv/update_users.csv',  '../data/csv/disable_users.csv' ]
    for path in extras:
        try: 
            os.remove(path) if os.path.exists(path) else None
            log.info(f"existing file '{path}' removed")
        except Exception as e:
            log.error(f"Failed to delete temp file {path}: {e}")

#main for sort files
def sortFile(input_file, sort_key):
    global COL_KY_DTYP
    COL_KY_DTYP = infer_column_type(input_file, sort_key)
    try:
        log.info(f"Starting sorting on file: {input_file} by column: {sort_key}")

        # Step 1: Validate and get headers
        with open(input_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            if isinstance(sort_key, str):
                if sort_key not in headers:
                    log.error(f"Sort key '{sort_key}' not found in headers.")
                    sys.exit(1)
                col_index = headers.index(sort_key)
            elif isinstance(sort_key, int):
                if sort_key < 0 or sort_key >= len(headers):
                    log.error(f"Sort key index {sort_key} is out of range.")
                    sys.exit(1)
                col_index = sort_key
            else:
                log.error("Sort key must be a string (column name) or an integer (index).")
                sys.exit(1)
                
        os.makedirs("backups", exist_ok=True)

        # Step 2: Chunk → Sort → Write
        temp_files = process_chunk(input_file, col_index)

        # Step 3: Merge sorted chunks
        sorted_path = "sorted_file.csv"
        merge_chunks(temp_files, sorted_path, col_index, headers)

        # Step 4: Replace original file (with backup)
        
        safelyReplaceFile(input_file, sorted_path, backup=True)

        # Step 5: Cleanup
        cleanup(temp_files)

        log.info("Sorting completed successfully.")

    except Exception as e:
        log.exception(f"Unexpected error occurred: {e}")
        sys.exit(1)
# ────────────────────────────────────────────────────────────

def filterNewUsers(old_file, new_file, col_index):
    """ Filter New add users.
    - all IDs which is in the new csv file but to in onld csv file these entries are users.
    """
    with open(old_file, 'r', newline='') as oldf, open( new_file, 'r' , newline='') as newf:

        reader4oldf = csv.reader(oldf)
        reader4newf = csv.reader(newf)

        newf_headers = next(reader4newf)

        old_set = set()
        for rw in reader4oldf:
            old_set.add(rw[0].strip())

        new_users = []
        for row in reader4newf:
            if row[0].strip() not in old_set:
                new_users.append(row)

    # newUsersCsv = os.path.join("data","csv","new_users.csv")
    addUsersCsv = '../data/csv/add_users.csv'
    with open(addUsersCsv, "w", newline='', encoding='utf-8') as out:
        writer = csv.writer(out)
        writer.writerow(newf_headers)
        writer.writerows(new_users)
    log.info(f"NEW USER FILE HAS WRITTEN  at : {addUsersCsv}")
# ──────────────────────────────

def filterUpdatedUsers(olf_file, new_file):
    """ Filter users which have changes in data.
    - All modified user are filted. i.e. they dont have new entry but have changes
         in old column valu with compare to new column value.    
    """
    with open(olf_file, 'r', newline='') as ofile, open(new_file, 'r', newline='') as nfile:
        old_reader = csv.reader(ofile)
        new_reader = csv.reader(nfile)

        old_headers = next(old_reader)
        next(new_reader)

        old_ids = {rw[0].strip(): rw for rw in old_reader}
        updated_rows = []

        
        for rw in new_reader:
            ID = rw[0].strip()
            if ID in old_ids:
                full_row = old_ids[ID]

                for i, (old_val, new_val) in enumerate(zip(full_row[1:], rw[1:]), start=1):
                    if old_val != new_val:
                        col_name = old_headers[i]
                        log.info(f"User ID {ID} → Field changed: '{col_name}' | Old: '{old_val}' → New: '{new_val}'")
                        updated_rows.append(rw) if rw not in updated_rows else None

        updateUsersCsv = '../data/csv/update_users.csv'
        with open(updateUsersCsv, 'w', newline='') as updatefile:
            writer = csv.writer(updatefile)
            writer.writerow(old_headers)
            writer.writerows(updated_rows)
        log.info(f"Update user file has written at : {updateUsersCsv}")
# ──────────────────────────────

def filterDisableUsers(old_file, new_file):
    """Filter user which are common in both file. 
    the ids which are not in the old file but in the new file.
    """
    with open(old_file, 'r', newline='') as ofile, open(new_file, 'r', newline='') as nfile:
        old_reader = csv.reader(ofile)
        new_reader = csv.reader(nfile)

        old_headers = next(old_reader)
        next(new_reader)

        new_ids = set(rw[0].strip() for rw in new_reader)
        disable_users = [rw for rw in old_reader if rw[0].strip() not in new_ids]
        
    disableUsersCsv = '../data/csv/disable_users.csv'
    with open(disableUsersCsv, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(old_headers)
        writer.writerows(disable_users)
    log.info(f"Disable users file has created at {disableUsersCsv}")

# ──────────────────────────────

def main(oldFile, newFile):    
    # cheking validation
    is_valid = fileValidation(oldFile,newFile)
    log.info("file Validation Complete") if is_valid else sys.exit("Validation Failed")            

    # read csv files
    with open(oldFile, 'r', newline='') as f:
        reader = csv.reader(f)
        oldFileColHeaders = next(reader)
    with open(newFile, 'r') as f:
        reader = csv.reader(f)
        newFileColHeaders = next(reader)
    
    # cheking if both files have same headers
    has_valid_headers= headerValidation(oldFileColHeaders, newFileColHeaders)
    log.info("Header Validation Complete") if has_valid_headers else sys.exit("Header validation failed!!")    

    # sort file
    # input file and sort key.
    sort_key = "ID"
    sortFile(oldFile, sort_key)
    sortFile(newFile, sort_key)
    filterNewUsers(oldFile, newFile, "ID")
    filterUpdatedUsers(oldFile, newFile)
    filterDisableUsers(oldFile, newFile)
# ──────────────────────────────

if __name__ == "__main__":
    oldFile='../data/csv/oldFile.csv'
    newFile='../data/csv/newFile.csv'

    main(oldFile, newFile)