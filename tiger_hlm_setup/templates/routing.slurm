#!/bin/bash
#SBATCH --job-name=$name
#SBATCH --account=$account
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=$cpus
#SBATCH --time=$time
#SBATCH --dependency=singleton
#SBATCH --mail-type=begin
#SBATCH --mail-type=end
#SBATCH --mail-user=$email

#run routing
module purge
module load Tiger_HLM_Routing/$routing_version
export OMP_NUM_THREADS=$cpus
routing $yaml > $out

$remove_runoff_cmd
