import shutil
from pathlib import Path

## gemini wrote me a simple script to shuffle the data and rename my folders

import shutil
from pathlib import Path

BASE_DIR = Path("/mnt/parscratch/users/acp25lmc")
SRC_DIR = BASE_DIR / "sensori"
DST_DIR = BASE_DIR / "sensori-data"

SITES = ["MS10", "MS21", "MS24", "MS25"]

# Create the base output directory if it doesn't exist
DST_DIR.mkdir(parents=True, exist_ok=True)

print(f"Copying files from {SRC_DIR} to {DST_DIR}...\n")

# 1. Collect copy jobs
copies = []
for site in SITES:
    site_path = SRC_DIR / site
    for folder in site_path.iterdir():
        parts = folder.name.split("_")
        new_folder_path = DST_DIR / f"{parts[0]}_{parts[1]}"
        copies.append((folder, new_folder_path))

# 2. Execute copies with skip check
for src, dst in copies:
    if dst.exists():
        print(f"[SKIPPED - EXISTS] Destination already exists: {dst.name} (Source: {src})")
        continue

    print(f"Copying: {src.name} -> {dst.name}")
    shutil.copytree(src, dst)

print("\nSuccessfully processed all directories to sensori-data.")