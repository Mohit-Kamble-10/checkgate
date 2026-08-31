import os
os.environ['OPENSSL_CONF']='/home/aikernel/src/configs/openssl.cnf'

import time 
import requests
import json
import os
import datetime
import config_operations as config   
from read_base_json import read_json
import serial
import time
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

def is_night_time():
    """Returns True if the current time is between 6 PM and 6 AM, otherwise False."""
    now = datetime.datetime.now()
    current_hour = now.hour
    return current_hour >= 18 or current_hour < 7

def control_relay(command):
    arduino_port = '/dev/ttyACM0'
    baud_rate = 9600

    """Send a command to the Arduino to control the relay."""
    try:
        # Open the serial port
        ser = serial.Serial(arduino_port, baud_rate)
        time.sleep(2)  # Wait for the connection to establish
        
        # Send the command to the Arduino
        ser.write(command.encode())
        print(f"Command '{command}' sent to Arduino")

        # Read a line from the serial port
        line = ser.readline().decode('utf-8').strip()
        if line:
            output=line
        else:
            output='Not_Found'
        

        
        if is_night_time():
            # control_relay('1')
            ser.write("1".encode())
            print("Relay turned ON, Light turned ON")
        else:
            # control_relay('0')
            ser.write("0".encode())
            # control_relay('3')
            print("It is not between 6 PM and 6 AM, Light remains OFF")

        # Close the serial port
        ser.close()
        return output
    except serial.SerialException as e:
        print("Serial port error:", e)
    except Exception as e:
        print("Error:", e)

def Check_power_status():
    output=control_relay('2')
    print('Check_power_status output: ',output)
    if "Power ON" in output: 
        return "On","Off"
    else:
        return "Off","On"




def get_generation_status():
    base_data,status=read_json(json_path)
    
    now = datetime.datetime.now()
    folder_name=now.strftime("%d_%m_%Y")
    found_date_time=now.strftime("%d_%m_%Y_%H_%M_%S")
    request_path=main_log_folder_powergeneration+folder_name+'/request/'
    response_path=main_log_folder_powergeneration+folder_name+'/response/'
    os.makedirs(request_path,exist_ok=True)
    os.makedirs(response_path,exist_ok=True)

    
    powerStatus,powerbackupstatus=Check_power_status()
    report={
    "machineid": MachineID,
    "locationid":locationId,
    "hardwareid": 6,
    "powerStatus": powerStatus,# Off # On
    "powerbackupstatus":powerbackupstatus,
    "workingstatus":'Active', #Deactive #Active
    "ai_createddate":found_date_time
    }
    base_data['powergenerationstatus']=report
    request_json_filename=f'request_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    response_json_filename=f'response_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    
    start=time.time()
    
    with open(request_path+request_json_filename, 'w') as f:
        json.dump(base_data, f)
    
    response,message=send_json(API,json_data=base_data)

    print('response : ',response)
    with open(response_path+response_json_filename, 'w') as f:
        json.dump(response, f)

    end=time.time()
    return {'Message':'get_generation_status Done','Execution_Time':f'{end-start:.2f} sec','report':report}

def main():
    get_generation_status()

if __name__=="__main__":
    main()
