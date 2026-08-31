
import os
os.environ['OPENSSL_CONF']='/home/aikernel/src/configs/openssl.cnf'

import requests
import json
import psutil
import datetime
import os
import config_operations as config 
from read_base_json import read_json
import sys
sys.path.append('/home/aikernel/src/') 
from secure_api import send_json

MachineID=config.MachineID
locationId=config.locationId
softwareId=1

API=config.updateSoftwareStatus#SaveMachineStorage#SaveUpdateSoftwareStatus

main_log_folder=config.Logs_Folder_Path+'/healthcheck_software_storage_status/'
json_path=config.HealthCheck_Software_Json

# def get_storage_ram_usage_status(report):
    
#     disk_usage = psutil.disk_usage('/')
    

#     total_space = (disk_usage.total)/(1024 * 1024 * 1024)# in GB'S
#     used_space = (disk_usage.used)/(1024 * 1024 * 1024)# in GB'S
#     percent_used = disk_usage.percent
#     report['total_space']=round(total_space,2)#f"{total_space:.2f}"
#     report['used_space']=round(used_space,2)#f"{used_space:.2f} GB"
#     report['percent_used']=round(percent_used,2)#f"{percent_used:.2f} %"
    
#     ram_info = psutil.virtual_memory()
#     total_ram_gb = ram_info.total / (1024 ** 3)
#     used_ram_gb = ram_info.used / (1024 ** 3)
#     ram_percent = ram_info.percent

#     report['total_ram']=round(total_ram_gb,2)#f"{total_ram_gb:.2f} GB"
#     report['used_ram']=round(used_ram_gb,2)#f"{used_ram_gb:.2f} GB"
#     report['percent_ramused']=round(ram_percent,2)#f"{ram_percent:.2f} %"

#     return report#total_space, used_space, percent_used
def get_storage_ram_usage_status(report):

    # ---- Disk Usage ----
    disk = psutil.disk_usage('/')

    total_space = disk.total / (1024 ** 3)   # GiB

    # ✅ df-style used (IMPORTANT FIX)
    used_space = (disk.total - disk.free) / (1024 ** 3)

    available_space = disk.free / (1024 ** 3)

    # ✅ df uses total for %
    percent_used = ((disk.total - disk.free) / disk.total) * 100

    report['total_space'] = round(total_space, 2)
    report['used_space'] = round(used_space, 2)
    report['available_space'] = round(available_space, 2)
    report['percent_used'] = round(percent_used, 2)

    # ---- RAM Usage ----
    ram = psutil.virtual_memory()

    total_ram = ram.total / (1024 ** 3)

    # Option 1: Matches "real usable" memory (recommended)
    # used_ram = (ram.total - ram.available) / (1024 ** 3)

    # Option 2 (uncomment if you want exact `free -h used`)
    used_ram = ram.used / (1024 ** 3)

    free_ram = ram.available / (1024 ** 3)
    ram_percent = ram.percent

    report['total_ram'] = round(total_ram, 2)
    report['used_ram'] = round(used_ram, 2)
    report['free_ram'] = round(free_ram, 2)
    report['percent_ramused'] = round(ram_percent, 2)

    return report


def main():
    base_data,status=read_json(json_path)
    now = datetime.datetime.now()
    folder_name=now.strftime("%d_%m_%Y")
    request_path=main_log_folder+folder_name+'/request/'
    response_path=main_log_folder+folder_name+'/response/'
    found_date_time=now.strftime("%d_%m_%Y_%H_%M_%S")

    report={
        "machineId": MachineID,
        "locationId":locationId,
        "softwareId":1,
        "total_space": -1,
        "used_space": -1,
        "percent_used": -1,
        "total_ram": -1,
        "used_ram": -1,
        "percent_ramused": -1,
        "ai_createddate":found_date_time
        }

    os.makedirs(request_path,exist_ok=True)
    os.makedirs(response_path,exist_ok=True)

    request_json_filename=f'request_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    response_json_filename=f'response_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    
    

    report=get_storage_ram_usage_status(report)

    base_data['storagemodel']=report
    print("API : ",API)
    print('base_data : ',base_data)
    with open(request_path+request_json_filename, 'w') as f:
        json.dump(base_data, f)
    

    response,message=send_json(API,json_data=base_data)
    
    # response=response.json()
    # response={}
    print('response : ',response)
    with open(response_path+response_json_filename, 'w') as f:
        json.dump(response, f)

if __name__=="__main__":
    main()
