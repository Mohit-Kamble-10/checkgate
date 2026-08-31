from fastapi import FastAPI
import uvicorn
from config_operations import MachineID
from get_machine_restart_status import check_restart_within_time
from supporting_function import get_last_transaction_done,get_last_transaction_uploaded,get_lane_restart_datetime
from get_image_roi import capture_frame
from support_start_stop_cron_jobs import main as cron_main
import datetime
import os
from typing import Dict, Any
app = FastAPI()
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
# main_path='/home/aikernel/src/operations/'
main_path='/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/src/operations/'
@app.get("/")
def read_root():
    return {"message": "Hello, World"}
#==============================================================code================================================================
@app.post("/get_config")
async def get_config(get_config):
    """
    send deployed configuration to server
    """
    return {}


@app.post("/set_config")
async def set_config(config_json):
    """
    take backup of old config.py and 
    set new configuration to LPU
    """
   

    return {}

@app.post("/deploy_new_code")
async def deploy_new_code(input_path):
    """
    take backup of deployed code and 
    deploy new code and execute it
    """
    
    return {}

@app.post("/start_stop_code")
async def start_stop_code(input_json:Dict):
    """
    if code is stopped due to some reson
    start the code / restart code 
    return code status
    """
    
    start_script=main_path+'start_code_dev.sh'
    stop_script=main_path+'stop_code.sh'
    status="Not_Found"
    error=''
    try:
        status=dict(input_json)['status']
        # print('status : ',status)
        if status=='start_code':
            os.system(start_script)
            # print("Bash script start_script executed successfully.")
        elif status=='stop_code':
            os.system(stop_script)
            # print("Bash script stop_script executed successfully.")
        elif status=='restart_code':
            os.system(stop_script)
            os.system(start_script)
            # print("Bash script restart executed successfully.")
        else:
            error="Invalid Option"
            # print("Invalid Option")
    except Exception as e:
        error=str(e)
        print(e)

    return {'status':status,'error':error}
#==============================================================Cron Job================================================================
@app.post("/start_stop_cronjob")
async def start_stop_cronjob(input_json:Dict):
    """
    if ceonjob is stopped due to some reson
    start the cron / restart code 
    return code status
    """
    main_obj=cron_main()
    # start_script=main_path+'start_code_dev.sh'
    # stop_script=main_path+'stop_code.sh'
    status="Not_Found"
    error=''
    try:
        status=dict(input_json)['status']
        # print('status : ',status)
        if status=='start_cron':

            main_obj.main('start')
            # print("Bash script start_script executed successfully.")
        elif status=='stop_cron':
            main_obj.main('stop')
            # print("Bash script stop_script executed successfully.")
        
        else:
            error="Invalid Option"
            # print("Invalid Option")
    except Exception as e:
        error=str(e)
        print(e)

    return {'status':status,'error':error}
#==============================================================get_data================================================================

@app.post("/get_raw_image_remote")
async def get_raw_image_remote(rtsp_sting):
    """
    get image from rtsp and convert it into base64
    share with server 
    """
    return {}


# @app.post("/get_LPU_basic_info")
# async def get_LPU_basic_info(input_json=None):
def get_LPU_basic_info(input_json=None):
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
    _,boot_time=check_restart_within_time()
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
        health_check=main_path+'health_check.sh'
        os.system(health_check)
        status='sent'
    except Exception as e:
        error=str(e)
    return {'status':status,'error':error}




#==============================================================transaction================================================================
@app.post("/pull_original_transaction")
async def pull_original_transaction(input_json):
    """
    input json conatin single or multiple transaction in list,
    we are going to upload original images of given transactions 
    """
    return {}


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


#==============================================================END================================================================


if __name__=='__main__':
    # uvicorn main:app --host=0.0.0.0 --port=8090
    uvicorn.run(app, host="0.0.0.0", port=8090)
    # get_LPU_basic_info()
