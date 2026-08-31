#!/bin/bash
sudo chmod 666 /dev/ttyACM0
# Activate the virtual environment
source /home/aikernel/base/bin/activate
# /home/linux/miniconda3/condabin/conda activate anpr_prod_cpu

# python3 /home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/MP_AISES/operations/upload_backup.py
source_dir=/home/aikernel
chmod 777 $source_dir
python3 /home/aikernel/src/Arduino/Arduino_LED_Router/LED_ON_betwn_6PM_6AM.py

# Deactivate the virtual environment
# conda deactivate

# chmod +x runcron.sh
# crontab -e
# 0 1 * * * /path/to/runcron.sh # at 1 am every day
# Run at 6:01 AM every day
# 1 6 * * * /home/aikernel/MP_AISES-main/operations/runcron_LED_ON_OFF.sh

# Run at 6:01 PM every day
# 1 18 * * * /home/aikernel/MP_AISES-main/operations/runcron_LED_ON_OFF.sh

# sudo service cron start
# tail -f  /var/log/syslog