#!/bin/bash

sudo chmod 666 /dev/ttyACM0
source /home/aikernel/base/bin/activate
nohup python3 "/home/aikernel/src/health_check/health_check_hardware_get_power_status.py"  &

# chmod +x runcron.sh
# crontab -e
# */15 * * * * /path/to/runcron.sh
# sudo service cron start
# tail -f  /var/log/syslog
# ps -ef | grep python
