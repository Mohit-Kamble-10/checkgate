#!/bin/bash


source /home/aikernel/base/bin/activate
#SRC_DIR="/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/src/"
SRC_DIR="/home/aikernel/src"


python3 /home/aikernel/src/health_check/health_check_software_get_machine_restart.py

# chmod +x runcron.sh
# crontab -e
# */15 * * * * /path/to/runcron.sh
# sudo service cron start
# tail -f  /var/log/syslog
# ps -ef | grep python
