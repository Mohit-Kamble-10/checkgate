import sys
sys.path.append('/home/aikernel/src/')
sys.path.append('/home/aikernel/metadata')
import master_config 

import os
from glob import glob
import json
import datetime
import config_operations as config
from config_operations import MachineID,Source_path
Machine_Id=MachineID
source_path=Source_path

main_log_folder=config.Logs_Folder_Path+'/general_operations_images_remove_count/'

def get_creation_time(folder):
    return os.path.getctime(folder)


def remove_unwanted_imgaes():
    upload_backup_days=7
    now = datetime.datetime.now()
    remove_transaction_data={}
    for day in range(1,upload_backup_days+1):
        count=0
        target_date=(now-datetime.timedelta(days=day))
        day_str=target_date.strftime("%d-%m-%Y")
        dest_folder_name=source_path+'/OUTPUT_Backup/'+target_date.strftime("%b_%Y")+'/'+target_date.strftime("%d-%m-%Y")+'/'
        transaction_path_list = glob(f'{dest_folder_name}/**/')
        # transaction_path_list=['/home/aikernel/OUTPUT_Backup/Aug_2026/22-08-2026/IND0033220820260200592/']
        for transaction_path in transaction_path_list[:]:
            try:
                # print('transaction_path : ',transaction_path)
                raw_request=transaction_path+'/json/request_raw.json'
                if os.path.exists(raw_request):
                    with open(raw_request,'r') as json_data:
                        json_data=json.load(json_data)
                        if 'mining_full' not in json_data['final_top_class']:
                            if 'covered'  in json_data['final_top_class'] and 'hywa'  in json_data['final_front_class'] and master_config.Hywa_Covered:
                                print('Not removed Hywa Covered')
                            else:
                                print('Removed.')
                                image_path_list=glob(transaction_path+'/raw/Cross**')
                                image_path_list.extend(glob(transaction_path+'/raw/top_image**'))
                                image_path_list.extend(glob(transaction_path+'/prediction/pred_top_image**'))
                                
                                for image_path in image_path_list:
                                    os.remove(image_path)
                                    count+=1

                        else:
                            print('Not removed')
                        
                else:
                    #print('raw_request not found ')
                    image_path_list=glob(transaction_path+'/raw/Cross**')
                    image_path_list.extend(glob(transaction_path+'/raw/top_image**'))
                    image_path_list.extend(glob(transaction_path+'/prediction/pred_top_image**'))
                    for image_path in image_path_list:
                        os.remove(image_path)
                        #print(cross_lane_path)
                        count+=1
            
                #break
            except Exception as e:
                continue
        remove_transaction_data[day_str]=count
    return remove_transaction_data
if __name__=="__main__":
    # remove_unwanted_imgaes()
    now = datetime.datetime.now()
    folder_name=now.strftime("%d_%m_%Y")
    found_date_time=now.strftime("%d_%m_%Y_%H_%M_%S")
    request_path=main_log_folder+folder_name+'/request/'
    request_json_filename=f'{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    os.makedirs(request_path,exist_ok=True)
    response=remove_unwanted_imgaes()
    print("response : ",response)
    with open(request_path+request_json_filename, 'w') as f:
        json.dump(response, f)

    
