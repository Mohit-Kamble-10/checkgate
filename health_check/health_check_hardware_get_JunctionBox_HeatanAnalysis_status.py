import os
os.environ['OPENSSL_CONF']='/home/aikernel/src/configs/openssl.cnf'

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
main_log_folder=config.Logs_Folder_Path+'/healthcheck_hardware_junctionbox_heatanalysis/'
json_path=config.HealthCheck_Hardware_Json



def main():
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
    final_report=[]
    
    report={
    "machineid": MachineID,
    "hardwareId": 3,# GPU
    "locationid": LocationID,
    "workingStatus": "Active",
    "status":'On',
    "temprature": 30,
    "ai_createddate":found_date_time
    }
    
        
    base_data['hardwareheatanalysis']=report
    with open(request_path+request_json_filename, 'w') as f:
        json.dump(base_data, f)
        
    response,message=send_json(API,json_data=base_data)
    
    print('response : ',response)
    # response={}
    with open(response_path+response_json_filename, 'w') as f:
        json.dump(response, f)
    



if __name__=="__main__":
    main()
