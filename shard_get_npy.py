#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from tqdm import tqdm

# Add scripts directory so we can import parse_recording directly
# sys.path.append(str(Path(__file__).parent / "scripts"))
from scripts.get_npy import parse_recording

# Input and Output paths
INPUT_DIR = Path("/mnt/parscratch/users/acp25lmc/joined_data_parquet")
OUTPUT_DIR = Path("/mnt/parscratch/users/acp25lmc/sensori")
SUBDIRS = ["MS10", "MS21", "MS24", "MS25"]

# Read SLURM environment parameters (defaults for local testing)
TASK_ID = int(os.environ.get("SLURM_ARRAY_TASK_ID", 0))
NUM_TASKS = int(os.environ.get("NUM_TASKS", 25))


def main():
    # 1. Collect and deterministically sort all parquet files across subdirectories
    all_files = []
    for subdir in SUBDIRS:
        folder = INPUT_DIR / subdir
        if folder.exists():
            all_files.extend(folder.glob("*.parquet"))

    all_files = sorted(all_files)
    total_files = len(all_files)

    if total_files == 0:
        print("No parquet files found in target directories.")
        return

    # 2. Calculate this worker's file slice
    files_per_task = total_files // NUM_TASKS
    start_idx = TASK_ID * files_per_task
    # The last task absorbs any remainder files
    end_idx = total_files if TASK_ID == (NUM_TASKS - 1) else start_idx + files_per_task

    current_job_files = all_files[start_idx:end_idx]

    print(f"--- Task {TASK_ID + 1}/{NUM_TASKS} ---")
    print(f"Total files found: {total_files}")
    print(f"Processing index {start_idx} to {end_idx - 1} ({len(current_job_files)} files)\n")

    # 3. Process assigned files sequentially
    eligible_count = 0
    ineligible_count = 0
    failed_count = 0

    for file_path in tqdm(current_job_files, desc=f"Task {TASK_ID}"):
        # Preserve directory structure (/sensori/MS10, /sensori/MS21, etc.)
        subdir = file_path.parent.name
        target_output = OUTPUT_DIR / subdir
        target_output.mkdir(parents=True, exist_ok=True)

        try:
            result = parse_recording(
                input_path=file_path,
                output_root=target_output,
                actipy_verbose=False,  # Keep stdout clean
            )
            if result.eligible:
                eligible_count += 1
            else:
                ineligible_count += 1
        except Exception as exc:
            failed_count += 1
            print(f"\n[Task {TASK_ID}] Error processing {file_path.name}: {exc}")

    print(f"\n--- Task {TASK_ID} Finished ---")
    print(f"Eligible: {eligible_count} | Ineligible (Failed QC): {ineligible_count} | Errors: {failed_count}")


if __name__ == "__main__":
    main()