#!/bin/bash
#SBATCH --job-name=calibration_check
#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --mail-user=lmcheesman1@sheffield.ac.uk
#SBATCH --mail-type=ALL
#SBATCH --output=/users/acp25lmc/Sensori/logs/calib_analysis_%j.out


module load Anaconda3/2025.06-1
source activate sensori
cd /users/acp25lmc/Sensori/slurm-jobs
python -u calibration_check.py