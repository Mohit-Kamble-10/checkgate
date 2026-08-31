import sys 
sys.path.append('/home/aikernel/src/')

import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
from glob import glob
import cv2
import datetime
import time
import os
import json
from configs import config
import re
import shutil
from collections import Counter
from detection import yolo_pred
import sys
import logging

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# source_path=config.root_path+'/src/weights/'
source_path=config.root_path+'/metadata/weights/'
now = datetime.datetime.now()
start_script_datetime=now.strftime("%d_%m_%Y_%H_%M")

Current_log_path=config.root_path+f"/logs/Top_Inferance_Logs_Remove_Unwanted.log"

FORMAT = "%(asctime)s: %(filename)s: %(levelname)s :%(lineno)5s:: - %(funcName)10s() :  %(message)s"
logging.basicConfig(filename=Current_log_path,
                    format=FORMAT,
                    filemode='a',
                    level=logging.DEBUG, # Set logging level
                    force=True)



def read_roi():
    ROI_INFO={}
    if os.path.exists(config.master_jsons+'/camera_details.json'):
        with open(config.master_jsons+'/camera_details.json') as json_file:
            get_camera_profile_data = json.load(json_file)
            logging.info('ROI Info Loaded...')
            return get_camera_profile_data
        
    else:
        print('camera_details.json not found')
        print(config.master_jsons+'/camera_details.json')
        logging.error('camera_details.json not found')
        
        # exit()

removed_image_count=0
class Top_Prediction():
    def __init__(self,lane_id) -> None:
        self.ROI_Info=read_roi()
        self.yolo_pred=yolo_pred(lane_id,image_type='TOP',roi_info= self.ROI_Info)
        logging.info('Top Model Loaded...')
        print('Top Model Loaded...')

    def main(self,image_dict,lane_id):
        self.removed_image_count=0
        self.removed_pred_image_count=0
        
        Top_Class_List=[]
        Top_Class_dict_valid={}
        Front_Class_List=[]
        Front_Class_dict_valid={}
        Top_Pred_image_dict={}
        Top_Class='Not_Found'
        Front_Class='Not_Found'
        Top_Class_valid='Not_Found'
        Front_Class_valid='Not_Found'
        Front_Valid_Image_list=[]
        for image_path,image in image_dict.items():
            image_name=image_path.split('/')[-1]
            top_output=self.yolo_pred.Top_main(image,lane_no=lane_id)
            if top_output['Status']==0:
                top_pred_image=top_output['Return_Disply_Frame'][0]
                Top_Pred_image_dict[image_name]=top_pred_image
                if top_output['Front_Class']!='':
                    Front_Class_List.append(top_output['Front_Class'])
                    if top_output['Front_Valid_Image']:
                            Front_Class_dict_valid[image_name]=top_output['Front_Class']

                if len(top_output['Raw_Top_Category_List'])>0:
                    Top_Class_List.append(top_output['Raw_Top_Category_List'][0])
                    if top_output['Front_Valid_Image']:
                            Top_Class_dict_valid[image_name]=top_output['Raw_Top_Category_List'][0]

            if len(top_output['Raw_Top_Category_List'])==0:
                # print('Front_Class_dict_valid : ',Front_Class_dict_valid)
                # print('Top_Class_dict_valid : ',Top_Class_dict_valid)
                # print('Top_Pred_image_dict : ',Top_Pred_image_dict.keys())
                prediction_path=image_path.replace('/raw/top_image','/prediction/pred_top_image')
                # print('removed_image_path : ',image_path)
                # print('removed_prediction_path : ',prediction_path)
                # cv2.imwrite('pred/removed/'+image_name,Top_Pred_image_dict[image_name])
                # shutil.copy(prediction_path,'pred/pred_removed/')
                os.remove(image_path)
                self.removed_image_count+=1
                if os.path.exists(prediction_path):
                    os.remove(prediction_path)
                    self.removed_pred_image_count+=1
            # else:
            #     cv2.imwrite('pred/not_removed/'+image_name,Top_Pred_image_dict[image_name])
        # print("self.removed_image_count : ",self.removed_image_count)
        # print("self.removed_pred_image_count : ",self.removed_pred_image_count)
        return self.removed_image_count,self.removed_pred_image_count

class main:
    def __init__(self):
        self.top_inferance_obj=Top_Prediction(2)
    def main(self):  
        
        count=0
        dublicate_image_count=0
        dublicate_pred_image_count=0
        removed_image_count=0
        removed_pred_image_count=0
        # day_list=sorted(glob('/home/aikernel/OUTPUT_Backup/Feb_2026/**'))
        day_list=sorted(glob('/mnt/mydisk/Backup/2024/Dec_2024/**'))

        # for day_path in day_list[18:]: # Dec_2024
        for day_path in day_list[:]: # Dec_2024
            mining_full_count=0
            transaction_deleted=0

            transaction_list=glob(day_path+'/**')
            print('day_path : ',day_path,len(transaction_list))
            logging.info('day_path : '+ day_path+' : '+str(len(transaction_list)))
            for index,transaction_path in enumerate(transaction_list[:]):
                data_path_image={}
                lane_number=str(int(transaction_path.split('/')[-1][15:17]))
                image_list=glob(transaction_path+'/raw/top_image**')
                
                if len(image_list)>0:
                    mining_full_count+=1
                    # print('transaction_path : ',transaction_path)            
                    for image_path in image_list:
                        image_name=image_path.split('/')[-1]
                        if '_valid'  in image_name:
                            top_image_path=image_path.replace('top_image_valid','top_image')
                            pred_top_image_path=image_path.replace('raw/top_image_valid','prediction/pred_top_image')
                            if os.path.exists(top_image_path):
                                os.remove(top_image_path)
                                dublicate_image_count+=1
                            if os.path.exists(pred_top_image_path):
                                os.remove(pred_top_image_path)
                                dublicate_pred_image_count+=1
                            
                            #shutil.copy(top_image_path,'pred/dublicate/')
                            #shutil.copy(pred_top_image_path,'pred/dublicate_pred/')     
                            if top_image_path in  image_list:          
                                image_list.remove(top_image_path)
                            if image_path in image_list:
                                image_list.remove(image_path)   
                            
                    # print('updated final_image_list : ',len(image_list))
                    for image_path in image_list[:]:
                        image_name=image_path.split('/')[-1]
                        image=cv2.imread(image_path)
                        data_path_image[image_path]=image
                
                    removed_image_count_,removed_pred_image_count_=self.top_inferance_obj.main(data_path_image,lane_number)
                    removed_image_count+=removed_image_count_
                    removed_pred_image_count+=removed_pred_image_count_
                else:
                    shutil.rmtree(transaction_path) 
                    transaction_deleted+=1
                if index%500==0:
                    print('Done :',index)
                    logging.info('Done :'+str(index))
                    
                # if count>=5:
                #     break
            print('Mining Full Count ',mining_full_count)
            print("dublicate_image_count : ",dublicate_image_count)
            print("dublicate_pred_image_count : ",dublicate_pred_image_count)
            print("removed_image_count : ",removed_image_count)
            print("removed_pred_image_count : ",removed_pred_image_count)
            print("transaction_deleted : ",transaction_deleted)
            
            logging.info('Mining Full Count :'+str(mining_full_count))
            logging.info('dublicate_image_count :'+str(dublicate_image_count))
            logging.info('dublicate_pred_image_count :'+str(dublicate_pred_image_count))
            logging.info('removed_image_count :'+str(removed_image_count))
            logging.info('removed_pred_image_count :'+str(removed_pred_image_count))
            logging.info('transaction_deleted :'+str(transaction_deleted))
        
        
if __name__=='__main__':
    main().main()

