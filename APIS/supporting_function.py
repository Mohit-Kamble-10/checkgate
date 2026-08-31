
import os
os.environ['OPENSSL_CONF']='/home/aikernel/src/configs/openssl.cnf'

from glob import glob
import datetime
import json
import sys
sys.path.append('/home/aikernel/src/') 
sys.path.append('/home/aikernel/metatdata/') 
from configs import config
# sys.path.append(path)
from upload_images import upload_image,upload_image_live_api_st
from multiprocessing import Process
import shutil
now = datetime.datetime.now()
from secure_api import send_json
"""
get_most_recent_file
return most recent files absolute path
"""
def get_most_recent_file(folder_path):
    # Get list of all files in the folder
    files = glob(folder_path)

    if not files:
        return None

    # Find the file with the latest modification time
    most_recent_file = max(files, key=os.path.getmtime)
    return most_recent_file

def get_lane_restart_datetime():
    lane_count=2
    data={'lane_restart_datetime':{}}
    
    for lane_id in range(1,lane_count+1):
        request_path=f"../../health_check_logs/lane_code_restart_status/**/request/request_Front_Top_lane_{str(lane_id)}**"
        most_recent_transaction_path=get_most_recent_file(request_path)
        print('get_lane_restart_datetime : ',most_recent_transaction_path)
        
 
        if most_recent_transaction_path!="" and most_recent_transaction_path!= None:
            f = open(most_recent_transaction_path)
            json_data = json.load(f)
            data['lane_restart_datetime']['lane_'+str(lane_id)]=json_data['code_restart_datetime']
        else:
            data['lane_restart_datetime']['lane_'+str(lane_id)]='not_found'
        
    return data['lane_restart_datetime']


def get_last_transaction_done():
    trans_data={'last_transaction_done':{}}
    # lane_count=2
    transaction_path="../../output/"
    
    for lane_id in config.active_lane:
        path=transaction_path+f'IND{(str(2).zfill(4))+now.strftime("%d%m%Y")+str(lane_id).zfill(2)}**'
        most_recent_transaction_path=get_most_recent_file(path)
        print('most_recent_transaction_path : ',most_recent_transaction_path)
        
        if most_recent_transaction_path!="" and most_recent_transaction_path!= None:
            most_recent_transaction=most_recent_transaction_path.split('/')[-1]
            print('most_recent_transaction : ',most_recent_transaction)
            trans_data['last_transaction_done']['lane_'+str(lane_id)]=most_recent_transaction
        else:
            trans_data['last_transaction_done']['lane_'+str(lane_id)]='not_found'
    return trans_data['last_transaction_done']

def get_last_transaction_uploaded():
    trans_data={'last_transaction_uploaded':{}}
    lane_count=2
    transaction_path="../../output/"
    for lane_id in range(1,lane_count+1):
        path=transaction_path+f'IND{(str(2).zfill(4))+now.strftime("%d%m%Y")+str(lane_id).zfill(2)}**/json/image_upload_jsons/'
        most_recent_transaction_path=get_most_recent_file(path)
        # print('most_recent_transaction : ',most_recent_transaction)
        
        if most_recent_transaction_path!="" and most_recent_transaction_path!= None:
            most_recent_transaction=most_recent_transaction_path.split('/')[-1]
            # print('most_recent_transaction : ',most_recent_transaction)
            trans_data['last_transaction_uploaded']['lane_'+str(lane_id)]=most_recent_transaction
        else:
            trans_data['last_transaction_uploaded']['lane_'+str(lane_id)]='not_found'
    return trans_data['last_transaction_uploaded']

def get_response(request_data,response_json_path):
    try:
        response_Live,message=send_json(config.Add_MonitoringVehicle_Live,json_data=request_data)
        print("response_Live : ",response_Live)
        with open( response_json_path, 'w') as f:
            json.dump(response_Live, f)
        return response_Live
    except Exception as e:
        return {'error':str(e)}

def upload_old_images(transaction_id,number_plate_flag,anpr_flag,top_flag,top_valid):
    current_date_obj=datetime.datetime.now().date()
    date_str=transaction_id[7:15]
    # Parse the date string
    date_obj = datetime.datetime.strptime(date_str, "%d%m%Y")
    if current_date_obj==date_obj.date():
        transaction_path=f'/home/aikernel/output/{transaction_id}/'
    else:
        
        # Convert to desired formats
        formatted_month_year = date_obj.strftime("%b_%Y")  # Month_Year Dec_2024
        formatted_dd_mm_yyyy = date_obj.strftime("%d-%m-%Y")  # Month_Year 16-12-2024
        transaction_path=f'/home/aikernel/OUTPUT_Backup/{formatted_month_year}/{formatted_dd_mm_yyyy}/{transaction_id}'
    request_json_path=transaction_path+'/json/request_raw.json'
    response_json_path=transaction_path+'/json/response_Live.json'
    if os.path.exists(request_json_path):
        request_data={}
        with open(request_json_path) as f:
            request_data=json.load(f)
            # print("request_data : ",request_data)
        if 'datetime' in request_data.keys():
            created_data=request_data['datetime']
    if not os.path.exists(response_json_path):
        data=get_response(request_data,response_json_path)
        # print('File not found so we hit it Newly live response : ',response_json_path,data)
    
    if os.path.exists(response_json_path):
        data={}
        with open(response_json_path) as f:
            data=json.load(f)
            # st.json(data)
        print('data : ',response_json_path,data,len(data))
        if len(data)==0:
            data=get_response(request_data,response_json_path)
            # st.write('Newly live response : '+str(data))
        else:
            print('Got Data : data : ',data)
        print('final data : ',data)
        if 'responseData' in data.keys() and 'logId' in data['responseData'].keys():
            logId=data['responseData']['logId']
            print('logId : ',logId)
            print('transaction_path : ',transaction_path)
            print('created_data : ',created_data)
            
            #upload_images.upload_image(logid=logId,path=transaction_path,top_class_name='',created_data=created_data)
            if logId!='' and int(logId)>0:
                try:
                    # upload_meta_data=(int(logId),transaction_path,'',created_data)
                    # process = Process(target=upload_image, args=(upload_meta_data))
                    # upload_meta_data=int(logId),-1,transaction_path,'',created_data,True
                    # process=Process(target=upload_image_live,args=(upload_meta_data))
                    # process.start()
                    upload_image_live_api_st(int(logId),-1,transaction_path,created_data,number_plate_flag,anpr_flag,top_flag,top_valid)
                    #(logid_Live,logid_Test,path,top_class_name,created_data,Valid_Image=False)
                    # with open(response_path, 'w') as f:
                    #     json.dump(response, f)
                    # logging.info(f'MPDSS Image Uploading: Done')

                except Exception as e:
                    # with open(response_path_error, 'w') as f:
                    #     json.dump(response, f)
                    print(e)
                    return -1,str(e)
        
       
            

        
        
        return 0,""
            
    else:
        return -1,f"Path not found : "+str(response_json_path)

def move_new_weight():
    EXTRACT_DIR = "/home/aikernel/metadata/"
    backup_weights_dir = EXTRACT_DIR+"/backup_weights/"
    # Implement logic to move the new weight file to the appropriate directory
    new_weight_path='/home/aikernel/metadata/demo/**'
    dest_dir = '/home/aikernel/metadata/weights/'
    new_weights_path_list=glob(new_weight_path)
    backup_date = datetime.datetime.now().strftime("%d_%m%_Y_%H_%M_%S")
    for path in new_weights_path_list:
        model_name=path.split('/')[-1]
        prefix_dict={
            'ANPR_Detection_Model':'MP_NumberPlate_FrontTop_',
            'Top_Detection_Model':'Covered_mining_full_',
            'Colour_Classificaion_Model':'Bonnet_',
            'Mineral_Classificaion_Model':'MP_Minerla_Classification_',
        }
        for item,value in prefix_dict.items():
            if value in path:
                weight_path_list=glob(dest_dir+value+'**')
                if len(weight_path_list)>0:
                    for old_weight_path  in weight_path_list:
                        old_model_name=old_weight_path.split('/')[-1]
                        print('old_weight_path : ',old_weight_path)
                        if not os.path.exists(backup_weights_dir+old_model_name):
                            shutil.move(old_weight_path,backup_weights_dir)
        
        if not os.path.exists(dest_dir+model_name):             
            shutil.move(path, dest_dir)
            print(f"Moved {path} to {dest_dir}")
        else:
            print(f"Model already deployed {path}")
# get_response_id_transaction_id('IND0002161220240100342')