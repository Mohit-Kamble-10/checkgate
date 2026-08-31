#!/bin/bash

# Activate the virtual environment
source /home/aikernel/base/bin/activate
# /home/linux/miniconda3/condabin/conda activate anpr_prod_cpu

# python3 /home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/MP_AISES/operations/upload_backup.py
source_dir=/home/aikernel
chmod 777 $source_dir
python3 /home/aikernel/src/operations/upload_backup.py

# Deactivate the virtual environment
# conda deactivate

# chmod +x runcron.sh
# crontab -e
# 0 1 * * * /path/to/runcron.sh # at 1 am every day
# sudo service cron start
# tail -f  /var/log/syslog
