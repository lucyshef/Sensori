#!/bin/bash
#SBATCH --job-name=sensori_shard
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=24G
#SBATCH --mail-user=lmcheesman1@sheffield.ac.uk
#SBATCH --mail-type=ALL
#SBATCH --output=/users/acp25lmc/Sensori/logs/shard_%A_%a.out
#SBATCH --array=0-24             # 25 tasks (indexed 0 to 24)

# Set the total number of tasks so Python matches the array length
export NUM_TASKS=25

module load Anaconda3/2025.06-1
source activate sensori
cd /users/acp25lmc/Sensori
python -u shard_get_npy.py