

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
import operations.config_operations as config  


API_dict=config.All_Master_API_Dict
main_log_folder=config.Logs_Folder_Path+'/master_table_log/'
master_folder=config.Master_Folder_Path
os.makedirs(master_folder,exist_ok=True)


def set_master(json_name,API):
    
        now = datetime.datetime.now()
        folder_name=now.strftime("%d_%m_%Y")
        found_date_time=now.strftime("%d_%m_%Y_%H_%M_%S")
        response_path=main_log_folder+folder_name+'/response/'
        master_dest_path=master_folder+json_name+'.json'
        os.makedirs(response_path,exist_ok=True)    
        response_json_filename=f'response_{json_name}_{found_date_time}.json'
        
        try:
            response=requests.get(API)
            response=response.json()
            print('response : ',json_name,response)
            with open(master_dest_path, 'w') as f:
                json.dump(response, f)

        except Exception as e:
            
            response={'Message':'Error','error':str(e)}
            
        

        with open(response_path+response_json_filename, 'w') as f:
            json.dump(response, f)
         

def main():
    for name,api in API_dict.items():
        try:
            set_master(name,api)
        except Exception as e:
            continue

if __name__=="__main__":
    main()
