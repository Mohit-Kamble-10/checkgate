#!/bin/bash
# # This script starts all Python 3 processes
source /home/aikernel/base/bin/activate
chmod 777 "/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/"
SRC_DIR="/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm//src"
Main_Dir="/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/"
# Directory to store logs
LOG_DIR="$Main_Dir/logs"
output_DIR="$Main_Dir/output"
API_File="FastAPI.py"
LED_File="LED_ON_OFF.py"
SRC_DIR_API="/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/src/operations/"
# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"
mkdir -p "$output_DIR"


# Activate the Conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate  anpr_prod_cpu

# Define the directory to save the JSON file
request_DIR="/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/health_check_logs/start_process/request/"
response_DIR="/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/health_check_logs/start_process/response/"


mkdir -p "$request_DIR"
mkdir -p "$response_DIR"
# Get current datetime in the specified format
TIMESTAMP=$(date +"%d_%m_%Y_%H_%M_%S")

# Define the JSON file path
JSON_FILE="$request_DIR/python3_processes_start_$TIMESTAMP.json"

# Define an array of process names
declare -a PROCESS_NAMES=(
"main.py" \
"FastAPI.py" \
# "LED_ON_OFF.py"
)

# declare -a PROCESS_NAMES=("lane_1.py")

# Check and restart processes
for PROCESS_NAME in "${PROCESS_NAMES[@]}"
do
    # Check if the process is running
    #if ps aux | grep -v grep | grep "$PROCESS_NAME" > /dev/null
    if ps aux | grep -v grep | grep -q "$PROCESS_NAME";
    then
        echo "Process $PROCESS_NAME is running."
    else
        echo "Process $PROCESS_NAME is not running. Restarting..."
        # nohup python3 "$PROCESS_NAME" >> "$LOG_DIR/$PROCESS_NAME-$(date +'%Y-%m-%d_%H-%M-%S').log" & 
        if [ $PROCESS_NAME ==  $API_File ] || [ $PROCESS_NAME ==  $LED_File ];
        then
            # nohup /usr/bin/python3 "$SRC_DIR_API/$PROCESS_NAME" >> "$LOG_DIR/$PROCESS_NAME.log" & 
            python3 "$SRC_DIR_API/$PROCESS_NAME" >> "$LOG_DIR/$PROCESS_NAME.log" & 
        else
            # nohup /usr/bin/python3 "$SRC_DIR/$PROCESS_NAME" >> "$LOG_DIR/$PROCESS_NAME.log" &
            python3  "$SRC_DIR/$PROCESS_NAME" >> "$LOG_DIR/$PROCESS_NAME.log" &
        fi
        # Add additional commands if needed, e.g., setting environment variables

        echo "Process restarted."
    fi
done

PIDS=$(pgrep python3)
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
