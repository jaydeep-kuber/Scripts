import csv
import heapq
import os
import sys
import json
import logging
import logging.config
import tempfile
import shutil
from datetime import datetime
import random

CHUNK_SIZE = 200  # You can tune this
# CUL_KY_DTYP = None
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
    # return {
    #     "column": column_name,
    #     "sample_size": len(sample_rows),
    #     "inferred_type": final_type,
    #     "missing_values": missing_count,
    # }

# ─────────────────────────────────────
def setup_logging(config_path='logging.json'):
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

# ─────────────────────────────────────
def process_chunks(file_path, col_index):
    temp_files = []

    with open(file_path, "r", newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = []

        for row in reader:
            rows.append(row)
            if len(rows) >= CHUNK_SIZE:
                rows.sort(key=lambda x: x[col_index]) if CUL_KY_DTYP == 'str' else rows.sort(key=lambda x: int(x[col_index])) 
                temp = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='', suffix='.csv')
                writer = csv.writer(temp)
                writer.writerow(headers)
                writer.writerows(rows)
                temp_files.append(temp.name)
                temp.close()
                rows = []

        if rows:  # handle last chunk
            rows.sort(key=lambda x: x[col_index]) if CUL_KY_DTYP == 'str' else rows.sort(key=lambda x: int(x[col_index]))
            temp = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='', suffix='.csv')
            writer = csv.writer(temp)
            writer.writerow(headers)
            writer.writerows(rows)
            temp_files.append(temp.name)
            temp.close()

    return temp_files

# ─────────────────────────────────────
def merge_chunks(temp_files, output_path, col_index, headers):
    file_handles = [open(f, "r", newline='', encoding='utf-8') for f in temp_files]
    readers = [csv.reader(fh) for fh in file_handles]

    for reader in readers:
        next(reader)

    def sort_key(row):
        return row[col_index] if CUL_KY_DTYP == 'str' else int(row[col_index]) 

    with open(output_path, "w", newline='', encoding='utf-8') as out_file:
        writer = csv.writer(out_file)
        writer.writerow(headers)

        for row in heapq.merge(*readers, key=sort_key):
            writer.writerow(row)

    for fh in file_handles:
        fh.close()

# ─────────────────────────────────────
def safely_replace_file(original_path, sorted_path, backup=True):
    if backup:
        backup_path = original_path + ".bak"
        shutil.copy2(original_path, backup_path)
    shutil.move(sorted_path, original_path)

# ─────────────────────────────────────
def cleanup_temp_files(temp_files):
    for path in temp_files:
        try:
            os.remove(path)
        except Exception as e:
            print(f"Failed to delete temp file {path}: {e}")


# ─────────────────────────────────────
def main(input_file, sort_key):
    setup_logging()
    logger = logging.getLogger("main")

    global CUL_KY_DTYP
    CUL_KY_DTYP = infer_column_type(input_file, sort_key)
    print(CUL_KY_DTYP)
    try:
        logger.info(f"Starting sorting on file: {input_file} by column: {sort_key}")

        # Step 1: Validate and get headers
        with open(input_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            if isinstance(sort_key, str):
                if sort_key not in headers:
                    logger.error(f"Sort key '{sort_key}' not found in headers.")
                    sys.exit(1)
                col_index = headers.index(sort_key)
            elif isinstance(sort_key, int):
                if sort_key < 0 or sort_key >= len(headers):
                    logger.error(f"Sort key index {sort_key} is out of range.")
                    sys.exit(1)
                col_index = sort_key
            else:
                logger.error("Sort key must be a string (column name) or an integer (index).")
                sys.exit(1)
                
        # Step 2: Chunk → Sort → Write
        temp_files = process_chunks(input_file, col_index)

        # Step 3: Merge sorted chunks
        sorted_path = "sorted_output.csv"
        merge_chunks(temp_files, sorted_path, col_index, headers)

        # Step 4: Replace original file (with backup)
        safely_replace_file(input_file, sorted_path, backup=True)

        # Step 5: Cleanup
        cleanup_temp_files(temp_files)

        logger.info("Sorting completed successfully.")

    except Exception as e:
        logger.exception(f"Unexpected error occurred: {e}")
        sys.exit(1)

# ─────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python csv_sorter.py <input_file.csv> <sort_column_name>")
        sys.exit(1)

    input_file = sys.argv[1]
    sort_key = sys.argv[2]
    main(input_file, sort_key)