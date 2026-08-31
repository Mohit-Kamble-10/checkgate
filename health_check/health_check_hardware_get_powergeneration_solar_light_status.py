import os
os.environ['OPENSSL_CONF']='/home/aikernel/src/configs/openssl.cnf'

import time 
import requests
import json
import os
import datetime
import config_operations as config   
from read_base_json import read_json
import sys
sys.path.append('/home/aikernel/src/') 
from secure_api import send_json

MachineID=config.MachineID
locationId=config.locationId

API=config.SaveUpdateHardwareStatus

main_log_folder_powergeneration=config.Logs_Folder_Path+'/health_check_hardware_powergeneration_status/'
main_log_folder_solor=config.Logs_Folder_Path+'/health_check_hardware_solar_status/'
main_log_folder_light_sensor=config.Logs_Folder_Path+'/health_check_hardware_light_sensor_status/'
json_path=config.HealthCheck_Hardware_Json
def get_generation_status():
    base_data,status=read_json(json_path)
    
    now = datetime.datetime.now()
    folder_name=now.strftime("%d_%m_%Y")
    found_date_time=now.strftime("%d_%m_%Y_%H_%M_%S")
    request_path=main_log_folder_powergeneration+folder_name+'/request/'
    response_path=main_log_folder_powergeneration+folder_name+'/response/'
    os.makedirs(request_path,exist_ok=True)
    os.makedirs(response_path,exist_ok=True)

    report={
    "machineid": MachineID,
    "locationid":locationId,
    "hardwareid": 6,
    "powerStatus": 'On',
    # "status": "On",
    "powerbackupstatus":"Off",
    "workingstatus":'Active',
    "ai_createddate":found_date_time
    }
    base_data['powergenerationstatus']=report
    request_json_filename=f'request_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    response_json_filename=f'response_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    
    start=time.time()
    
    with open(request_path+request_json_filename, 'w') as f:
        json.dump(base_data, f)

    response,message=send_json(API,json_data=base_data)
    
    # response={}
    print('response : ',response)
    with open(response_path+response_json_filename, 'w') as f:
        json.dump(response, f)

    end=time.time()
    return {'Message':'get_generation_status Done','Execution_Time':f'{end-start:.2f} sec','report':report}

def get_solar_status():
    base_data,status=read_json(json_path)
    # hardwareId=5
    now = datetime.datetime.now()
    folder_name=now.strftime("%d_%m_%Y")
    found_date_time=now.strftime("%d_%m_%Y_%H_%M_%S")
    request_path=main_log_folder_solor+folder_name+'/request/'
    response_path=main_log_folder_solor+folder_name+'/response/'
    os.makedirs(request_path,exist_ok=True)
    os.makedirs(response_path,exist_ok=True)

    report={
    "machineId": MachineID,
    "locationId":locationId,
    "hardwareId": 5,
    "status": 'On',
    # "powerGeneration": "On",
    "workingstatus":'Active',
    "ai_createddate":found_date_time
    }
    request_json_filename=f'request_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    response_json_filename=f'response_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    
    start=time.time()
    base_data['hardwaresolar']=report
    with open(request_path+request_json_filename, 'w') as f:
        json.dump(base_data, f)

    response,message=send_json(API,json_data=base_data)
    
    # response={}
    print('response : ',response)
    with open(response_path+response_json_filename, 'w') as f:
        json.dump(response, f)

    end=time.time()
    return {'Message':'main_log_folder_solor Done','Execution_Time':f'{end-start:.2f} sec','report':report}

def get_light_sensor_status():
    base_data,status=read_json(json_path)
    # hardwareId=4
    now = datetime.datetime.now()
    folder_name=now.strftime("%d_%m_%Y")
    found_date_time=now.strftime("%d_%m_%Y_%H_%M_%S")
    request_path=main_log_folder_light_sensor+folder_name+'/request/'
    response_path=main_log_folder_light_sensor+folder_name+'/response/'
    os.makedirs(request_path,exist_ok=True)
    os.makedirs(response_path,exist_ok=True)

    report={
    "machineid": MachineID,
    "locationid":locationId,
    "hardwareId": 4,
    "status": 'On',
    "workingstatus":'Active',
    "ai_createddate":found_date_time
    }
    request_json_filename=f'request_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    response_json_filename=f'response_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    
    start=time.time()
    base_data['hardwarelightsensor']=report
    with open(request_path+request_json_filename, 'w') as f:
        json.dump(base_data, f)

    response,message=send_json(API,json_data=base_data)
    
    # response={}
    print('response : ',response)
    with open(response_path+response_json_filename, 'w') as f:
        json.dump(response, f)

    end=time.time()
    return {'Message':'get_light_sensor_status Done','Execution_Time':f'{end-start:.2f} sec','report':report}

def main():
    get_light_sensor_status()
    get_solar_status()
    get_generation_status()

if __name__=="__main__":
    main()
