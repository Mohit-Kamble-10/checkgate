#!/bin/bash

# Source the Conda setup script. Adjust the path according to your Conda installation.
source ~/miniconda3/etc/profile.d/conda.sh

# Activate the Conda environment
conda activate  anpr_prod_cpu

# Verify activation (optional)
if [[ "$CONDA_DEFAULT_ENV" == "anpr_prod_cpu" ]]; then
    echo "Conda environment activated: $CONDA_DEFAULT_ENV"
else
    echo "Failed to activate Conda environment."
    exit 1
fi

# Your code to run within the Conda environment goes here
# For example, running a Python script
#python your_script.py

# Deactivate the Conda environment
conda deactivate
