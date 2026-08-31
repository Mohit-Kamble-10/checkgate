import os
os.environ['OPENSSL_CONF']='/home/aikernel/src/configs/openssl.cnf'


"""
Used to save all master data table for further operarations
1. Colour Master
2. Mineral Master
3. Vehicle Front Category Master
4. Vehicle Top Category Master
5. Hardware Master
"""
import time 
import requests
import json
import os
import datetime
import config_operations as config  
import sys
sys.path.append('/home/aikernel/src/') 
from secure_api import send_json_get


API_dict=config.All_Master_API_Dict
main_log_folder=config.Logs_Folder_Path+'/master_table_log/'
master_folder=config.Raw_Json_Folder_Path
processed_json=config.Processed_Json_Folder_Path
master_json=config.master_Processed_Json_Folder_Path

os.makedirs(master_folder,exist_ok=True)
os.makedirs(processed_json,exist_ok=True)

def process_get_profile_jsons(raw_data):
    camera_info_json_name='camera_details'
    RFID_info_json_name='RFID_details'
    processed_CameraData = {}
    processed_RFIDData = {}
    
    for item in raw_data['responseData']['cameraDetailsForProfiles']:

        cameraType=item['cameraType']
        laneId=item['laneId']
        globalUrl=item['globalUrl']
        localUrl=item['localUrl']
        isPrimary=item['isPrimary']
        id=item['id']
        if isPrimary:# and (cameraType=='ANPR' or cameraType=='Top'):
            ROI_info=item['rOIInfos'][0]['rOIRatioModels']
        

        if isPrimary:
            roi_dict={}
            for roi_data in ROI_info:
                pointNo=roi_data['pointNo']
                xRatio=round(float(roi_data['xRatio']),2)
                yRatio=round(float(roi_data['yRatio']),2)
                roi_dict[pointNo]={'xRatio':xRatio,'yRatio':yRatio}
                

            processed_CameraData[cameraType+'_'+str(laneId)] = {
                'globalUrl':globalUrl,
                'localUrl':localUrl,
                'id':id,
                'roi_info':roi_dict
            }
        else:
            processed_CameraData[cameraType] = {
                'globalUrl':globalUrl,
                'localUrl':localUrl,
                'id':id,
                'roi_info':{}
            }

        # Save the processed data to a new JSON file
    # with open(processed_json+camera_info_json_name+'.json', 'w') as file:
    #     json.dump(processed_CameraData, file, indent=4)
    #     print('Created : ',processed_json+camera_info_json_name+'.json')
    with open(master_json+camera_info_json_name+'.json', 'w') as file:
        json.dump(processed_CameraData, file, indent=4)
        print('master_json Created : ',master_json+camera_info_json_name+'.json')
    

    serverIP=raw_data['responseData']['localUrl']
    for item in raw_data['responseData']['rFIDPortDetails']:

        lane=item['lane']
        id=item['id']
        rfidReaderIP=item['rfidReaderIP']
        rfidPort=item['rfidPort']
        receiverPort=item['receiverPort']

        processed_RFIDData['RFID_'+str(lane)] = {
            'id':id,
            'rfidReaderIP':rfidReaderIP,
            'rfidPort':rfidPort,
            'receiverPort':receiverPort,
            'serverIP':serverIP
        }

    # with open(processed_json+RFID_info_json_name+'.json', 'w') as file:
    #     json.dump(processed_RFIDData, file, indent=4)
    #     print('Created : ',processed_json+RFID_info_json_name+'.json')

    with open(master_json+RFID_info_json_name+'.json', 'w') as file:
        json.dump(processed_RFIDData, file, indent=4)
        print('master_json Created : ',master_json+RFID_info_json_name+'.json')

    

def process_other_jsons(json_name,raw_data):
    function_name_value_dict={
        'color_class_category':'color',
        'front_class_category':'vehicleType',
        'hardware_class_categroy':'hardwareName',
        'mineral_class_category':'mineral',
        'top_class_category':'subcategory'
        
    }

    processed_data = {}
    for item in raw_data['responseData']:
        item_name = item[function_name_value_dict[json_name]].replace(" (Including ", "_").replace(")", "").replace(" ", "_").replace(" ", "_")
        processed_data[item_name] = item['id']
        if item_name=="NA":
            processed_data['Not_Found']=item['id']
    
        # Save the processed data to a new JSON file
    with open(processed_json+json_name+'.json', 'w') as file:
        json.dump(processed_data, file, indent=4)


def set_master(json_name,API):
    
        now = datetime.datetime.now()
        folder_name=now.strftime("%d_%m_%Y")
        found_date_time=now.strftime("%d_%m_%Y_%H_%M_%S")
        response_path=main_log_folder+folder_name+'/response/'
        master_dest_path=master_folder+json_name+'.json'
        os.makedirs(response_path,exist_ok=True)    
        response_json_filename=f'response_{json_name}_{found_date_time}.json'
        
        # try:
        if json_name=='get_profile':

            response,message=send_json_get(API,params={'LocationId':str(int(config.locationId))})
    

            print('get_profile response : ',response)
            process_get_profile_jsons(response)
        else:
            response,message=send_json_get(API)
    
            # response=response.json()
            print('response : ',json_name ,response)
            process_other_jsons(json_name,response)
        
            

        print('response : ',json_name,response)
        
        # with open(master_dest_path, 'w') as f:
        #     json.dump(response, f)
        with open(master_json+json_name+'.json', 'w') as f:
            json.dump(response, f)
        

        # except Exception as e:
            
        #     response={'Message':'Error','error':str(e)}
            
        

        with open(response_path+response_json_filename, 'w') as f:
            json.dump(response, f)
            
         

def main():
    for name,api in API_dict.items():
        try:
            print('api : ',api)
            set_master(name,api)
            
        except Exception as e:
            print(e)
            raise
            # continue

if __name__=="__main__":
    main()
