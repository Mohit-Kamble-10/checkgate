import os
os.environ['OPENSSL_CONF']='/home/aikernel/src/configs/openssl.cnf'


import time 
import requests
import json
import os
import datetime
import config_operations as config   
import serial
from read_base_json import read_json
import sys
sys.path.append('/home/aikernel/src/') 
from secure_api import send_json

MachineID=config.MachineID
LocationID=config.locationId
# hardwareId=2

API=config.SaveUpdateHardwareStatus
main_log_folder=config.Logs_Folder_Path+'/health_check_hardware_microcontroller_working_status/'
json_path=config.HealthCheck_Hardware_Json


def check_microcontroller_status():
    arduino_port = '/dev/ttyACM0'
    baud_rate = 9600
    try:
        ser = serial.Serial(arduino_port, baud_rate)
        time.sleep(2)  # Wait for the connection to establish
        if type(ser).__name__=='Serial':
            return True
        else:
            return False
    except Exception as e:
        return False


def get_microcontroller_working_status():
    base_data,status=read_json(json_path)
    now = datetime.datetime.now()
    folder_name=now.strftime("%d_%m_%Y")
    found_date_time=now.strftime("%d_%m_%Y_%H_%M_%S")
    request_path=main_log_folder+folder_name+'/request/'
    response_path=main_log_folder+folder_name+'/response/'
    os.makedirs(request_path,exist_ok=True)
    os.makedirs(response_path,exist_ok=True)

    report={
    "machineid": MachineID,
    "locationid": LocationID,
    "hardwareid": 2,
    "workingstatus": "Active",
    "status": "On",
    "aI_CreatedDate":found_date_time
    }
    request_json_filename=f'request_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    response_json_filename=f'response_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    
    start=time.time()
    if check_microcontroller_status==True:
        report['workingstatus']='Active'
    else:
        report['workingstatus']='Active'#'Deactive'#'Inactive'

    base_data['microcontrollerstatus']=report
    with open(request_path+request_json_filename, 'w') as f:
        json.dump(base_data, f)

    response,message=send_json(API,json_data=base_data)
    
    # response={}
    print('response : ',response)
    with open(response_path+response_json_filename, 'w') as f:
        json.dump(response, f)

    end=time.time()
    return {'Message':'get_microcontroller_working_status Done','Execution_Time':f'{end-start:.2f} sec','report':report}

def main():
    get_microcontroller_working_status()

if __name__=="__main__":
    main()
