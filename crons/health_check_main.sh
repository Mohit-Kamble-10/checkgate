#!/bin/bash

source /home/aikernel/base/bin/activate

#SRC_DIR="/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/src/"
SRC_DIR="/home/aikernel/src"

# Hardwares
python3 "$SRC_DIR/health_check/health_check_hardware_get_camera_status.py"
python3 "$SRC_DIR/health_check/health_check_hardware_get_gpu_status.py"
python3 "$SRC_DIR/health_check/health_check_hardware_get_LED_ON_OFF_status.py"
python3 "$SRC_DIR/health_check/health_check_hardware_get_JunctionBox_HeatanAnalysis_status.py"
python3 "$SRC_DIR/health_check/health_check_hardware_get_microcontroller_working_status.py"
python3 "$SRC_DIR/health_check/health_check_hardware_get_solar_light_status.py"
python3 "$SRC_DIR/health_check/health_check_hardware_get_RFID_Reader_status.py"
# Softwares
#python3 health_check/health_check_hardware_get_tampering_status.py"
#python3 health_check/health_check_software_get_code_restart.py"
#python3 health_check/health_check_software_get_machine_restart.py"
python3 "$SRC_DIR/health_check/health_check_software_get_machine_storage_ram_status.py"
python3 "$SRC_DIR/health_check/health_check_software_get_overheating_status.py"
python3 "$SRC_DIR/health_check/health_check_software_get_running_code_status.py"
python3 "$SRC_DIR/health_check/health_check_software_get_code_error_status.py"

# chmod +x runcron.sh
# crontab -e
# */15 * * * * /path/to/runcron.sh
# sudo service cron start
# tail -f  /var/log/syslog
# ps -ef | grep python
