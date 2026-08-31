#!/bin/bash
# # This script kills all Python 3 processes
source /home/aikernel/base/bin/activate
request_DIR="/home/aikernel//health_check_logs/stop_process/request/"
response_DIR="/home/aikernel/health_check_logs/stop_process/request/"

# request_DIR="/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/health_check_logs/stop_process/request/"
# response_DIR="/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/health_check_logs/stop_process/request/"
mkdir -p "$request_DIR"
mkdir -p "$response_DIR"
# Get current datetime in the specified format
TIMESTAMP=$(date +"%d_%m_%Y_%H_%M_%S")

# Define the JSON file path
JSON_FILE="$request_DIR/python3_processes_kill_$TIMESTAMP.json"

EXCLUDE_FILE="FastAPI.py"

# Find the PID of the specific Python file
EXCLUDE_PID=$(pgrep -f "$EXCLUDE_FILE")

# Get all the PIDs of python3 processes
# PIDS=$(pgrep python3)
PIDS=$(ps aux | grep '[p]ython3' | awk '{print $2}')

# Check if there are any python3 processes
if [ -z "$PIDS" ]; then
    echo "No Python 3 processes found."
    exit 0
fi

# Start the JSON file
echo "{" > "$JSON_FILE"
echo "  \"processes\": [" >> "$JSON_FILE"

# Loop through each PID and gather process details
for PID in $PIDS; do
    # Get the process details
    PROCESS_INFO=$(ps -p $PID -o pid=,user=,start=,cmd= --no-headers)
    
    # Extract details into variables
    PID_NUM=$(echo $PROCESS_INFO | awk '{print $1}')
    USER=$(echo $PROCESS_INFO | awk '{print $2}')
    START=$(echo $PROCESS_INFO | awk '{print $3}')
    CMD=$(echo $PROCESS_INFO | awk '{print substr($0, index($0,$4))}')

    # Append process information to the JSON file
    echo "    {" >> "$JSON_FILE"
    echo "      \"pid\": \"$PID_NUM\"," >> "$JSON_FILE"
    echo "      \"user\": \"$USER\"," >> "$JSON_FILE"
    echo "      \"start_time\": \"$START\"," >> "$JSON_FILE"
    echo "      \"command\": \"$CMD\"" >> "$JSON_FILE"
    echo "    }," >> "$JSON_FILE"
done

# Remove the last comma and close the JSON array
sed -i '$ s/,$//' "$JSON_FILE"
echo "  ]" >> "$JSON_FILE"
echo "}" >> "$JSON_FILE"

# Kill all python3 processes
# echo "Killing the following Python 3 processes: $PIDS"
# kill $PIDS

for PID in $PIDS; do
  if [[ $PID != $EXCLUDE_PID ]]; then
    echo "Killing the following Python processes: $PID"
    kill $PID
  fi
done

# Verify if the processes have been killed
if [ $? -eq 0 ]; then
    echo "Successfully killed all Python processes."
else
    echo "Failed to kill some or all Python processes."
fi

echo "Process information saved to $JSON_FILE"
