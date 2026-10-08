import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

JSON_DIR = Path("/mnt/parscratch/users/acp25lmc/sensori-data")
PARQUET_DIR = Path("/mnt/parscratch/users/acp25lmc/joined_data_parquet")
STANDARD_GRAVITY = 9.80665

##### GEMINI WROTE THIS #####

def get_failed_calibration_samples():
    """Scan info.json files to find samples where calibration failed."""
    failed_samples = {}
    for json_path in JSON_DIR.rglob("info.json"):
        try:
            data = json.loads(json_path.read_text())
            is_calib_ok = data.get("eligibility", {}).get("calibration_ok", True) and data.get("CalibOK", 1) == 1

            if not is_calib_ok:
                filename = data.get("Filename", "")
                if filename:
                    parquet_path = Path(filename)
                else:
                    # Fallback lookup if Filename field is absent
                    sample_name = json_path.parent.name
                    matches = list(PARQUET_DIR.rglob(f"{sample_name}*.parquet"))
                    parquet_path = matches[0] if matches else None

                if parquet_path and parquet_path.exists():
                    failed_samples[json_path.parent.name] = parquet_path
        except Exception as e:
            print(f"Error reading {json_path}: {e}")

    return failed_samples


def analyze_parquet_file(file_path):
    """Analyze vector magnitude, unit scaling, clipping, and orientation diversity."""
    parquet_file = pq.ParquetFile(file_path)

    # Fast streaming metrics
    total_rows = 0
    nan_count = 0
    mag_min = float('inf')
    mag_max = float('-inf')

    # Aggregators for stationary orientation sampling
    # We downsample blocks to check 3D orientation diversity
    sample_blocks = []

    for batch in parquet_file.iter_batches(columns=['acc_x', 'acc_y', 'acc_z'], batch_size=100000):
        df_batch = batch.to_pandas()
        total_rows += len(df_batch)

        # Check NaNs
        nan_count += df_batch.isna().sum().sum()

        # Extract raw values (m/s^2 in raw parquet)
        acc_raw = df_batch[['acc_x', 'acc_y', 'acc_z']].to_numpy()

        # Convert to g as in get_npy.py
        acc_g = acc_raw / STANDARD_GRAVITY

        # Raw vector magnitude in g
        mags = np.linalg.norm(acc_g, axis=1)
        valid_mags = mags[np.isfinite(mags)]

        if len(valid_mags) > 0:
            mag_min = min(mag_min, valid_mags.min())
            mag_max = max(mag_max, valid_mags.max())

        # Sample every 10,000th row to assess overall orientation spread
        sample_blocks.append(acc_g[::10000])

    if not sample_blocks:
        return None

    all_sampled = np.vstack(sample_blocks)

    # Calculate orientation diversity across 3 axes (std dev of mean directional components)
    x_std = float(np.std(all_sampled[:, 0]))
    y_std = float(np.std(all_sampled[:, 1]))
    z_std = float(np.std(all_sampled[:, 2]))

    # Estimate median magnitude
    median_mag = float(np.median(np.linalg.norm(all_sampled, axis=1)))

    # Identify failure indicators
    unit_scale_issue = median_mag < 0.2 or median_mag > 5.0
    low_diversity = (x_std < 0.05) or (y_std < 0.05) or (z_std < 0.05)
    clipping_issue = mag_max > 16.0 or mag_min < -16.0

    return {
        "total_rows": total_rows,
        "nan_count": nan_count,
        "median_mag_g": round(median_mag, 3),
        "mag_range_g": (round(mag_min, 2), round(mag_max, 2)),
        "axis_std_g": (round(x_std, 3), round(y_std, 3), round(z_std, 3)),
        "unit_scale_issue": unit_scale_issue,
        "low_diversity": low_diversity,
        "clipping_issue": clipping_issue
    }


def main():
    print("Finding failed calibration samples...")
    failed_samples = get_failed_calibration_samples()
    print(f"Found {len(failed_samples)} failed samples with accessible Parquet files.")

    results = []

    for i, (sample_id, parquet_path) in enumerate(failed_samples.items(), 1):
        print(f"[{i}/{len(failed_samples)}] Analyzing {sample_id} ({parquet_path.name})...")
        metrics = analyze_parquet_file(parquet_path)
        if metrics:
            metrics["sample_id"] = sample_id
            results.append(metrics)

    df_res = pd.DataFrame(results)

    # Save diagnostic results
    output_path = "failed_calibration_analysis.csv"
    df_res.to_csv(output_path, index=False)

    print("\n" + "=" * 60)
    print("           CALIBRATION FAILURE ROOT CAUSE REPORT            ")
    print("=" * 60)
    print(f"Total Failed Parquet Files Analyzed: {len(df_res)}")
    print(f"  - Unit Scaling / Order-of-Magnitude Issue: {df_res['unit_scale_issue'].sum()}")
    print(f"  - Low Orientation Diversity (Static Pos): {df_res['low_diversity'].sum()}")
    print(f"  - Severe Clipping / Out-of-Bounds Values:  {df_res['clipping_issue'].sum()}")
    print(f"  - Files containing NaNs:                   {(df_res['nan_count'] > 0).sum()}")
    print("=" * 60)
    print(f"Detailed per-sample findings saved to {output_path}")


if __name__ == "__main__":
    main()