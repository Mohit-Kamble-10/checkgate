"""
# send json to server 
# take logID and 
# Save logID to send image to server
"""

"""
{

  "logId":0   ,
 "machineId": 32,
  "vehicleNo": "BB12BB3456",
  "topClassId": 4,
  "frontClassId": 4,
  "manual_check_reg": "Test",
  "raw_vehicleno": "BB12BB3456",
  "lane_id": 1,
  "colorId": 2,
  "materialId": 1,
  "quantity": 50,
  "anpR_frames_process": 1,
  "transactionId": "IND0002fJ565HKJHdfd6",
  "dateTime": "11_10_2024_17_52_17",
  "rfid": "",
  "axial_AI": 4,
  "approxWidth_AI": "12.2",
  "approxLength_AI": "13.2",
  "approxHeight_AI": "15.2",
  "isOverloaded_AI": 1
}

"""

import os
os.environ['OPENSSL_CONF']='/home/aikernel/src/configs/openssl.cnf'

import json
import time
from io import BytesIO
import mimetypes  
import cv2

import requests
from glob import glob
import datetime
import sys
import random
import logging
import shutil
from configs.config import aws_access_key,aws_secret_access_key, public_bucket_name,\
    mining_vehicle_list, jsons_path,mining_category,mahakhanij_updaload, \
    Add_MonitoringVehicle,Add_MonitoringVehicle_Live,Add_MonitoringVehicle_Test,root_path,\
    root_path_lane,MachineID,check_error,Live_Data_Upload,Test_Data_Upload,Dss_Data_Upload
from multiprocessing import Process
from upload_images import main as upload_image_main
from upload_images import main_live as upload_image_main_live
from upload_front_class import (
    load_json_file,
    load_front_class_maps,
    build_record_payloads,
    write_record_request_files,
)



now = datetime.datetime.now()
start_script_datetime=now.strftime("%d_%m_%Y_%H_%M")

Current_log_path=root_path+f"/logs/Upload_Data_Logs_old_transactions.log"
backup_logs_path=root_path+f"/logs/Upload_Data_Logs_old_transactions/"
os.makedirs(backup_logs_path,exist_ok=True)
if os.path.exists(Current_log_path):
    shutil.move(Current_log_path,backup_logs_path+f"Upload_Data_Logs_{start_script_datetime}.log")

FORMAT = "%(asctime)s: %(filename)s: %(levelname)s :%(lineno)5s:: - %(funcName)10s() :  %(message)s"
logging.basicConfig(filename=Current_log_path,
                    format=FORMAT,
                    filemode='a',
                    level=logging.DEBUG, # Set logging level
                    force=True)

def check_time(current_time):
    day_start = 6
    day_end = 18
    current_hour = current_time.hour
    if day_start <= current_hour < day_end:
        return 'day'
    else:
        return 'night'

def upload_data(path,colour_json_data,mineral_json_data,front_json_data_live,front_json_data_test,top_json_data):
    monitoringVehicle= {
        "transactionId":-1,
        "datetime":"",
        "vehicleno":"",
        "raw_vehicleno":"",
        "top_class_name":"Not_Found",
        "front_class_name":"Not_Found",
        "front_class_name_top_camera":"Not_Found",
        "top_class_name_top_camera":"Not_Found",
        "front_class_name_top_camera_valid":"Not_Found",
        "top_class_name_top_camera_valid":"Not_Found",
        "final_front_class":"",
        "final_top_class":"",
        "lane_id":1,
        "manual_check_reg":"",
        "ANPR_frames_process":0,
        "machineId" : int(MachineID),
        "colour": "Not_Found",
        "material": "Not_Found",
        "material_valid": "Not_Found",
        "material_final":"Not_Found",
        "quantity": 0,
        "rfid":""
       
    }
    #v4
    # request_json={
    #     "machineId":int(MachineID),
    #     "vehicleNo": "",
    #     "topClassId": 0,
    #     "frontClassId": 0,
    #     "manual_check_reg": "",
    #     "raw_vehicleno": "",
    #     "lane_id": 0,
    #     "colorId": 0,
    #     "materialId": 0,
    #     "quantity":0,
    #     "anpR_frames_process": 0,
    #     "transactionId": "",
    #     "dateTime": "",
    #     "rfid": "",
    #     }
    
    #v5
    request_json={
        "logId":0,
        "machineId":int(MachineID),
        "vehicleNo": "",
        "topClassId": 0,
        "frontClassId": 0,
        "manual_check_reg": "",
        "raw_vehicleno": "",
        "lane_id": 0,
        "colorId": 0,
        "materialId": 0,
        "quantity":0,
        "anpR_frames_process": 0,
        "transactionId": "",
        "dateTime": "",
        "rfid": "",
        "axial_AI": 0,
        "approxWidth_AI": 0,
        "approxLength_AI": 0,
        "approxHeight_AI": 0,
        "isOverloaded_AI": 0
        }


    start=time.time()
    transaction_path=path
    Front_Top_json_path=path+'/json/Front_Top_output.json'
    ANPR_json_path=path+'/json/ANPR_output.json'
    Mineral_json_path=path+'/json/Mineral_output.json'
    Colour_json_path=path+'/json/Colour_output.json'
    Top_Detection_json_path=path+'/json/Top_Detection_output.json'
    response_path=path+'/json/response.json'
    response_path_Live=path+'/json/response_Live.json'
    response_path_Test=path+'/json/response_Test.json'
    
    response_path_error=path+'/json/response_error.json'
    response_path_error_Live=path+'/json/response_error_Live.json'
    response_path_error_Test=path+'/json/response_error_Test.json'
    
    request_path_raw=path+'/json/request_raw.json'
    request_path=path+'/json/request.json'
    request_Live=path+'/json/request_Live.json'
    request_Test=path+'/json/request_Test.json'
    
    RFID_path=path+'/json/RFID_output.json'
    response_Live={}
    response_Test={}
    
    
    save_path='output/'+path.split('/')[-1]+'/' #'/'.join((path.split('/')[1:-1]))+'/'
    
    current_time = datetime.datetime.now()
    if os.path.exists(Front_Top_json_path):
        try:
            with open(Front_Top_json_path) as json_file:
                json_data_front = json.load(json_file)
        except Exception as e:
            return

        monitoringVehicle['front_class_name']=json_data_front['front_class_name']
        # monitoringVehicle['top_class_name']=json_data_front['top_class_name']
        monitoringVehicle['transactionId']=json_data_front['id']
        monitoringVehicle['datetime']=json_data_front['datetime']
        monitoringVehicle['lane_id']=json_data_front['lane_id']
        monitoringVehicle['ANPR_frames_process']=json_data_front['ANPR_frames_process']
    else:
        logging.info(f'Front_Top_json_path Not Found : {Front_Top_json_path}')

    if os.path.exists(Top_Detection_json_path):
        
        with open(Top_Detection_json_path) as top_json_file:
            top_detection_json_data = json.load(top_json_file)
            if top_detection_json_data['Front_Class']!=''or top_detection_json_data['Front_Class'] !='Not_Found':
                monitoringVehicle['front_class_name_top_camera']=top_detection_json_data['Front_Class']
            
            if 'Front_Class_Valid' in top_detection_json_data.keys():
                if top_detection_json_data['Front_Class_Valid']!='Not_Found' and top_detection_json_data['Front_Class_Valid']!='':
                    monitoringVehicle['front_class_name_top_camera_valid']=top_detection_json_data['Front_Class_Valid']

            if top_detection_json_data['Top_Class']!=''or top_detection_json_data['Top_Class'] !='Not_Found':
                monitoringVehicle['top_class_name_top_camera']=top_detection_json_data['Top_Class']
            
            if 'Top_Class_Valid' in top_detection_json_data.keys():
                if top_detection_json_data['Top_Class_Valid']!='Not_Found' and top_detection_json_data['Top_Class_Valid']!='':
                    monitoringVehicle['top_class_name_top_camera_valid']=top_detection_json_data['Top_Class_Valid']


    if os.path.exists(ANPR_json_path):
        with open(ANPR_json_path) as json_file:
            ANPR_json_data = json.load(json_file)
        monitoringVehicle['vehicleno']=ANPR_json_data['vehicleno']
        monitoringVehicle['raw_vehicleno']=ANPR_json_data['raw_vehicleno']
        monitoringVehicle['manual_check_reg']=ANPR_json_data['manual_check_req']
    else:
        logging.info(f'ANPR_json_path Not Found : {ANPR_json_path}')

    if os.path.exists(Mineral_json_path):
        with open(Mineral_json_path) as Mineral_json_file:
            mineral_data = json.load(Mineral_json_file)
            if mineral_data['material_valid']=='Kopra':
                mineral_data['material_valid']='Murum'
            if mineral_data['material']!=''or mineral_data['material'] !='Not_Found':
                monitoringVehicle['material']=mineral_data['material']
            if 'material_valid' in mineral_data.keys():
                if mineral_data['material_valid']!=''and mineral_data['material_valid'] !='Not_Found':
                    monitoringVehicle['material_valid']=mineral_data['material_valid']
                    monitoringVehicle['material_final']=monitoringVehicle['material_valid']
                else:
                    monitoringVehicle['material_final']=monitoringVehicle['material']
            else:
                monitoringVehicle['material_final']=monitoringVehicle['material']
            # monitoringVehicle['Raw_material_list']=mineral_data['Raw_material_list']
    else:
        logging.info(f'Mineral_json_path Not Found : {Mineral_json_path}')

    if os.path.exists(RFID_path):
        with open(RFID_path) as RFID_json_file:
            rfid_data = json.load(RFID_json_file)['RFID_data']
            rfid_final_text=""
            for rfid_list in rfid_data:
                for rfid_text_data in rfid_list:
                    rfid_text_data=rfid_text_data.split('-')[1]
                    rfid_final_text+=rfid_text_data+','
            monitoringVehicle['rfid']=rfid_final_text
    else:
        logging.info(f'RFID_path Data Not Found : {RFID_path}')

    if os.path.exists(Colour_json_path):
        with open(Colour_json_path) as Colour_json_file:
            colour_json_data_read = json.load(Colour_json_file)
        if colour_json_data_read['colour']!=''or colour_json_data_read['colour'] !='Not_Found':
            monitoringVehicle['colour']=colour_json_data_read['colour']

    else:
        # print(f'Colour_json_path Not Found : {Colour_json_path}')
        logging.info(f'Colour_json_path Not Found : {Colour_json_path}')

    # if monitoringVehicle['front_class_name'] not in mining_vehicle_list or monitoringVehicle['top_class_name'] not in mining_category:
    
     
    
    """_summary_
    Preprocess Json
    1.  front : ANPR front_class_name:  "" or "Not_Found" check top_camera output 
        front_class_name_top_camera if its different then ANPR mark it
    2. front : ANPR front_class_name:  "" or "Not_Found" check top_camera output 
        front_class_name_top_camera if its different then ANPR mark it
        Special Case Mining Full : if any camera mark mining full mark it as mining full

    """
    # Front Class
    # print("monitoringVehicle['front_class_name'] : ",monitoringVehicle['front_class_name'])
    # print("monitoringVehicle['front_class_name_top_camera'] : ",monitoringVehicle['front_class_name_top_camera'])
    
    ##=======================================================================
    if monitoringVehicle['front_class_name']!='Not_Found' and monitoringVehicle['front_class_name_top_camera']!='Not_Found'and \
        monitoringVehicle['front_class_name']==monitoringVehicle['front_class_name_top_camera']:
        monitoringVehicle['final_front_class']=monitoringVehicle['front_class_name']

    elif monitoringVehicle['front_class_name']!='Not_Found' and monitoringVehicle['front_class_name_top_camera']!='Not_Found'and \
        monitoringVehicle['front_class_name']!=monitoringVehicle['front_class_name_top_camera']:
        
        monitoringVehicle['front_class_name']=monitoringVehicle['front_class_name_top_camera']
        monitoringVehicle['final_front_class']=monitoringVehicle['front_class_name_top_camera']

    elif monitoringVehicle['front_class_name']!='Not_Found' and \
        monitoringVehicle['front_class_name_top_camera']=='Not_Found':
        monitoringVehicle['final_front_class']=monitoringVehicle['front_class_name']
        
    elif (monitoringVehicle['front_class_name']=='Not_Found') and \
        ( monitoringVehicle['front_class_name_top_camera']!='Not_Found'):
        monitoringVehicle['final_front_class']=monitoringVehicle['front_class_name_top_camera']

    elif (monitoringVehicle['front_class_name']=='Not_Found' ) and \
        (monitoringVehicle['front_class_name_top_camera']=='Not_Found'):
        monitoringVehicle['final_front_class']='Not_Found'
    
    if 'Front_Class_Valid' in top_detection_json_data.keys():
        if top_detection_json_data['Front_Class_Valid']!='Not_Found' and top_detection_json_data['Front_Class_Valid']!='':
            monitoringVehicle['final_front_class']=top_detection_json_data['Front_Class_Valid'] 
    # Top Class 
    # top_class_name not going to use to indetify mining full vehicles
    ##=======================================================================
    if monitoringVehicle['top_class_name']!='Not_Found' and monitoringVehicle['top_class_name_top_camera']!='Not_Found'and \
        monitoringVehicle['top_class_name']==monitoringVehicle['top_class_name_top_camera']:
        monitoringVehicle['final_top_class']=monitoringVehicle['top_class_name']
    
    # elif monitoringVehicle['top_class_name']=='mining_full' or monitoringVehicle['top_class_name_top_camera']=='mining_full':
    elif  monitoringVehicle['top_class_name_top_camera']=='mining_full':
    
        monitoringVehicle['final_top_class']='mining_full'
    
    elif monitoringVehicle['top_class_name']!='Not_Found' and monitoringVehicle['top_class_name_top_camera']!='Not_Found'and \
        monitoringVehicle['top_class_name']!=monitoringVehicle['top_class_name_top_camera']:
        monitoringVehicle['final_top_class']=monitoringVehicle['top_class_name']
        
    elif (monitoringVehicle['top_class_name']!='Not_Found' )and \
        ( monitoringVehicle['top_class_name_top_camera']=='Not_Found'):
        monitoringVehicle['final_top_class']=monitoringVehicle['top_class_name']

    elif (monitoringVehicle['top_class_name']=='Not_Found') and \
        ( monitoringVehicle['top_class_name_top_camera']!='Not_Found'):
        monitoringVehicle['final_top_class']=monitoringVehicle['top_class_name_top_camera']

    elif (monitoringVehicle['top_class_name']=='Not_Found' ) and \
        (monitoringVehicle['top_class_name_top_camera']=='Not_Found'):
        monitoringVehicle['final_top_class']='Not_Found'
    
    if 'Top_Class_Valid' in top_detection_json_data.keys():
        if top_detection_json_data['Top_Class_Valid']!='Not_Found' and top_detection_json_data['Top_Class_Valid']!='':
            monitoringVehicle['final_top_class']=top_detection_json_data['Top_Class_Valid']
    ##=======================================================================

    

            
    if monitoringVehicle['final_top_class']=='mining_full':
        monitoringVehicle['quantity']=random.randint(90,100)


    request_json['vehicleNo']=monitoringVehicle['vehicleno']        
    request_json['raw_vehicleno']=monitoringVehicle['raw_vehicleno']
    request_json['lane_id']=monitoringVehicle['lane_id']
    request_json['manual_check_reg']=monitoringVehicle['manual_check_reg']
    request_json['anpR_frames_process']=monitoringVehicle['ANPR_frames_process']
    request_json['transactionId']=monitoringVehicle['transactionId']
    request_json['dateTime']=monitoringVehicle['datetime']
    request_json['rfid']=monitoringVehicle['rfid']

    if monitoringVehicle['final_top_class']=='mining_full':
        request_json['quantity']=monitoringVehicle['quantity']

    if monitoringVehicle['final_top_class']!='Not_Found'and monitoringVehicle['final_top_class']!='':
        if monitoringVehicle['final_top_class']!='covered_mining_full':
            request_json['topClassId']=top_json_data[monitoringVehicle['final_top_class']]     
        else:
            request_json['topClassId']=1# covered_mining_full -> upload as covered  
            monitoringVehicle['material_final']='Not_Found'
    else:
        request_json['topClassId']=6 # not_found
    
    if monitoringVehicle['colour']!='Not_Found' and monitoringVehicle['colour']!='':
        request_json['colorId']=colour_json_data[monitoringVehicle['colour']]
    else:
        request_json["colorId"]=10 #colour_json_data[monitoringVehicle['colour']]

    
    # print('monitoringVehicle  : ',monitoringVehicle)
    if monitoringVehicle['material_final']!='Not_Found' and monitoringVehicle['material_final']!='':
        if monitoringVehicle['material_final']=='covered_mining_full' or monitoringVehicle['material_final']=='Blur':
            request_json["materialId"]=7
        else:
            request_json["materialId"]=mineral_json_data[monitoringVehicle['material_final']]
    else:
        request_json["materialId"]=7   

    logging.info(f'updaload Json dump: Start')

    request_json_live, request_json_test = build_record_payloads(
        request_json,
        monitoringVehicle['final_front_class'],
        front_json_data_live,
        front_json_data_test,
    )
    write_record_request_files(
        request_path, request_Live, request_Test, request_json_live, request_json_test,
    )
    logging.info(
        f"frontClassId Live={request_json_live['frontClassId']} "
        f"Test={request_json_test['frontClassId']} "
        f"class={monitoringVehicle['final_front_class']}"
    )

    logging.info(f'MPDSS Uploading: Start')

    with open(request_path_raw, 'w') as f:
        json.dump(monitoringVehicle, f)

    
    if monitoringVehicle['final_top_class'] not in mining_category:# 
        #monitoringVehicle['final_front_class'] not in mining_vehicle_list and 
        response={"statusCode": "200", "statusMessage": 
"Non Mining Vehicle or not mining full", "statusMessage1": 'null', "responseData": -1, 
"responseData1": 'null', "responseData2": 'null', "responseData3": 'null', "responseData4": 'null'}
        with open(response_path, 'w') as f:
            json.dump(response, f)
        with open(response_path_Live, 'w') as f:
            json.dump(response, f)
        with open(response_path_Test, 'w') as f:
            json.dump(response, f)
        
         
    else:
        try:
            logid=-1
            logid_Live=-1
            logid_Test=-1
            response={"statusCode": "-1", "statusMessage": "Not Uploaded", 
                      "statusMessage1": "null", "responseData": "-1", "responseData1": "null", 
                      "responseData2": "null", "responseData3": "null", "responseData4": "null"}
            # print('Add_MonitoringVehicle : ',Add_MonitoringVehicle)
            # print('request_json : ',request_json)
            # response=requests.post(Add_MonitoringVehicle_v4,json=request_json,verify=False)
            if Dss_Data_Upload:
                logging.info(f'request_json : '+str(request_json_test))
                response=requests.post(Add_MonitoringVehicle,json=request_json_test,verify=False)
                response=response.json()
                logging.info(f'response_json : '+str(response))
                print('response : ',response)
            else:
                response['statusMessage']='DSS Upload False'
                # print("Dss response : ",response)
                with open(response_path, 'w') as f:
                    json.dump(response, f)

            if Live_Data_Upload:
                response_Live=requests.post(Add_MonitoringVehicle_Live,json=request_json_live,verify=False)
                response_Live=response_Live.json()
                # print('response_Live : ',response_Live)
                logging.info(f'response_Live : '+str(response_Live))
            else:
                response_Live['statusMessage']='Live Upload False'
                print("Live response : ",response_Live)
                with open(response_path_Live, 'w') as f:
                    json.dump(response_Live, f)
                response_Live={}
            if Test_Data_Upload:
                response_Test=requests.post(Add_MonitoringVehicle_Test,json=request_json_test,verify=False)
                response_Test=response_Test.json()
                # print('response_Test : ',response_Test)
                logging.info(f'response_Test : '+str(response_Test))
            else:
                response_Test['statusMessage']='Test Upload False'
                print("Test response : ",response_Test)
                with open(response_path_Test, 'w') as f:
                    json.dump(response_Test, f)
                response_Test={}
            if Dss_Data_Upload:
                if response['statusCode']=="200" and response["statusMessage"]== "Data Saved Successfully!":
                    logid=response['responseData']['logId']
                
                elif response['statusCode']=="409" and 'already a record with same TransactionId' in response["statusMessage"]:
                        logid=response['responseData']['logId']
                
                else:

                    with open(response_path_error, 'w') as f:
                            json.dump(response, f)
                if logid!='' and int(logid)>0:
                    try:
                        upload_meta_data=(int(logid),path,monitoringVehicle['final_top_class'],monitoringVehicle['datetime'])
                        process = Process(target=upload_image_main().main, args=(upload_meta_data))
                        process.start()
                        with open(response_path, 'w') as f:
                            json.dump(response, f)
                    
                        logging.info(f'MPDSS Image Uploading: Done')

                    except Exception as e:
                        with open(response_path_error, 'w') as f:
                            json.dump(response, f)
                        print(e)
                        logging.error(f'MPDSS Uploading: Error '+str(e))

            if Live_Data_Upload or Test_Data_Upload:
                if Live_Data_Upload:
                    try:
                        print("response_Live : ",response_Live)
                        with open( response_path_Live, 'w') as f:
                            json.dump(response_Live, f)
                        if response_Live['statusCode']=="200" and response_Live["statusMessage"]== "Data Saved Successfully!":
                            
                            logid_Live=response_Live['responseData']['logId']
                        elif response_Live['statusCode']=="409" and 'already a record with same TransactionId' in response_Live["statusMessage"]:
                            logid_Live=response_Live['responseData']['logId']
                        else:
                            logid_Live=-1
                    except Exception as e:
                        print(e)
                    
                else:
                    logid_Live=-1
                
                if Test_Data_Upload:
                    try:
                        with open(response_path_Test, 'w') as f:
                            json.dump(response_Test, f)
                        if response_Test['statusCode']=="200" and response_Test["statusMessage"]== "Data Saved Successfully!":
                            logid_Test=response_Test['responseData']['logId']
                        else:
                            logid_Test=-1
                    except Exception as e:
                        print(e)
                        # with open(response_path_error, 'w') as f:
                    
                else:
                    logid_Test=-1
                
                print('logid_Test : ',logid_Test, ' logid_Live: ',logid_Live)
                try:
                    logging.info(f'Test / Live Image Uploading: Started'+str(transaction_path))
                    print("Test Upload Image Transaction Path : ",transaction_path)
                    
                    upload_meta_data_test=(int(logid_Live),int(logid_Test),transaction_path,monitoringVehicle['final_top_class'],monitoringVehicle['datetime'])
                    process = Process(target=upload_image_main_live().main, args=(upload_meta_data_test))
                    process.start()
                    
                
                    logging.info(f'Test / Live Image Uploading: Done')

                except Exception as e:
                    with open(response_path_error, 'w') as f:
                        json.dump(response, f)
                    print(e)
                    logging.error(f'MPDSS Uploading: Error '+str(e))
            

        except Exception as e:
            print(e)
            logging.error(f'MPDSS Uploading: Error '+str(e))

    
    

    end=time.time()
    uploading_time=end-start
    print(path.split('/')[-1],':',round(uploading_time,2))
    return 


def find_files_created_within_last_minute(folder_path):
    
    recent_files = []
    

    for file_path in sorted(glob(folder_path))[:]:
        try:
            if os.path.exists(file_path+'/json/Front_Top_output.json') and \
                os.path.exists(file_path+'/json/Mineral_output.json') and \
                os.path.exists(file_path+'/json/ANPR_output.json') and \
                os.path.exists(file_path+'/json/Top_Detection_output.json') and \
                os.path.exists(file_path+'/json/Colour_output.json') and \
                not os.path.exists(file_path+'/json/response_Live.json') and \
                not os.path.exists(file_path+'/json/response_Test.json') :
                recent_files.append(file_path)
            else:
                pass
                # if not os.path.exists(file_path+'/json/Front_Top_output.json'):
                #     print('Front_Top_output.json does not exist')
                # if not os.path.exists(file_path+'/json/Mineral_output.json'):
                #     print('Mineral_output.json does not exist')
                # if not os.path.exists(file_path+'/json/ANPR_output.json'):
                #     print('ANPR_output.json does not exist')
                # if not os.path.exists(file_path+'/json/Top_Detection_output.json'):
                #     print('Top_Detection_output.json does not exist')
                # if not os.path.exists(file_path+'/json/Colour_output.json'):
                #     print('Colour_output.json does not exist')
                # if  os.path.exists(file_path+'/json/response_Live.json'):
                #     print('response_Live.json does exist')
                # if os.path.exists(file_path+'/json/response_Test.json') :
                #     print('response_Test.json does  exist')

        except Exception as e:
            # print(e)
            continue
    return recent_files
def find_files_image_uploading_pending(folder_path):
    recent_files = []

    for file_path in glob(folder_path):
        if os.path.exists(file_path+'/json/Front_Top_output.json') and \
            os.path.exists(file_path+'/json/Mineral_output.json') and \
            os.path.exists(file_path+'/json/ANPR_output.json') and \
            os.path.exists(file_path+'/json/Top_Detection_output.json') and \
            os.path.exists(file_path+'/json/response.json') and \
            not os.path.exists(file_path+'/json/image_upload_jsons'):
            recent_files.append(file_path)
        # else:
        #     print('File not exist : ',file_path)
    print('find_files_image_uploading_pending : ',recent_files)
    return recent_files

def read_jsons():
    """Load category ID maps. Live and Test use separate frontClassId JSON files."""
    colour_json_data = load_json_file(jsons_path + '/color_class_category.json')
    mineral_json_data = load_json_file(jsons_path + '/mineral_class_category.json')
    top_json_data = load_json_file(jsons_path + '/top_class_category.json')
    front_json_data_live, front_json_data_test = load_front_class_maps(
        jsons_path, live_upload=Live_Data_Upload, test_upload=Test_Data_Upload,
    )
    return colour_json_data, mineral_json_data, front_json_data_live, front_json_data_test, top_json_data

class main():
    def main(self):   
        full_path='/home/aikernel/OUTPUT_Backup/May_2026/11-05-2026/'   
        logging.info(f'read_jsons Started ')  
        colour_json_data,mineral_json_data,front_json_data_live,front_json_data_test,top_json_data=read_jsons()
        logging.info(f'read_jsons Done ')  
        # print('colour_json_data : ',colour_json_data)
        # print('mineral_json_data : ',mineral_json_data)
        # print('front_json_data : ',front_json_data)
        # print('top_json_data : ',top_json_data)
        # folder_path = full_path+f'/*IND0003060920240{str(lane_no)}*'
        folder_path = full_path+f'/**/'
        # print('folder_path : ',folder_path)
        zero_count=0
        # recent_files_pending_image_uploading_list=find_files_image_uploading_pending(folder_path)
        #check_pending_upload_image(recent_files_pending_image_uploading_list)
        
        recent_files = find_files_created_within_last_minute(folder_path)
        if len(recent_files)==0:
            zero_count+=1
            if zero_count>9999:
                zero_count=0
        else:
            zero_count=0

            

        # if  (zero_count%10==0) or len(recent_files)>0:
        #     logging.info(f'pending count : {str(len(recent_files))}')
        print(f'pending count : {str(len(recent_files))}')
        for transaction_count,file_path in enumerate(recent_files[:]):
            try:
                if transaction_count%100==0:
                    print('file_path  : ',file_path) 
                start_time=time.time()
                # logging.info(f'Uploding Started : {file_path}')
    
                upload_data(file_path,colour_json_data,mineral_json_data,front_json_data_live,front_json_data_test,top_json_data)
                # logging.info(f'Uploding Done : {file_path} : {str(round(time.time()-start_time,2))}')

            except Exception as e:
                print(e)
                continue
                if check_error:
                    print('Upload Json : ',e,file_path)
                    # raise
                logging.error(f'Upload Json Error  : {str(e)} ')
                print('Upload Json : ',e,file_path)
                if 'Input/output error' in  str(e):
                    logging.error('upload_json code Error : upload_json.py  Restarted')
                    os.execv(sys.executable, ['python3'] + sys.argv)
                
        # break


if __name__ == "__main__":
    main().main()