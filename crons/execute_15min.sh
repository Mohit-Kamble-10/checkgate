#!/bin/bash

# Activate the virtual environment
source /home/aikernel/base/bin/activate
# source_dir=/home/aikernel
# operations_dir=/src/operations
source_dir=/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm
operations_dir=/src/operations
# /home/linux/miniconda3/condabin/conda activate anpr_prod_cpu
chmod 777 $source_dir

python3 "$source_dir/$operations_dir/get_gpu_status.py"
python3 "$source_dir/$operations_dir/get_power_status.py"
python3 "$source_dir/$operations_dir/get_camera_status.py"
python3 "$source_dir/$operations_dir/get_LED_light_status.py"
python3 "$source_dir/$operations_dir/get_tampering_status.py"
python3 "$source_dir/$operations_dir/get_overheating_status.py"
python3 "$source_dir/$operations_dir/get_machine_restart_status.py"
python3 "$source_dir/$operations_dir/get_machine_storage_status.py"
python3 "$source_dir/$operations_dir/get_microcontroller_working_status.py"
python3 "$source_dir/$operations_dir/get_running_code_status.py"
# python3 upload_backup.py

# Deactivate the virtual environment
# conda deactivate

# chmod +x runcron.sh
# crontab -e
# */15 * * * * /path/to/runcron.sh
# sudo service cron start
# tail -f  /var/log/syslog
# ps -ef | grep python
