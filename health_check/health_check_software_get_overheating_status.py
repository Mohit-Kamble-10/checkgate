import os
os.environ['OPENSSL_CONF']='/home/aikernel/src/configs/openssl.cnf'

import time 
import requests
import json
import os
import datetime
import psutil
import GPUtil
import config_operations as config   
from read_base_json import read_json
import sys
sys.path.append('/home/aikernel/src/') 
from secure_api import send_json

MachineID=config.MachineID
locationId=config.locationId


API=config.updateSoftwareStatus
main_log_folder=config.Logs_Folder_Path+'/healthcheck_software_overheating_status/'
json_path=config.HealthCheck_Software_Json



# Define average temperature thresholds
AVERAGE_CPU_TEMP = 85  # degrees Celsius, adjust based on your system
AVERAGE_GPU_TEMP = 75  # degrees Celsius, adjust based on your system

def get_cpu_temperature():
    try:
        temps = psutil.sensors_temperatures()
        for name, entries in temps.items():
            for entry in entries:
                if entry.label == 'Core 0':
                    return entry.current
        return None
    except Exception as e:
        print(f"Could not get CPU temperature: {e}")
        return None

def get_gpu_temperature():
    try:
        gpus = GPUtil.getGPUs()
        for gpu in gpus:
            return gpu.temperature
        return None
    except Exception as e:
        print(f"Could not get GPU temperature: {e}")
        return None

def check_temperature(component, temp, threshold):
    if temp is not None and temp > threshold:
        # print(f"ALARM: {component} temperature is above average! Current: {temp}°C, Threshold: {threshold}°C")
        return False
    else:
        # print(f"{component} temperature is within normal range.")
        return True

def get_temprature_status():
    base_data,status=read_json(json_path)
    now = datetime.datetime.now()
    folder_name=now.strftime("%d_%m_%Y")
    found_date_time=now.strftime("%d_%m_%Y_%H_%M_%S")
    request_path=main_log_folder+folder_name+'/request/'
    response_path=main_log_folder+folder_name+'/response/'
    os.makedirs(request_path,exist_ok=True)
    os.makedirs(response_path,exist_ok=True)
    #gpU_CPU_Temperature
    report={
    "machineId": MachineID,
    "locationId":locationId,
    "softwareId": 5,
    "cpu_temprature": 0,
    "cpu_temperature_above_avg_flag":False,
    "cpu_temperature_above_avg_threshold": AVERAGE_CPU_TEMP,
    "gpu_temprature": 0,
    "gpu_temperature_above_avg_flag":False,
    "gpu_temperature_above_avg_threshold":AVERAGE_GPU_TEMP,
    "workingStatus":'',
    "status": "",
    "aI_CreatedDate":found_date_time
    }
    request_json_filename=f'request_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    response_json_filename=f'response_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    
    start=time.time()
    cpu_temp = get_cpu_temperature()
    gpu_temp = get_gpu_temperature()
    print('cpu_temp : ',cpu_temp,type(cpu_temp))
    print('gpu_temp : ',gpu_temp,type(gpu_temp))
    report['cpu_temperature']=cpu_temp
    report['gpu_temperature']=gpu_temp
    # if cpu_temp is not None:
    #     report['cpu_temprature']=cpu_temp
    # if gpu_temp is not None:
    #     report['gpu_temprature']=gpu_temp

    if cpu_temp is not None and gpu_temp is not None:
        report['workingStatus']='Active'

    CPU_Status=check_temperature("CPU", cpu_temp, AVERAGE_CPU_TEMP)
    GPU_Status=check_temperature("GPU", gpu_temp, AVERAGE_GPU_TEMP)
    if CPU_Status==False:
        report['cpu_temperature_above_avg_flag']=True
    
    if GPU_Status==False:
        report['gpu_temperature_above_avg_flag']=True
    print('report : ',report)
    base_data['gpU_CPU_Temperature']=report
    with open(request_path+request_json_filename, 'w') as f:
        json.dump(base_data, f)
    
    response,message=send_json(API,json_data=base_data)
    # response={}
    # print('response : ',response)
    with open(response_path+response_json_filename, 'w') as f:
        json.dump(response, f)

    end=time.time()
    return {'Message':'get_temprature_status Done'+str(message),'Execution_Time':f'{end-start:.2f} sec','report':report}

def main():
    get_temprature_status()

if __name__=="__main__":
    main()
