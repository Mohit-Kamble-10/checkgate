import os
os.environ['OPENSSL_CONF']='/home/aikernel/src/configs/openssl.cnf'

import time 
import requests
import json
import os
import datetime
import sys
sys.path.append('/home/aikernel/src/') 
from secure_api import send_json
sys.path.append('/home/aikernel/src/health_check/')
import config_operations as config   
from read_base_json import read_json
MachineID=config.MachineID
locationId=config.locationId
API=config.updateSoftwareStatus
json_path=config.HealthCheck_Software_Json

main_log_folder_machine_restart=config.Logs_Folder_Path+'/healthcheck_software_code_restart_status/'



def get_code_restart_status():
    base_data,status=read_json(json_path)
    now = datetime.datetime.now()
    folder_name=now.strftime("%d_%m_%Y")
    found_date_time=now.strftime("%d_%m_%Y_%H_%M_%S")
    request_path=main_log_folder_machine_restart+folder_name+'/request/'
    response_path=main_log_folder_machine_restart+folder_name+'/response/'
    os.makedirs(request_path,exist_ok=True)
    os.makedirs(response_path,exist_ok=True)

    report={
        "machineId": MachineID,
        "locationId":locationId,
        "softwareId":2,
        "laneid":-1,
        "aI_CreatedDate":found_date_time
        }
    base_data['coderestart']=report
    request_json_filename=f'request_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    response_json_filename=f'response_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    
    start=time.time()
    
    with open(request_path+request_json_filename, 'w') as f:
        json.dump(base_data, f)
    print("API : ",API)
    print('request_json : ',base_data)

    response,message=send_json(API,json_data=base_data)
    
    # response={}
    print('response : ',response)
    with open(response_path+response_json_filename, 'w') as f:
        json.dump(response, f)

    end=time.time()
    return {'Message':'get_code_restart_status Done','Execution_Time':f'{end-start:.2f} sec','report':report}


def main():
    get_code_restart_status()

if __name__=="__main__":
    main()
