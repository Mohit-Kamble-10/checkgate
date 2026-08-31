
import os
os.environ['OPENSSL_CONF']='/home/aikernel/src/configs/openssl.cnf'

import sys
# config_path='/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/src/configs/'
config_path='/home/aikernel/src/'
# config_path='../'
sys.path.append(config_path)
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Security,Request,Header
from tempfile import NamedTemporaryFile
import uvicorn
from configs.config import MachineID,LocationId,Cron_path
# from get_machine_restart_status import check_restart_within_time
from supporting_function import get_last_transaction_done,get_last_transaction_uploaded,get_lane_restart_datetime,upload_old_images,move_new_weight
from get_image_roi import capture_frame
from starlette import status
from support_start_stop_cron_jobs import main as cron_main
from datetime import datetime
import os
from typing import Dict, Any
import json
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv
import zipfile
import shutil
from pathlib import Path
from glob import glob
app = FastAPI()

# Load environment variables from .env file
load_dotenv()
# Get API Key from environment variables
API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "API-Key"

# Define the extraction directory
EXTRACT_DIR = "/home/aikernel/metadata/"
backup_weights_dir = EXTRACT_DIR+"/backup_weights"
weights_dir = EXTRACT_DIR+"/weights"
Path(weights_dir).mkdir(parents=True, exist_ok=True)
Path(backup_weights_dir).mkdir(parents=True, exist_ok=True)


# Define API Key Dependency
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

# Function to verify API key
def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    


async def valid_content_length(content_length: int = Header(..., lt=500_000_000)):
    return content_length

"""
Modules:
healthcheck
code
cron jobs
transaction
microcontroller
get_data
get_rtsp
"""
@app.get("/")
def read_root():
    return {"message": "Hello, World"}
#==============================================================code================================================================
@app.post("/get_config")
async def get_config():
    """
    send deployed configuration to server
    """
    response={
        "statusCode":200,
        "responseData":{},
        "statusMessage":""
    }
    config_path='/home/aikernel/src/configs/raw_jsons/get_profile.json'
    if os.path.exists(config_path):
        with open(config_path) as f:
            get_info = json.load(f)
        response={
        "statusCode":200,
        "responseData":get_info,
        "statusMessage":"Success"
        }   
    else:
        response={
        "statusCode":200,
        "responseData":{},
        "statusMessage":"File not found"
        }   
        

    return response


@app.post("/set_config")
async def set_config(config_json):
    from general_operations import get_raw_jsons
    """
    take backup of old config.py and 
    set new configuration to LPU
    """
    get_raw_jsons.main()
    config_path='/home/aikernel/src/configs/raw_jsons/get_profile.json'
    if os.path.exists(config_path):
        with open(config_path) as f:
            get_info = json.load(f)

    return get_info

@app.post("/deploy_new_code")
async def deploy_new_code(input_path):
    """
    take backup of deployed code and 
    deploy new code and execute it
    """
    
    return {}

@app.post("/start_stop_code")
async def start_stop_code(input_json:Dict,api_key: str = Depends(verify_api_key) ):
    """
    if code is stopped due to some reson
    start the code / restart code 
    return code status
    Input : 
    {
        "statusCode":"start_code",
    }
    """
    response={
        "statusCode":200,
        "responseData":{},
        "statusMessage":""
    }
    start_script=Cron_path+'main.sh'
    stop_script=Cron_path+'stop_code.sh'
    restart_script=Cron_path+'restart_code.sh'
    status="Not_Found"
    error=''
    try:
        status=dict(input_json)['status']
        # print('status : ',status)
        if status=='start_code':
            os.system(start_script)
            response['statusMessage']='Code Started'
            # print("Bash script start_script executed successfully.")
        elif status=='stop_code':
            # os.system(stop_script)
            response['statusMessage']='Not Allowd'
            # print("Bash script stop_script executed successfully.")
        elif status=='restart_code':
            # os.system(stop_script)
            # os.system(start_script)
            os.system(restart_script)
            response['statusMessage']='Code Restarted'
            print("restart_code script restart executed successfully.")
            
        else:
            response['statusMessage']='Invalid Option'
            # print("Invalid Option")
    except Exception as e:
        error=str(e)
        print(e)
        response['statusMessage']=error

    # return {'status':status,'error':error}
    return response



@app.post("/upload_weights")
def upload_file(
    file: UploadFile = File(...), 
    file_size: int = Depends(valid_content_length),
    api_key: str = Depends(verify_api_key) 
):
    file_path = os.path.join(EXTRACT_DIR, file.filename)
    temp_zip_path = f"{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(EXTRACT_DIR)
    except zipfile.BadZipFile:
        os.remove(temp_zip_path)
        raise HTTPException(status_code=400, detail="Invalid ZIP file")
    move_new_weight()
    return {"ok": True,'file':'Uploaded'}



#==============================================================Cron Job================================================================
@app.post("/start_stop_cron_job")
async def start_stop_cron_job(input_json:Dict):
    """
    if cron job is stopped due to some reson
    start the cron / restart code 
    return code status
    {
        "statusCode":"start_cron",
    }

    """
    response={
        "statusCode":200,
        "responseData":{},
        "statusMessage":""
    }
    main_obj=cron_main()
    status="Not_Found"
    error=''
    try:
        status=dict(input_json)['status']
        # print('status : ',status)
        if status=='start_cron':
            main_obj.main('start')
            # print("Bash script start_script executed successfully.")
        elif status=='stop_cron':
            # main_obj.main('stop')
            response['statusMessage']='Not Allowd'
            
            # print("Bash script stop_script executed successfully.")
        
        else:
            error="Invalid Option"
            # print("Invalid Option")
    except Exception as e:
        error=str(e)
        print(e)

    return {'status':status,'error':error}
#==============================================================get_data================================================================

# @app.post("/get_raw_image_remote")
# async def get_raw_image_remote(rtsp_sting):
#     """
#     get image from rtsp and convert it into base64
#     share with server 
#     """
#     return {}


@app.post("/get_LPU_basic_info")
# async def get_LPU_basic_info(input_json=None):
async def get_LPU_basic_info():
    """
    1. LPU restart data time 
    2. LPU Code restart data time Lane wise
    3. LPU Last Transaction date time
    4. LPU Last Transaction Upload date time 
    """

    data={
        'MachineID':MachineID,
        'restart_datetime':'not_found',
        'code_restart_datetime':{},
        'last_transaction_done':{},
        'last_transaction_uploaded':{}
        
    }
    # 1. LPU restart data time 
    _,boot_time=None,None#check_restart_within_time()
    data['restart_datetime']=boot_time
    
    # 2. LPU Code restart data time Lane wise
    data['code_restart_datetime']=get_lane_restart_datetime()

    #3. LPU Last Transaction date time
    data['last_transaction_done']=get_last_transaction_done()

    #4. LPU Last Transaction uploaded date time
    data['last_transaction_uploaded']=get_last_transaction_uploaded()

    print('final data : ',data)


    
    return data
#==============================================================microcontroller================================================================

@app.post("/set_LED_on_off")
async def set_LED_on_off(input_json):
    """
    LED on off based on call
    """
    return {}

@app.post("/set_LED_on_off_time")
async def set_LED_on_off_time(input_json):
    """
    LED on off time
    """
    return {}

#==============================================================healthcheck================================================================
@app.post("/get_current_health_check_status")
async def get_current_health_check_status():
    """
    get_current_health_check_status
    """
    error=''
    status=''
    try:
        health_check=Cron_path+'health_check.sh'
        os.system(health_check)
        status='sent'
    except Exception as e:
        error=str(e)
    return {'status':status,'error':error}




#==============================================================transaction================================================================
@app.post("/pull_original_transaction")
async def pull_original_transaction(input_json:Dict):
    """
    input json conatin single or multiple transaction in list,
    we are going to upload original images of given transactions 
    Input : {
        "transaction_list":["IND0002171220240100594"],
        "number_plate":True/False,
        "anpr":True/False,
        "top":True/False,
        "top_valid":True/False,
        
    }
    """
    response={
        "statusCode":200,
        "responseData":{},
        "statusMessage":""
    }
    try:
        data=dict(input_json)
        transaction_list=data['transaction_list']
        number_plate_flag=data['number_plate']
        
        anpr_flag=data['anpr']
        top_flag=data['top']
        top_valid=data['top_valid']
        
        print("transaction_list,number_plate_flag,anpr_flag,top_flag,top_valid : ",transaction_list,number_plate_flag,anpr_flag,top_flag,top_valid)
        for transaction_number in transaction_list:
            print("Uploading Started transaction_number : ",transaction_number)
            respose,error_message=upload_old_images(transaction_number,number_plate_flag,anpr_flag,top_flag,top_valid)
            if respose==0:
                response["statusMessage"] ="Data Send Successfully!"
            else:
                response['statusCode']= 501
                response["statusMessage"] =error_message
    except Exception as e:
        print(e)

    
    return response


@app.post("/upload_backup")
async def upload_backup(input_json):
    """
    input json conatin single or multiple date,
    we are going to upload backup
    """
    return {}

#==============================================================Get RTSP================================================================
@app.get("/capture_frame/")
async def read_root(rtsp_link: str):
    try:
        base64_str = capture_frame(rtsp_link)
        return {'image':base64_str}
    except Exception as e:
        raise e

#======================================================================================================================================

if __name__=='__main__':
    # uvicorn main:app --host=0.0.0.0 --port=8090
    # uvicorn.run(app, host="0.0.0.0", port=1136,h11_max_incomplete_event_size=500_000_000  )# 500MB
    uvicorn.run(app, host="0.0.0.0", port=1136, limit_max_requests=10000 )# 500MB
    # get_LPU_basic_info()
