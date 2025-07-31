import subprocess
import sys
import shutil
from pathlib import Path

def encryption(upload_dir_path: Path, prefix: str, _key: str):
    """
        Args:
            upload_dir_path: ../UPLOAD/ dir path of company which is being processing.
            prefix: prefix of file which is processing
            _key: secret key use for encryption.
    """

    filename = f"{prefix}_complete.csv.pgp"
    out_file = upload_dir_path / filename
    in_file = "/home/jay/work/scripts/AUP/Crypto/input-plain.txt"

    # Define the GPG encryption command
    gpg_encrypt_command = [
        "gpg",
        "--output", str(out_file),  # Output path
        "--encrypt",
        "--recipient", _key,
        str(in_file)  # Input plaintext file
    ]

    try:
        print(f"Executing GPG command: {' '.join(gpg_encrypt_command)}")
        subprocess.run(
            gpg_encrypt_command,
            capture_output=True,
            text=True,
            check=True  # Raise an exception for non-zero exit codes
        )
        print("GPG encryption successful.")
        return out_file

    except subprocess.CalledProcessError as e:
        print(f"GPG encryption failed error->: {e}")
        print(f"STDERR (if any):\n{e.stderr}")
        return None
    except FileNotFoundError:
        print("Error: 'gpg' command not found. Ensure GPG is installed and in your system's PATH.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during encryption: {e}")
        return None

if __name__ == "__main__":
    company = "company_1"
    _prefix = "20250731"  # need for encryption function.
    if len(sys.argv) > 1:
        key = sys.argv[1]
    upload_dir = Path(f"/home/jay/work/scripts/AUP/home/{company}/UPLOAD")
    if not key:
        sys.exit("Secret Key is needed... pass key in 1st arg")
    encryption(upload_dir, _prefix, key)
