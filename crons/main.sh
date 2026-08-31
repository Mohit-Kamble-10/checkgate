#!/bin/bash

source /home/aikernel/base/bin/activate

#SRC_DIR="/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/src/"
SRC_DIR="/home/aikernel/src"


nohup python3 "$SRC_DIR/main.py" > "/home/aikernel/logs/cron_main.log" &
# nohup streamlit run /home/aikernel/src/streamlit_app/main.py --server.port=1135 > streamlit.log &
# nohup python3 /home/aikernel/src/APIS/FastAPI.py &
# chmod +x runcron.sh
# crontab -e
# */15 * * * * /path/to/runcron.sh
# sudo service cron start
# tail -f  /var/log/syslog
# ps -ef | grep python
