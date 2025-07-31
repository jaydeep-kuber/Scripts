import os
from pathlib import Path

def cleanup_dump_dir(base_dir: str) -> None:
    """
    Deletes all files inside base_dir and its subdirectories, preserving directory structure.
    """
    base = Path(base_dir)

    if not base.exists() or not base.is_dir():
        raise ValueError(f"Provided path is not a valid directory: {base_dir}")

    deleted_files = 0

    for root, dirs, files in os.walk(base):
        for file in files:
            file_path = Path(root) / file
            try:
                file_path.unlink()
                deleted_files += 1
                print(f"🗑️ Deleted: {file_path}")
            except Exception as e:
                print(f"❌ Failed to delete {file_path}: {e}")

    print(f"\n✅ Cleanup complete. Total files deleted: {deleted_files}")

if __name__ == "__main__":
    cleanup_dump_dir("/home/jay/work/scripts/AUP/home")