import os
os.environ['OPENSSL_CONF']='/home/aikernel/src/configs/openssl.cnf'

import subprocess
import os
import datetime
import json
import requests
import psutil
from read_base_json import read_json
import config_operations as config  
import sys


src_folder='/home/aikernel/src/'
sys.path.append(src_folder)
from secure_api import send_json
path='/home/aikernel/src/'
from main import rtsp_type,global_scripts,lane_wise_scripts
MachineID=config.MachineID
locationId=config.locationId
active_lane=config.active_lane

API=config.updateSoftwareStatus#CodeHealthCheckStatus
json_path=config.HealthCheck_Software_Json
main_log_folder=config.Logs_Folder_Path+'/healthcheck_software_running_code_status/'

lane_count=config.lane_count
#rtsp_type='local' # local / global
#global_scripts=['ANPR_Inference_Script_main.py','Mineral_Classification_main.py','Colour_Classification_Inference_Script.py']
#lane_wise_scripts=['upload_json_main.py','Capture_Top_main.py','Sync_ANPR_Top_main.py','RFID_reader_main.py','Sync_RFID_main.py','Front_Top_main.py']

def is_process_running(script_name, args):
    print('script_name, args : ',script_name, args)
    if args!=[''] :
        print('--------------->if')
        for process in psutil.process_iter(['pid', 'cmdline']):
            try:
                if path+script_name in process.info['cmdline'] and all(arg in process.info['cmdline'] for arg in args):
                    return True
            except Exception as e :
                print(e)
                #
                # pass
                # continue
        return False
    else:
        print('--------------->else')
        for process in psutil.process_iter(['pid', 'cmdline']):
            try:
                if path+script_name in process.info['cmdline']:
                    return True
            except Exception as e :
                print(e)
                #
                # pass
                # continue
        return False


def main():
    base_json,status=read_json(json_path)
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
        "locationId":locationId,
        "softwareId":4,
        "runningProcess":"",
        "stoppedProcess": "",
        "softwarename":"",
        "aI_CreatedDate":found_date_time
        }


    scripts=[]
    # now = datetime.datetime.now()
    # date_str=now.strftime("%d_%m_%Y")

    for global_script in global_scripts:
        scripts.append((global_script,['']))
    
    for index,lane_wise_script in enumerate(lane_wise_scripts):
        for i in range(1,lane_count+1):
            if i in active_lane:
                if lane_wise_script!='upload_json_main.py':
                    scripts.append((lane_wise_script,[str(i),rtsp_type]))
                elif lane_wise_script=='upload_json_main.py':
                    scripts.append((lane_wise_script,[str(i),'main.py']))
                    
    running_process=[]
    stopped_process=[]
    for script, args in scripts:
        if  is_process_running(script, args):
            # running_process.append([script,args])
            running_process.append(script)
            print(f'Process for script: {script} with args: {args} is already running.')
        else:
            print(f'Process for script: {script} with args: {args} is stopped.')
            # stopped_process.append([script,args])
            stopped_process.append(script)
    report['runningProcess']=str(running_process)
    report['stoppedProcess']=str(stopped_process)
    base_json['codeHealthcheck']=report
    print('base_json:',base_json)
    with open(request_path+request_json_filename, 'w') as f:
        json.dump(base_json, f)

    response,message=send_json(API,json_data=base_json)
    # response={}
    print('response : ',response)
    with open(response_path+response_json_filename, 'w') as f:
        json.dump(response, f)

            

if __name__ == "__main__":
    main()

    
    
        
    