import subprocess
import sys
import shutil
from pathlib import Path


def decryption(upload_dir_path: Path, archive_dir: Path, passphrase: str = None):
    """
        Args
            upload_dir_path: ../UPLOAD/ dir path of company which is being processing.
            archive_dir: archive dir path.
            passphrase: secret phrase need to decryption
    """
    pattern = f"*_complete.csv.pgp"
    for idx, _pgp_file in enumerate(upload_dir_path.glob(f"{pattern}")):
        filename = _pgp_file.name
        prefix = filename[:-17]

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
            gpg_decrypt_command.insert(1, "--passphrase-fd")
            gpg_decrypt_command.insert(2, "0")
            process_input = passphrase  # Pass the passphrase to stdin

        try:
            result = subprocess.run(
                gpg_decrypt_command,
                input=process_input,
                capture_output=True,
                text=True,
                check=True
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
                        print(f"An unexpected error occurred while moving '{file.name}': {e}")
            else:
                print("No .pgp files found in the UPLOAD directory for move to archive.")
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
        except FileNotFoundError:
            print("Error: 'gpg' command not found. Please ensure GPG is installed and in your system's PATH.")

def print_loop(upload_dir: Path, archive_dir: Path, company: str):
    """
    Args:
        upload_dir: ../UPLOAD/ dir path of company which is being processing.
        archive_dir: archive dir path.
        company: company name which is being processing.
    """

    print("--- THIS IS PRINT LOOP --- ")
    pattern = "*_complete"

    # looping over UPLOAD dir and matching pattern
    for inx, _file in enumerate(upload_dir.glob(f"{pattern}")):
        _filename = _file.name
        prefix = _filename[:-9]
        print(f"Filename: {_filename} \n Prefix: {prefix}")
        print(f"gpg --output {upload_dir}/{prefix}_{company}_users.csv /home/{company}/UPLOAD/{prefix}_users.csv")

        # touch {prefix}_{company}_complete
        _touch_file = upload_dir / f"{prefix}_{company}_complete"
        _touch_file.touch()  # exist = ok

        # mv {prefix}_users.csv archive
        _src_file = upload_dir / f"{prefix}_users.csv"
        try:
            shutil.move(_src_file, archive_dir)
        except Exception as e:
            print(f"Exception in moving file: {e}")

        # rm {prefix}_complete
        _rm_file = upload_dir / f"{prefix}_complete"
        shutil.rmtree(_rm_file) if _rm_file.exists() else print(f"{_rm_file} : This file is not exist.")

    print("--- PRINT LOOP END --- ")


def main(company: str, key: str, passphrase: str):
    upload_dir = Path(f"/home/{company}/UPLOAD")
    sys.exit(f"{upload_dir} : is not exist") if not upload_dir.exists() else print(
        f"Working for files inside-> {upload_dir} ")
    if not upload_dir.is_absolute():
        sys.exit("Upload dir path must be absolute")

    archive_dir = Path(f"/home/{company}/archive")
    sys.exit(f"{archive_dir} : is not exist") if not archive_dir.exists() else print(
        f"Archive Directory -> {archive_dir} ")
    if not archive_dir.is_absolute():
        sys.exit("archive dir path must be absolute")

    print_loop(upload_dir, archive_dir, company)
    decryption(upload_dir, archive_dir, company, passphrase)

# Use: Script_file [company_name] [secret_key] [passphrase]
# EX: python3 gpg.py  company_1 2DA3357A9453282A04A40EF0DE59FC65193FBCA3 init.001
# key: 2DA3357A9453282A04A40EF0DE59FC65193FBCA3 (this key is dumped)
# Passphrase init.1 (example)
if __name__ == "__main__":
    # checking args
    if len(sys.argv) < 4:
        print("Script has missing args")
        print("Use: Script_file [company_name] [secret_key] [passphrase]")
        sys.exit(1)

    # setting values form args
    company_name = sys.argv[1]
    secret_key = sys.argv[2]
    pass_phrase = sys.argv[3]

    main(company_name, secret_key, pass_phrase)