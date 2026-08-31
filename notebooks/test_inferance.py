import psutil
import subprocess

# Define the script name to check
SCRIPT_NAME = "inferance.py"

# Check if the script is running
if any(process.cmdline() == ['python3', SCRIPT_NAME] for process in psutil.process_iter()):
    print(f"Script {SCRIPT_NAME} is already running.")
else:
    print(f"Script {SCRIPT_NAME} is not running. Starting the script...")

    # Execute your script here
    # Replace "/path/to/your/script.py" with the actual path to your script
    subprocess.run(["python3", "inferance.py"])