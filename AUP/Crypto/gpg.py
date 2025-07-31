import subprocess
import sys
import shutil
from pathlib import Path

def encryption(upload_dir_path: str ,prefix: str, key: str):
    upload_dir_path = Path(upload_dir_path)
    if not upload_dir_path.is_absolute():
        sys.exit("Upload dir path must be absolute")

    filename = f"{prefix}_complete.csv.pgp"
    out_file = upload_dir_path / filename
    in_file = "/home/jay/work/scripts/AUP/Crypto/input-plain.txt"

    # Define the GPG encryption command
    gpg_encrypt_command = [
        "gpg",
        "--output", str(out_file),  # Output path
        "--encrypt",
        "--recipient", key,
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

def decryption(upload_dir_path: str , company: str, passphrase: str = None):
    """
        @prams
        in_file: input file absolute path for gpg command
        out_file: output file absolute path for gpg command
        key: the secret key which needed to decrypt, it is mandatory
    """

    upload_dir_path = Path(upload_dir_path)
    if not upload_dir_path.is_absolute():
        sys.exit("Upload dir path must be absolute")

    archive_dir = Path(f'/home/jay/work/scripts/AUP/home/{company}/archive')
    # key = key if key else sys.exit("Key arg is missing, Please provide key for decryption.")
    archive_dir.mkdir(parents=True, exist_ok=True) if not archive_dir.exists() else print("Archive dir exist")

    for idx, _pgp_file in enumerate(upload_dir_path.glob("*_complete.csv.pgp")):
        filename = _pgp_file.name
        prefix = filename[:-17]
        # prefix = "20250730"

        out_file = upload_dir_path / f"{prefix}_user.csv"
        in_file = upload_dir_path / f"{prefix}_users.csv.pgp"

        gpg_decrypt_command = [
            "gpg", "--output", out_file,
            "--decrypt",
            "--batch",
            "--no-tty",
            in_file
        ]

        # Handle passphrase input
        process_input = None
        if passphrase:
            # Add --passphrase-fd 0 to read passphrase from stdin
            gpg_decrypt_command.insert(1, "--passphrase-fd")
            gpg_decrypt_command.insert(2, "0")
            process_input = passphrase  # Pass the passphrase to stdin

        try:
            result = subprocess.run(
                gpg_decrypt_command,
                input=process_input,
                capture_output = True,
                text = True,
                check = True
            )
            print(f"Command executed successfully")

            # touch
            _cmp_file = upload_dir_path / f"{prefix}_complete"
            _cmp_file.touch()

            # mv *.pgp
            pgp_files = list(upload_dir_path.glob("*.pgp"))
            if pgp_files:
                for file in pgp_files:
                    try:
                        shutil.move(file, archive_dir)
                    except shutil.Error as e:
                        print(f"Error moving '{file.name}': {e}")
                    except Exception as e:
                        # Catch any other unexpected errors during move
                        print(f"An unexpected error occurred while moving '{file.name}': {e}")
            else:
                print("No .pgp files found in the UPLOAD directory for move to archive.")
            return  result
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            return None  # Indicate failure
        except FileNotFoundError:
            print("Error: 'gpg' command not found. Please ensure GPG is installed and in your system's PATH.")
    return None

def main(company: str, key: str, passphrase: str):
        _prefix = "20250730"
        passphrase = passphrase if passphrase else None
        upload_dir = f"/home/jay/work/scripts/AUP/home/{company}/UPLOAD"
        print(f"UPLOAD dir: {upload_dir}")

        encryption(upload_dir,_prefix, key)
        dec = int(input("Do want to go for decryption? [0/1] :"))
        decryption(upload_dir, company, passphrase) if dec == 1 else print(f"Done till encryption. not moving further as you provide flag: {dec}")

# Use: Script_file [company_name] [secret_key] [passphrase]
# EX:
# key: this key is only for my laptop
# 2DA3357A9453282A04A40EF0DE59FC65193FBCA3
# Passphrase init.001
if __name__ == "__main__":
    # checking args
    if len(sys.argv) < 4:
        print("Script has missing args")
        print("Use: Script_file [company_name] [secret_key] [passphrase]")
        sys.exit(1)
    company_name = sys.argv[1]
    secret_key = sys.argv[2]
    pass_phrase = sys.argv[3]

    if not company_name or secret_key or pass_phrase:
        print(company_name,secret_key, pass_phrase)
    main(company_name, secret_key, pass_phrase)