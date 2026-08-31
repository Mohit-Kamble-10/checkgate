import os
os.environ['OPENSSL_CONF']='/home/aikernel/src/configs/openssl.cnf'

import subprocess
import os
import subprocess
import os
import datetime
import json
import requests
import config_operations as config  
from read_base_json import read_json
import sys
sys.path.append('/home/aikernel/src/') 
from secure_api import send_json

MachineID=config.MachineID
LocationID=config.locationId


API=config.SaveUpdateHardwareStatus
main_log_folder=config.Logs_Folder_Path+'/healthcheck_hardware_gpu_status/'
json_path=config.HealthCheck_Hardware_Json

def check_gpu_error_state():
    try:
        output = subprocess.check_output(['nvidia-smi']).decode('utf-8')
        # Parsing the output to find GPU error state
        print("output.upper() : ",output.upper())
        if "ERR" in output.upper():
            return True
        else:
            return False
    except subprocess.CalledProcessError:
        # Handle the case when nvidia-smi command fails
        print("Error: Unable to run nvidia-smi command.")
        return False

def reboot_system():
    print("Rebooting the system...")
    os.system("sudo reboot")

if __name__ == "__main__":
    base_data,status=read_json(json_path)
    now = datetime.datetime.now()
    folder_name=now.strftime("%d_%m_%Y")
    found_date_time=now.strftime("%d_%m_%Y_%H_%M_%S")
    request_path=main_log_folder+folder_name+'/request/'
    response_path=main_log_folder+folder_name+'/response/'
    request_json_filename=f'request_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    response_json_filename=f'response_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    os.makedirs(request_path,exist_ok=True)
    os.makedirs(response_path,exist_ok=True)
    
    report={
    "machineId": MachineID,
    "hardwareId": 7,# GPU
    "locationId": LocationID,
    "workingstatus": "Active",
    "status": "On",
    "ai_createddate":found_date_time
    }

    if check_gpu_error_state():
        report['workingstatus']='Deactive'
        report['status']='Off'
        print("GPU is in an error state. Rebooting...")
        base_data['hardwareGPU']=report
        with open(request_path+request_json_filename, 'w') as f:
            json.dump(base_data, f)

        response,message=send_json(API,json_data=base_data)
    

        print("response : ",response)
        
        response={}
        with open(response_path+response_json_filename, 'w') as f:
           json.dump(response, f)
        print("System Reboot....")    
        reboot_system()
        
    else:
        base_data['hardwareGPU']=report
        with open(request_path+request_json_filename, 'w') as f:
           json.dump(base_data, f)
        print("API : ",API)
        print('base_data : ',base_data)

        response,message=send_json(API,json_data=base_data)
        print('response : ',response)
        # response={}
        with open(response_path+response_json_filename, 'w') as f:
           json.dump(response, f)
        
        print("GPU is not in an error state. No action needed.")
        

    

#sudo visudo -f /etc/sudoers.d/reboot_privilege
#mppoc ALL=(root) NOPASSWD: /sbin/reboot
# import os
# os.system("sudo reboot")
