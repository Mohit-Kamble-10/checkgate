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


class Top_Prediction():
    def __init__(self,lane_id) -> None:
        self.yolo_pred=yolo_pred(lane_id,image_type='TOP')
        print('Top Model Loaded...')

    
    
    def main(self,mapping,Top_image_name_list,image_List,lane_id):
        Top_Class_dict_list=[]
        Front_Class_dict_list=[]
        Top_image_crop_dict_list=[]
        Bonnet_crop_dict_list=[]
        Top_Pred_image_dict_list=[]
        Top_Class_List=[]
        Front_Class_List=[]
        Top_Class='Not_Found'
        Front_Class='Not_Found'
        
        for index,image in enumerate(image_List):
            top_output=self.yolo_pred.Top_main(image,lane_no=lane_id)
            image_name=Top_image_name_list[index]
            # print("image_name : ",image_name)
            mapping[image_name]={
                "Status":'Empty',
                "Front_Class":'Empty',
                "Top_Class":'Empty',
                "Mineral_Crop_Path":"Empty",
                "Bonnet_Crop_Path":"Empty",
                "Prediction_image_Path":"Empty"
            }

            if top_output['Status']==0:
                mapping[image_name]["Status"]=0
                
                top_pred_image=top_output['Return_Disply_Frame'][0]
                # print("top_pred_image.shape : ",top_pred_image.shape)
                Top_Pred_image_dict_list.append({image_name:top_pred_image})

                Front_Class_Predicted=top_output['Front_Class']
                
                
                if Front_Class_Predicted!='':
                    Front_Class_dict_list.append({image_name:Front_Class_Predicted})
                    mapping[image_name]["Front_Class"]=Front_Class_Predicted
                    Front_Class_List.append(Front_Class_Predicted)
                else:
                    mapping[image_name]["Front_Class"]="Not_Found"
                    
                if len(top_output['Raw_Top_Category_List'])>0:
                    
                    Top_Class_Predicted=top_output['Raw_Top_Category_List'][0]
                    Top_Class_List.append(Top_Class_Predicted)
                    Top_Class_dict_list.append({image_name:Top_Class_Predicted})
                    mapping[image_name]["Top_Class"]=Top_Class_Predicted
                else:
                    
                    mapping[image_name]["Top_Class"]="Not_Found"
                    

                if len(top_output['Raw_Mining_Full_Crop_List'])>0:
                    for mining_full_crop in top_output['Raw_Mining_Full_Crop_List']:
                        Top_image_crop_dict_list.append({image_name:mining_full_crop})

                    
                if top_output['Bonnet_Crop_Found']:
                    for bonnet_crop in top_output['Bonnet_Crop_List']:
                        Bonnet_crop_dict_list.append({image_name:bonnet_crop})

            else:
                mapping[image_name]["Status"]=1

        if len(Top_Class_List)>0:
            Top_Class=max(Top_Class_List,key=Top_Class_List.count)
        if len(Front_Class_List)>0:
            Front_Class=max(Front_Class_List,key=Front_Class_List.count)
        # print("mapping : ",mapping)
        return Top_Class,Top_Class_dict_list,Top_Class_List,Front_Class,Front_Class_dict_list,Front_Class_List,\
            Bonnet_crop_dict_list,Top_Pred_image_dict_list,Top_image_crop_dict_list,mapping
    

class main():
    def __init__(self) -> None:
        self.Top_obj=Top_Prediction(lane_id=None)

    def save_bonnet_image(self,folder_path,bonnet_image_list_dict,mapping_top_obj_output):
        # mapping_top_obj_output['bonnet_crop']=[]
        dest_path=folder_path+'/processed/'
        for dict_data in bonnet_image_list_dict:
            # print("dict_data : ",dict_data)
            for image_name,image_crop in dict_data.items():
                path=dest_path+f'/bonnet_crop_{image_name}'
                cv2.imwrite(path,cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB))
                mapping_top_obj_output[image_name]["Bonnet_Crop_Path"]=path
        return mapping_top_obj_output

    def save_top_prediction(self,folder_path,Top_image_name_dict,mapping_top_obj_output):
        # mapping_top_obj_output['top_prediction']=[]
        dest_path=folder_path+'/prediction/'
        for dict_data in Top_image_name_dict:
            for image_name,image_pred in dict_data.items():
                path=dest_path+f'/pred_{image_name}'
                # cv2.imwrite(path,cv2.cvtColor(image_pred, cv2.COLOR_BGR2RGB))
                cv2.imwrite(path,image_pred)
                # mapping_top_obj_output['top_prediction'].append({image_name:path})
                mapping_top_obj_output[image_name]["Prediction_image_Path"]=path
        return mapping_top_obj_output
        
    def save_top_crop(self,folder_path,Top_image_crop_dict,mapping_top_obj_output):
        dest_path=folder_path+'/top_crop/'
        # for i in range(len(Top_image_crop_list)):
        for dict_data in Top_image_crop_dict:
            for image_name,image_crop in dict_data.items():
                # cv2.imwrite(dest_path+f'/Top_Camera_{Top_image_name_list[i]}',cv2.cvtColor(Top_image_crop_list[i], cv2.COLOR_BGR2RGB))
                path=dest_path+f'/Top_Camera_{image_name}'
                cv2.imwrite(path,cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB))
                # mapping_top_obj_output['mineral_crop'].append({image_name:path})
                mapping_top_obj_output[image_name]["Mineral_Crop_Path"]=path
        return mapping_top_obj_output



    
    def Top_Start(self,folder_path,lane_no):
        Top_image_Path_List=sorted(glob(folder_path+'/raw/*top_image*'))
        Top_image_List=[]
        Top_image_name_list=[]
        mapping={}
        Raw_Top_List=[]
        Raw_Front_List=[]
        Bonnet_Crop_List=[]
        mapping={}
        Raw_Top_dict={}
        Raw_Front_dict={}
        Bonnet_Crop_dict={}
        mapping_top_obj_output={}


        
        for top_image_path in Top_image_Path_List:
            if 'Cross_Lane_' not in top_image_path:
                Top_image_name_list.append(top_image_path.split('/')[-1])
                top_image=cv2.imread(top_image_path)
                Top_image_List.append(top_image)
        
        if len(Top_image_Path_List)>0:
            Top_Class,Raw_Top_dict,Raw_Top_List,Front_Class,Raw_Front_dict,Raw_Front_List,Bonnet_Crop_dict,Top_Pred_image_dict,\
            Top_image_crop_dict,mapping_top_obj_output=self.Top_obj.main(mapping,Top_image_name_list,Top_image_List,lane_no)
            if len(Bonnet_Crop_dict)>0:
                mapping_top_obj_output=self.save_bonnet_image(folder_path,Bonnet_Crop_dict,mapping_top_obj_output)
            if len(Top_Pred_image_dict)>0:
                mapping_top_obj_output=self.save_top_prediction(folder_path,Top_Pred_image_dict,mapping_top_obj_output)
            if len(Top_image_crop_dict)>0:
                mapping_top_obj_output=self.save_top_crop(folder_path,Top_image_crop_dict,mapping_top_obj_output)
            

        else:
            Top_Class,Raw_Top_List,Front_Class,Raw_Front_List,Bonnet_Crop_List,Top_Pred_image_list,Top_image_crop_list='Not_Found',[],'Not_Found',[],[],[],[]
        # print("Raw_Top_dict :",Raw_Top_dict)
        # print("Raw_Front_dict :",Raw_Front_dict)
        # print("Bonnet_Crop_dict :",Bonnet_Crop_dict)
        
        # Raw_Top_List=self.extract_data_from_json(Raw_Top_dict)
        # Raw_Front_List=self.extract_data_from_json(Raw_Front_dict)
        # Bonnet_Crop_List=self.extract_data_from_json(Bonnet_Crop_dict)
        # print('Top_Class : ',Top_Class)
        return Top_Class,Raw_Top_List,Front_Class,Raw_Front_List,Bonnet_Crop_List,mapping_top_obj_output
        

    def find_files_created_within_last_minute(self,folder_path):
        current_time = datetime.datetime.now()
        one_minute_ago = current_time - datetime.timedelta(minutes=2000)
        recent_files = []
        # print('folder_path : ',folder_path)
        for file_path in glob(folder_path):
            # print('file_path : ',file_path)
            if os.path.exists(file_path+'/json/Front_Top_output.json') and \
                os.path.exists(file_path+'/json/Sync_ANPR_TOP_output.json') and \
                not os.path.exists(file_path+'/json/Top_Detection_output.json') and \
                not os.path.exists(file_path+'/json/response.json'):
            # if os.path.exists(file_path+'/json/Front_Top_output.json') and \
            #     not os.path.exists(file_path+'/json/Top_Detection_output_dev.json') and \
            #     not os.path.exists(file_path+'/json/response.json'):
            #     # print('file_path : ',file_path)
                creation_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
                if creation_time > one_minute_ago:
                    recent_files.append(file_path)
            # else:
            #     print('File not exist : ',file_path)

        return recent_files   

    def inferance(self,folder_path,non_mining=False):
        lane_no=int(folder_path.split('/')[-1][15:17])
        print('Top Detection inferance folder_path : ',folder_path)
        start=time.time()
        Front_Top_output_json_path=folder_path+'/json/Front_Top_output.json'
        Top_Detection_output_json_path=folder_path+'/json/Top_Detection_output.json'
        
        if os.path.exists(Front_Top_output_json_path):
            with open(Front_Top_output_json_path) as json_file:
                json_data = json.load(json_file)
            # print('json_data : ',json_data)
            Top_Analysis_data={}
            Top_Analysis_data['transactionId']=json_data['id']
            Top_Analysis_data['datetime']=json_data['datetime']
            Top_Analysis_data['Top_Class']=json_data['top_class_name'],
            Top_Analysis_data['Raw_Top_List']=[]
            Top_Analysis_data['Front_Class']=json_data['front_class_name'], 
            Top_Analysis_data['Raw_Front_List']=[]
            Top_Analysis_data['mapping']={}
            
            

            if non_mining==False:
                Top_Analysis_data['Top_Class'],Top_Analysis_data['Raw_Top_List'],Top_Analysis_data['Front_Class'],\
                    Top_Analysis_data['Raw_Front_List'],Bonnet_Crop_List,Top_Analysis_data['mapping']=self.Top_Start(folder_path,lane_no)
                
            Top_Analysis_data['inferance_time']=f'{round(time.time()-start,2)}'
            print(json_data['id'],' : ',Top_Analysis_data['Front_Class'],' : ',Top_Analysis_data['Top_Class'],' : ',Top_Analysis_data['inferance_time'])
            # print("Top_Analysis_data :",Top_Analysis_data)
            with open(Top_Detection_output_json_path, 'w') as f:
                json.dump(Top_Analysis_data, f)
        else:
            print('Top Detection File not found Front_Top_output_json_path')

    def main(self):
        
        folder_path = config.root_path+'/output/*2026*'
        print('folder_path : ',folder_path)
        # self.inferance('/home/aikernel/output/IND0041191020240101269')
        while True:
            
            recent_files = self.find_files_created_within_last_minute(folder_path)
            # print("last 20 minute count:",len(recent_files))
            for file_path in recent_files:
                self.inferance(file_path)
                try:
                    time.sleep(2)
                    self.inferance(file_path)
                except Exception as e:
                    print(e)
                    continue
                # break
            # break

            # time.sleep(1)
if __name__=='__main__':
    main().main()
    # main().inferance('/home/shaurya/output/IND0001210820240101197',lane_no=1)

# if __name__=='__main__':
#     image_paths=glob('/home/linux/DeepLearning/Uday/MP_AVDR/model_training/Mineral_Classification/support_data/training_data_original/train_224_512/**/**/**')
#     mineral_classification_obj=mineral_classification()
#     for image_path in image_paths:
#         # print(image_path)
#         #image_path='/home/linux/DeepLearning/Uday/MP_AVDR/model_training/Mineral_Classification/support_data/training_data_original/train/1_12March_Mineral_Classification/Murum/IND0002070320240101186_Anpr_Raw_6_11.png'
#         #image_path='/home/linux/DeepLearning/Uday/MP_AVDR/model_training/Mineral_Classification/support_data/training_data_original/train/13_14March_Mineral_Classification/Soil/IND0002140320240102157_Anpr_Raw_5_11.png'
#         image_path='/home/linux/DeepLearning/Uday/MP_AVDR/model_training/Mineral_Classification/support_data/training_data_original/train/13_14March_Mineral_Classification/Stone/IND0002130320240100941_Anpr_Raw_5_11.png'
#         image=cv2.imread(image_path)
#         mineral_classification_obj.main_mineral_classification(image)
#         break
