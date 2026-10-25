import os
import shutil
import zipfile
import time
from datetime import datetime

SOURCE_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
DESKTOP_DIR = r"C:\Users\power\Desktop"
BACKUP_FOLDER = os.path.join(DESKTOP_DIR, "SMC_V17_COMPLETE_BACKUP")
ZIP_DESKTOP = os.path.join(DESKTOP_DIR, "SMC_V17_COMPLETE_BACKUP.zip")
ZIP_TIMESTAMPED = os.path.join(DESKTOP_DIR, f"SMC_V17_BACKUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
ZIP_LOCAL = os.path.join(SOURCE_DIR, "smc_v17_latest_full_backup.zip")

EXCLUDE_DIRS = {"__pycache__", ".git"}
EXCLUDE_FILES = {".DS_Store"}

def make_backup():
    print(f"Starting complete backup of: {SOURCE_DIR}")
    
    # 1. Update Desktop Folder
    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    
    file_count = 0
    total_bytes = 0
    
    for root, dirs, files in os.walk(SOURCE_DIR):
        # Exclude directories in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        rel_path = os.path.relpath(root, SOURCE_DIR)
        target_root = BACKUP_FOLDER if rel_path == "." else os.path.join(BACKUP_FOLDER, rel_path)
        os.makedirs(target_root, exist_ok=True)
        
        for file in files:
            if file in EXCLUDE_FILES or file.endswith(".tmp"):
                continue
            src_file = os.path.join(root, file)
            dst_file = os.path.join(target_root, file)
            shutil.copy2(src_file, dst_file)
            file_count += 1
            total_bytes += os.path.getsize(src_file)
            
    print(f"Copied {file_count} files ({total_bytes / 1024:.1f} KB) to {BACKUP_FOLDER}")
    
    # 2. Create Zip Archives
    for zip_target in [ZIP_DESKTOP, ZIP_TIMESTAMPED, ZIP_LOCAL]:
        with zipfile.ZipFile(zip_target, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(SOURCE_DIR):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for file in files:
                    if file in EXCLUDE_FILES or file.endswith(".tmp") or file.endswith("_backup.zip"):
                        continue
                    abs_file = os.path.join(root, file)
                    arcname = os.path.relpath(abs_file, SOURCE_DIR)
                    zf.write(abs_file, arcname)
        print(f"Created Archive: {zip_target} ({os.path.getsize(zip_target) / 1024:.1f} KB)")
        
    print("\nBackup completed successfully!")

if __name__ == "__main__":
    make_backup()
