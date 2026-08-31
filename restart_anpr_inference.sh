#!/usr/bin/env bash
set -euo pipefail
source /home/aikernel/base/bin/activate
cd /home/aikernel/src
pkill -f '/home/aikernel/src/ANPR_Inference_Script_main.py' 2>/dev/null || true
sleep 2
nohup python3 /home/aikernel/src/ANPR_Inference_Script_main.py \
  >>/home/aikernel/logs/ANPR_restart_nohup.log 2>&1 &
echo "STARTED pid=$!"
sleep 15
ps -eo pid,cmd | grep '[A]NPR_Inference_Script_main.py' || echo 'NOT_IN_PS'
tail -5 /home/aikernel/logs/ANPR_Logs.log || true
tail -8 /home/aikernel/logs/ANPR_restart_nohup.log || true
