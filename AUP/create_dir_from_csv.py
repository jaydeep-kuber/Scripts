import csv
import os
from pathlib import Path
import tempfile
import sys


def create_structure_from_csv(csv_path: Path, base_dir: Path):
    """
    Generates a directory and file structure based on a CSV file.

    The CSV file must contain two columns: 'filename' and 'absolute_filepath'.
    This function will recreate the structure specified by 'absolute_filepath'
    inside the 'base_dir', creating empty files for each entry.

    Args:
        csv_path (Path): The path to the input CSV file.
        base_dir (Path): The root directory where the structure will be created.

    Raises:
        FileNotFoundError: If the csv_path does not exist.
        ValueError: If the CSV format is incorrect or paths are invalid.
        IOError: For other file system-related errors.
    """
    print(f"--- Starting Directory Structure Generation ---")
    print(f"Reading from: {csv_path}")
    print(f"Outputting to: {base_dir}\n")

    # --- 1. Initial Validation ---
    try:
        if not csv_path.is_file():
            raise FileNotFoundError(f"Error: The CSV file was not found at '{csv_path}'")

        # Ensure the base directory exists.
        # The exist_ok=True argument prevents an error if the directory already exists.
        base_dir.mkdir(parents=True, exist_ok=True)

    except (IOError, OSError) as e:
        # Catch potential permission errors or other OS-level issues
        print(f"Error creating base directory '{base_dir}': {e}", file=sys.stderr)
        return

    # --- 2. Process the CSV file ---
    try:
        with open(csv_path, mode='r', encoding='utf-8') as infile:
            # Use DictReader to easily access columns by name
            reader = csv.DictReader(infile)

            # Check for required headers
            required_headers = {'filename', 'absolute_filepath'}
            if not required_headers.issubset(reader.fieldnames):
                raise ValueError(
                    f"CSV file is missing required headers. "
                    f"Found: {reader.fieldnames}, Required: {required_headers}"
                )

            for i, row in enumerate(reader, start=2):  # Start from 2 for 1-based line number
                filename = row.get('filename', '').strip()
                absolute_filepath_str = row.get('absolute_filepath', '').strip()

                # --- 3. Per-Row Validation ---
                if not filename or not absolute_filepath_str:
                    print(f"Warning: Skipping row {i} due to missing 'filename' or 'absolute_filepath'.")
                    continue

                # Sanitize path string for consistency (replace backslashes)
                absolute_filepath_str = absolute_filepath_str.replace('\\', '/')

                # Create a Path object for robust handling
                absolute_filepath = Path(absolute_filepath_str)

                # Validate that the path is absolute
                if not absolute_filepath.is_absolute():
                    print(
                        f"Warning: Skipping row {i}. "
                        f"Path '{absolute_filepath_str}' is not an absolute path."
                    )
                    continue

                # Validate that the filename in the path matches the filename column
                if absolute_filepath.name != filename:
                    print(
                        f"Warning: Skipping row {i}. Mismatch between filename column "
                        f"('{filename}') and filename in path ('{absolute_filepath.name}')."
                    )
                    continue

                # --- 4. Create Directory and File ---
                try:
                    # We need to strip the root/anchor of the absolute path to make it relative.
                    # e.g., /home/user/doc.txt -> home/user/doc.txt
                    # e.g., C:/Users/user/doc.txt -> Users/user/doc.txt
                    relative_path = absolute_filepath.relative_to(absolute_filepath.anchor)

                    # Construct the final destination path inside our base directory
                    destination_path = base_dir / relative_path

                    # Create all necessary parent directories
                    destination_path.parent.mkdir(parents=True, exist_ok=True)

                    # Create the empty file
                    print(f"Creating: {destination_path}")
                    destination_path.touch()

                except (IOError, OSError) as e:
                    print(f"Error creating file or directory for row {i}: {e}", file=sys.stderr)
                    # Continue to the next row
                    continue

    except FileNotFoundError:
        # This is redundant due to the initial check, but good for safety
        print(f"Error: The CSV file was not found at '{csv_path}'", file=sys.stderr)
    except ValueError as e:
        print(f"Error processing CSV file: {e}", file=sys.stderr)
    except Exception as e:
        # Catch any other unexpected errors during CSV processing
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
    finally:
        print("\n--- Generation Process Finished ---")


def main():
    """
    Main function to demonstrate the script's usage.
    It creates a temporary CSV file and a temporary output directory,
    then runs the generation process.
    """
    # Create a temporary directory to work in
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        # Define paths for our dummy CSV and the output directory
        dummy_csv_path = temp_dir / "source_data.csv"
        output_base_dir = temp_dir / "generated_structure"

        # --- Create a dummy CSV file for demonstration ---
        csv_data = [
            ['filename', 'absolute_filepath'],
            ['report.docx', '/home/user/documents/reports/report.docx'],
            ['data.csv', '/home/user/data/raw/data.csv'],
            ['main.py', '/app/src/main.py'],
            ['photo.jpg', 'C:\\Users\\Alice\\Pictures\\vacation\\photo.jpg'],  # Windows path
            ['invalid.txt', 'relative/path/is/invalid.txt'],  # Invalid relative path
            ['mismatch.log', '/var/log/correct.log'],  # Mismatched filename
            ['', '/this/row/is/skipped.txt'],  # Missing filename
            ['config.json', '/etc/app/config.json'],
        ]

        with open(dummy_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)

        print("--- Created dummy CSV file for demonstration ---")
        print(dummy_csv_path.read_text())

        # --- Run the main function ---
        create_structure_from_csv(csv_path=dummy_csv_path, base_dir=output_base_dir)

        # --- Verify the output (optional) ---
        print("\n--- Verifying created structure: ---")
        if output_base_dir.exists():
            # Use a recursive generator to walk the directory tree
            paths = sorted(output_base_dir.rglob('*'))
            for path in paths:
                # Print path relative to the output base for clarity
                print(path.relative_to(output_base_dir))
        else:
            print("Output directory was not created.")


if __name__ == "__main__":
    main()
