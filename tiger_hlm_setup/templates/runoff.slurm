#!/bin/bash
#SBATCH --job-name=$name
#SBATCH --account=$account
#SBATCH --partition=$partition
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=$mem
#SBATCH --time=$time
#SBATCH --gres=gpu:1
#SBATCH --dependency=singleton
#SBATCH --mail-type=end
#SBATCH --mail-user=$email

set -e

# ==== Runoff ==========
module purge
module load Tiger_HLM_Runoff/$runoff_version
srun runoff $yaml > $out

# ==== Routing ==========
cd $routing_slurm_dir
sbatch $routing_script
