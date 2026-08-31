
import os
os.environ['OPENSSL_CONF']='/home/aikernel/src/configs/openssl.cnf'

import time 
import requests
import json
import subprocess
import os
import datetime
from datetime import datetime, timedelta
import sys
sys.path.append('/home/aikernel/src/health_check/')
import config_operations as config   
from read_base_json import read_json
MachineID=config.MachineID
locationId=config.locationId
API=config.updateSoftwareStatus
json_path=config.HealthCheck_Software_Json

main_log_folder_machine_restart=config.Logs_Folder_Path+'/healthcheck_software_code_error_status/'



Cron_path='/home/aikernel/src/crons/'
script=Cron_path+'restart_code.sh'



def get_recently_created_folders(directory):
    """
    Check if any folders were created within the last 10 minutes in the given directory.

    Args:
        directory (str): Path of the directory to monitor.

    Returns:
        list: Names of folders created within the last 15 minutes.
    """
    now = time.time()
    fifteen_minutes_ago = now - 20 * 60
    recent_folders = []

    # Traverse the directory
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        # Check if it's a directory and within the time range
        if os.path.isdir(item_path):
            creation_time = os.path.getctime(item_path)
            if creation_time >= fifteen_minutes_ago:
                recent_folders.append(item)
    
    return recent_folders

# Example usage
def main():
    now = datetime.now()
    folder_name=now.strftime("%d_%m_%Y")
    found_date_time=now.strftime("%d_%m_%Y_%H_%M_%S")
    request_path=main_log_folder_machine_restart+folder_name+'/request/'
    # response_path=main_log_folder_machine_restart+folder_name+'/response/'
    os.makedirs(request_path,exist_ok=True)
    # os.makedirs(response_path,exist_ok=True)

    report={
        "machineId": MachineID,
        "locationId":locationId,
        "softwareId":2,
        "recent_folders_count":-1,
        "Code_Running":False,
        "aI_CreatedDate":found_date_time
        }

    request_json_filename=f'request_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    

    directory_to_check = "/home/aikernel/output/"  # Replace with your directory path
    recent_folders = get_recently_created_folders(directory_to_check)
    if recent_folders:
        report['recent_folders_count']=len(recent_folders)
        report['Code_Running']=True
        print("Folders created within the last 15 minutes:")
        for folder in recent_folders:
            print(folder)
    else:
        report['recent_folders_count']=len(recent_folders)
        report['Code_Running']=False
        print("No new folders were created within the last 10 minutes.")
        process = subprocess.Popen(script, shell=True)

        
        
    with open(request_path+request_json_filename, 'w') as f:
        json.dump(report, f)
if __name__ == "__main__":
    main()