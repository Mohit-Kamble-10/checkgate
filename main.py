import os
os.environ['OPENSSL_CONF']='/home/aikernel/src/configs/openssl.cnf'

import subprocess
import json
import os
import psutil
import datetime
import general_operations.config_operations as config  
import requests
from health_check import health_check_software_get_code_restart
import sys
sys.path.append('/home/aikernel/src/') 
os.makedirs("/home/aikernel/metadata//loaded_model",exist_ok=True)
from secure_api import send_json
MachineID=config.MachineID
locationId=config.locationId
active_lane=config.active_lane
API=config.MainCodeStartAPI

main_log_folder=config.Logs_Folder_Path+'/main_code_start/'
path='/home/aikernel/src/'

rtsp_type='global' # local / global
lane_count=config.lane_count
global_scripts=['ANPR_Inference_Script_main.py','Top_Inference_Script_main.py','Mineral_Classification_main.py','Colour_Classification_Inference_Script.py']
lane_wise_scripts=['upload_json_main.py','Capture_Top_main.py','Sync_ANPR_Top_main.py','RFID_reader_main.py','Sync_RFID_main.py','Front_Top_main.py']



def send_request(process_info):
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
    "Code_Started":found_date_time,
    "process_info":process_info
    }

    with open(request_path+request_json_filename, 'w') as f:
            json.dump(report, f)

    response={}
    try:
        response,message=send_json(API,json_data=report)
    except Exception as e:
        print(e)

    with open(response_path+response_json_filename, 'w') as f:
        json.dump(response, f)

    
    

def start_script(script_name, args=None):
    command = ['python3', path+script_name]
    if args:
        command.extend(args)
    return subprocess.Popen(command)

def is_process_running(script_name, args):
    print('script_name, args : ',script_name, args)
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

if __name__ == '__main__':
    # now = datetime.datetime.now()
    # date_str=now.strftime("%d_%m_%Y")
    scripts=[]
    for global_script in global_scripts:
        scripts.append((global_script,['']))
    
    for lane_wise_script in lane_wise_scripts:
        for i in range(1,lane_count+1):
            if i in active_lane:
                if lane_wise_script!='upload_json_main.py':
                    scripts.append((lane_wise_script,[str(i),rtsp_type]))
                elif lane_wise_script=='upload_json_main.py':
                    scripts.append((lane_wise_script,[str(i),'main.py']))
    

    
    print('scripts : ',scripts)
    process_info = {}
    restrt_flag=False
    for script, args in scripts:
        if not is_process_running(script, args):
            restrt_flag=True
            process = start_script(script, args)
            process_info[script] = process.pid
            print(f'Started script: {script} with args: {args}, process ID: {process.pid}')
            print('script, args process.pid',script, args, process.pid)
        else:
            print(f'Process for script: {script} with args: {args} is already running.')
    print('restrt_flag================> ',restrt_flag)
    if restrt_flag:
        health_check_software_get_code_restart.main()
    # if len(process_info)>0:
    print('process_info : ',process_info)
    # send_request(process_info)
    # with open("process_info.json", "w") as json_file:
    #     json.dump(process_info, json_file, indent=4)


# ps -ef | grep python
# ps aux | grep python | grep -v "grep python" | awk '{print $2}' | xargs kill -9