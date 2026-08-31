import sys
sys.path.append('../')
import os
from glob import glob
import datetime
import json
import time
import boto3
from io import BytesIO
import mimetypes  # Import the mimetypes library
# from configs.config import aws_access_key,aws_secret_access_key,public_bucket_name,upload_anpr_data_url,mining_vehicle_list
import os
import requests
from glob import glob
import shutil
from config_operations import MachineID,Source_path
Machine_Id=MachineID
source_path=Source_path


def get_creation_time(folder):
    return os.path.getctime(folder)


def create_backup_folder():
    upload_backup_days=7
    now = datetime.datetime.now()
    for day in range(1,upload_backup_days+1):
        target_date=(now-datetime.timedelta(days=day))
        day_str=target_date.strftime("%d%m%Y")
        dest_folder_name=source_path+'/OUTPUT_Backup/'+target_date.strftime("%b_%Y")+'/'+target_date.strftime("%d-%m-%Y")+'/'
        os.makedirs(dest_folder_name,exist_ok=True)
        all_folders_in_target_date=glob(source_path+f'/output/**{day_str}**')
        print(day_str ,' : ',len(all_folders_in_target_date))
        # print('Dest path : ',dest_folder_name)
        for index,folder_path in enumerate(all_folders_in_target_date):
            # if index%50==0:
            #     print(index,' : ',folder_path)
            shutil.move(folder_path,dest_folder_name)

if __name__=="__main__":
    create_backup_folder()