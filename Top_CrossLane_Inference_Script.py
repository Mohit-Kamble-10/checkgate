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
# lane_no=sys.argv[1] # string 1,2,3

# Load the saved model
# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# source_path=config.root_path+'/src/weights/'
source_path=config.root_path+'/metadata/weights/'


class Top_Cross_Prediction():
    def __init__(self,lane_id) -> None:
        self.yolo_pred=yolo_pred(lane_id,image_type='CROSS')
        print('Top CROSS Model Loaded...')

    
    
    def main(self,Top_image_name_list,image_List):

        Top_image_crop_list=[]
        Axel_count_list=[]
        Top_Pred_image_list=[]
        Axel_count='Not_Found'
        distance_in_pixels_list=[]
        for index,image in enumerate(image_List):
            top_output=self.yolo_pred.Top_cross_lane(image)
            if top_output['Status']==0:
                top_crosslane_pred_image=top_output['Return_Disply_Frame'][0]
                Top_Pred_image_list.append({Top_image_name_list[index]:top_crosslane_pred_image})
                if top_output['Vehicle_IN_ROI']==True:
                    Axel_count_list.append({Top_image_name_list[index]:top_output['Axel_count']})

                    distance_in_pixels_list.append({Top_image_name_list[index]:top_output['distance_in_pixels']})

                    if len(top_output['Vehicle_Crop'])>0:
                        Top_image_crop_list.append({Top_image_name_list[index]:top_output['Vehicle_Crop'][0]})
                    
        if len(Axel_count_list)>0:
            Axel_count=max(Axel_count_list,key=Axel_count_list.count)
        
        return Axel_count,Axel_count_list,distance_in_pixels_list,Top_image_crop_list,Top_Pred_image_list
    

class main():
    def __init__(self) -> None:
        self.Top_obj=Top_Cross_Prediction(lane_id=None)

  
    def save_top_prediction(self,folder_path,Top_Pred_image_list_dict):
        dest_path=folder_path+'/prediction/'
        for data in Top_Pred_image_list_dict:
            image_name=list(data.keys())[0]
            Pred_image=list(data.values())[0]
            cv2.imwrite(dest_path+f'/pred_{image_name}',Pred_image)
    
    def save_top_crop(self,folder_path,Top_image_crop_list_dict):
        dest_path=folder_path+'/top_crop/'
        for data in Top_image_crop_list_dict:
            image_name=list(data.keys())[0]
            image_crop=list(data.values())[0]
            cv2.imwrite(dest_path+f'/{image_name}',cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB))
    
    def Top_CrossLane_Start(self,folder_path):
        Top_image_Path_List=sorted(glob(folder_path+'/raw/*Cross_Lane_top_image*'))
        Top_image_List=[]
        Top_image_name_list=[]
        distance_in_pixels=[]
        Axel_count_list=[]
        Axel_count=0
        
        for top_image_path in Top_image_Path_List:
            Top_image_name_list.append(top_image_path.split('/')[-1])
            top_image=cv2.imread(top_image_path)
            Top_image_List.append(top_image)
        
        if len(Top_image_Path_List)>0:
            Axel_count,Axel_count_list,distance_in_pixels,Vehicle_Crop,Top_Pred_image_list=self.Top_obj.main(Top_image_name_list,Top_image_List)
            if len(Top_Pred_image_list)>0:
                self.save_top_prediction(folder_path,Top_Pred_image_list)
            if len(Vehicle_Crop)>0:
                self.save_top_crop(folder_path,Vehicle_Crop)
            

        else:
            Axel_count,distance_in_pixels=[],[]
            

        
        return Axel_count,Axel_count_list,distance_in_pixels

        


        

    def find_files_created_within_last_minute(self,folder_path):
        current_time = datetime.datetime.now()
        one_minute_ago = current_time - datetime.timedelta(minutes=20)
        recent_files = []
        # print('folder_path : ',folder_path)
        for file_path in glob(folder_path):
            # print('file_path : ',file_path)
            if os.path.exists(file_path+'/json/Front_Top_output.json') and \
                os.path.exists(file_path+'/json/Sync_ANPR_TOP_output.json') and \
                not os.path.exists(file_path+'/json/Top_CrossLane_Detection_output.json') and \
                not os.path.exists(file_path+'/json/response.json'):
                # print('file_path : ',file_path)
                creation_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
                if creation_time > one_minute_ago:
                    recent_files.append(file_path)
            # else:
            #     print('File not exist : ',file_path)

        return recent_files   

    def inferance(self,folder_path):
        print('Top Detection inferance folder_path : ',folder_path)
        start=time.time()
        Front_Top_output_json_path=folder_path+'/json/Front_Top_output.json'
        Top_Detection_output_json_path=folder_path+'/json/Top_CrossLane_Detection_output.json'
        
        if os.path.exists(Front_Top_output_json_path):
            with open(Front_Top_output_json_path) as json_file:
                json_data = json.load(json_file)
            # print('json_data : ',json_data)
            Top_Analysis_data={}
            Top_Analysis_data['transactionId']=json_data['id']
            Top_Analysis_data['datetime']=json_data['datetime']
            Top_Analysis_data['Top_Class']=json_data['top_class_name'],
            Top_Analysis_data['Axel_count']=[]
            Top_Analysis_data['distance_in_pixels']=[]#{image_name : distance_in_pixels}
            Top_Analysis_data['Axel_count_list']=[] #{image_name : Axel_count_list}
            Top_Analysis_data['Axel_count'],Top_Analysis_data['Axel_count_list'],Top_Analysis_data['distance_in_pixels']=self.Top_CrossLane_Start(folder_path)
            
            Top_Analysis_data['inferance_time']=f'{round(time.time()-start,2)}'
            print(json_data['id'],' : ',' Axel_count: ',Top_Analysis_data['Axel_count'],' distance_in_pixels: ',Top_Analysis_data['distance_in_pixels'],' : ',Top_Analysis_data['inferance_time'])
            with open(Top_Detection_output_json_path, 'w') as f:
                json.dump(Top_Analysis_data, f)
        else:
            print('Top Detection File not found Front_Top_output_json_path')

    def main(self):
        
        folder_path = config.root_path+'/output/*2026*'
        print('folder_path : ',folder_path)
        while True:
            
            recent_files = self.find_files_created_within_last_minute(folder_path)
            # print("last 20 minute count:",len(recent_files))
            for file_path in recent_files:
                # self.inferance(file_path)
                try:
                    self.inferance(file_path)
                except Exception as e:
                    if config.check_error:
                        print('Cross Lane Inferance : ',e)
                    continue
                # break
            # break

            time.sleep(1)
        

if __name__ == "__main__":
    main_obj=main()
    main_obj.main()
            
