import sys
sys.path.append('/home/aikernel/metadata')
import master_config 
import torch
import torch.nn.functional as F
import numpy as np
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from torch.utils.data import Dataset, DataLoader
import torch.nn as nn
# from model import model as mineral_classification_model
from tqdm import tqdm
import albumentations as A
from PIL import Image
from glob import glob
import cv2
import datetime
import time
import os
import json
import torchvision.models as models
from configs import config
import shutil
import logging
from custom_utils.save_json import save_json
# Load the saved model
# Set device

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# source_path=config.root_path+'/src/weights/'
source_path=config.root_path+'/metadata/weights/'

now = datetime.datetime.now()
start_script_datetime=now.strftime("%d_%m_%Y_%H_%M")

Current_log_path=config.root_path+f"/logs/Mineral_Classification_Logs.log"
backup_logs_path=config.root_path+f"/logs/Mineral_Classification_Logs/"
os.makedirs(backup_logs_path,exist_ok=True)
if os.path.exists(Current_log_path):
    shutil.move(Current_log_path,backup_logs_path+f"Mineral_Classification_Logs_{start_script_datetime}.log")

FORMAT = "%(asctime)s: %(filename)s: %(levelname)s :%(lineno)5s:: - %(funcName)10s() :  %(message)s"
logging.basicConfig(filename=Current_log_path,
                    format=FORMAT,
                    filemode='a',
                    level=logging.DEBUG, # Set logging level
                    force=True)

class CustomResNet(nn.Module):
    def __init__(self):
        super(CustomResNet, self).__init__()
        self.resnet = models.resnet18(pretrained=True)
        self.resnet.conv1 = nn.Conv2d(3, 64, kernel_size=(7, 7), stride=(2, 2), padding=(3, 3), bias=False)

    def forward(self, x):
        return self.resnet(x)


Location_ID=int(master_config.LocationId)   
Local_Mineral_Classification_Model_Path_List=glob(source_path+f'/MP_Minerla_Classification_{str(Location_ID)}_**.pth')


class mineral_classification():
    def __init__(self) -> None:
        self.load_model()
        self.aug_pad=A.PadIfNeeded(min_height=224, min_width=512,value=0,p=1.0)
    def load_model(self):
        model=CustomResNet()
        num_ftrs = model.resnet.fc.in_features
        
        
        if len(Local_Mineral_Classification_Model_Path_List)>0:
            Local_Mineral_Classification_Model_Path=Local_Mineral_Classification_Model_Path_List[0]
            print('Local_Mineral_Classification_Model_Path : ',Local_Mineral_Classification_Model_Path)
            if Local_Mineral_Classification_Model_Path!='':
                Local_Mineral_Classification_Json_Path=glob(config.root_path+f'/metadata/MP_Minerla_Classification_{str(Location_ID)}_**.json')[0]
                if Local_Mineral_Classification_Json_Path!='' and os.path.exists(Local_Mineral_Classification_Json_Path):
                    with open(Local_Mineral_Classification_Json_Path) as f:
                        self.Local_Mineral_Classification_Json_Data = json.load(f)
                        print("Local_Mineral_Classification_Json_Data : ",self.Local_Mineral_Classification_Json_Data)
                        
                        print('Mineral Classification Local Json Found and Loaded....')
                        logging.info('Mineral Classification Local Json Found and Loaded....')
                    
                    model.resnet.fc = nn.Linear(num_ftrs, len(self.Local_Mineral_Classification_Json_Data)) 
                    Pretrain_path=Local_Mineral_Classification_Model_Path
                    save_json('/home/aikernel/metadata/loaded_model/','Mineral_Classification.json',{'model':Pretrain_path})  
                    model.load_state_dict(torch.load(Pretrain_path,map_location=device))
                    
                    print('Local Mineral Classification Model Loaded')
                    logging.info('Local Mineral Classification Model Loaded Successfully.....')

                else:
                    print('Mineral Classification Local Json Not Found....')
                    logging.info('Mineral Classification Local Json Not Found....')

        else:
            
            model.resnet.fc = nn.Linear(num_ftrs, len(config.mineral_classes)) 
            #Pretrain_path=source_path+'/best_71_prec0.96_rec0.96_acc0.96_val0.96.pth'
            # Pretrain_path=source_path+'/best_02042024_50_prec0.97_rec0.97_acc0.97_val0.98.pth'
            Pretrain_path=source_path+'/MP_Minerla_Classification_21102024_89_prec0.96_rec0.96_acc0.96_val1.0.pth'  
            save_json('/home/aikernel/metadata/loaded_model/','Mineral_Classification.json',{'model':Pretrain_path}) 


            model.load_state_dict(torch.load(Pretrain_path,map_location=device))
            print('Global Mineral Classification Model Loaded')
            logging.info('Global Mineral Classification Model Loaded Successfully.....')

        self.mineral_classification_model=model.cuda()
        self.mineral_classification_model.eval()
        
        print('Mineral Classification Model Loaded On Cuda')
        logging.info('Mineral Classification Model Loaded Successfully On Cuda.....')

    def add_aug_pad(self,image):
        return self.aug_pad(image=image)['image']
    
    def resize_or_pad_image(self,image):
        # desired_width, desired_height = 512, 224
        desired_width, desired_height = 640, 416

        # with Image.open(input_image_path) as img:
        #     img_width, img_height = img.size
        img_height,img_width,_=image.shape
        img = Image.fromarray(image)

            # If the image is larger than the desired size, resize it.
        if img_width > desired_width or img_height > desired_height:
            img = img.resize((desired_width, desired_height), Image.Resampling.LANCZOS)

        
        # If the image is smaller than the desired size, pad it.
        else:
            # Calculate padding sizes
            horizontal_padding = (desired_width - img_width) / 2
            vertical_padding = (desired_height - img_height) / 2

            # Ensure padding sizes are integer values
            left_pad = int(np.floor(horizontal_padding))
            right_pad = int(np.ceil(horizontal_padding))
            top_pad = int(np.floor(vertical_padding))
            bottom_pad = int(np.ceil(vertical_padding))

            # Create a new image with the desired size and black background
            # and paste the original image onto the center
            new_img = Image.new("RGB", (desired_width, desired_height), (0, 0, 0))
            new_img.paste(img, (left_pad, top_pad))

            img = new_img

        img=np.array(img)
        
        return img
    
    def main_mineral_classification(self,image_crop):

        # print('image_crop.shape : ',image_crop.shape)
        padded_image=self.resize_or_pad_image(image_crop)
        # print('padded_image.shape : ',padded_image.shape)
        # cv2.imwrite('padded_image.png',padded_image)
        
        # padded_image=cv2.cvtColor(padded_image, cv2.COLOR_BGR2RGB)
        
        padded_image=np.transpose(padded_image, (2, 0, 1))
        padded_image=padded_image/255.0
        padded_image=np.array([padded_image])
        img_tensor = torch.FloatTensor(padded_image)
        # print('img_tensor : ',img_tensor.size())

        img_tensor = img_tensor.to(device)

        outputs = self.mineral_classification_model(img_tensor)
        # print('outputs : ',outputs)
        _, predicted = torch.max(outputs, 1)
        predicted_class=predicted.cpu().numpy()[0]
        # print('Final Prediction : ',mineral_classes[predicted_class])
        if len(Local_Mineral_Classification_Model_Path_List)>0:
            return self.Local_Mineral_Classification_Json_Data[str(predicted_class)]
        else:
            return config.mineral_classes[predicted_class]

class main():
    def __init__(self) -> None:
        self.mineral_classification_obj=mineral_classification()

    def mineral_classification_def(self,path):
        mineral_classification_pred_list=[]
        mineral_classification_pred_list_valid=[]
        final_mineral_class='Not_Found'
        final_mineral_class_Valid='Not_Found'
        
        image_crop_path=glob(path+'/top_crop/**')
        image_crop_path_valid=glob(path+'/top_crop/Top_Camera_Valid**')
        for image_path in image_crop_path:
            image=cv2.imread(image_path)
            result=self.mineral_classification_obj.main_mineral_classification(image)
            mineral_classification_pred_list.append(result)
        for image_path in image_crop_path_valid:
            image=cv2.imread(image_path)
            result=self.mineral_classification_obj.main_mineral_classification(image)
            mineral_classification_pred_list_valid.append(result)

        if len(mineral_classification_pred_list)>0:
            final_mineral_class=max(mineral_classification_pred_list,key=mineral_classification_pred_list.count)
            
        if len(mineral_classification_pred_list_valid)>0:
            final_mineral_class_Valid=max(mineral_classification_pred_list_valid,key=mineral_classification_pred_list_valid.count)
        

        return final_mineral_class,mineral_classification_pred_list,final_mineral_class_Valid,mineral_classification_pred_list_valid
        

    def find_files_created_within_last_minute(self,folder_path):
        current_time = datetime.datetime.now()
        one_minute_ago = current_time - datetime.timedelta(minutes=2000)
        recent_files = []
        # print('folder_path : ',folder_path)
        for file_path in glob(folder_path):
            try:
                if os.path.exists(file_path+'/json/Front_Top_output.json') and \
                    os.path.exists(file_path+'/json/Top_Detection_output.json') and \
                    os.path.exists(file_path+'/json/Sync_ANPR_TOP_output.json') and \
                    not os.path.exists(file_path+'/json/Mineral_output.json') and \
                    not os.path.exists(file_path+'/json/response.json'):
                    # print('file_path : ',file_path)
                    creation_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
                    if creation_time > one_minute_ago:
                        recent_files.append(file_path)
                # else:
                #     print('File not exist : ',file_path)
            except Exception as e:
                continue

        return recent_files   
    def check_time(self,current_time):
        day_start = 6
        day_end = 18
        current_hour = current_time.hour
        if day_start <= current_hour < day_end:
            return 'day'
        else:
            return 'night'
    def filter_mining_full_vehicles(self,folder_path):
        # print(folder_path)
        start=time.time()
        ANPR_json_path=folder_path+'/json/Front_Top_output.json' # Day time
        Top_Detection_json_path=folder_path+'/json/Top_Detection_output.json' # Night time
        
        Mineral_json_path=folder_path+'/json/Mineral_output.json'

        current_time = datetime.datetime.now()
        top_class_name='Not_Found'
        top_class_name_Top_Camera_valid='Not_Found'
        mineral_data={
            'transactionId':-1,
            'datetime':"",
            'material':"Not_Found",
            'inferance_time':-1,
            
        }
        top_class_name_ANPR_Camera=""
        top_class_name_Top_Camera=""

        # if self.check_time(current_time)=='day':
        if os.path.exists(ANPR_json_path):
            with open(ANPR_json_path) as json_file:
                json_data = json.load(json_file)
            
            mineral_data['transactionId']=json_data['id']
            mineral_data['datetime']=json_data['datetime']
            top_class_name_ANPR_Camera=json_data['top_class_name']
            mineral_data['material'],mineral_data['Raw_material_list']='',[]
            mineral_data['material_valid'],mineral_data['Raw_material_list_valid']='',[]
        else:
            mineral_data['inferance_time']=f'{round(time.time()-start,2)}'
            
        
        if os.path.exists(Top_Detection_json_path):
            with open(Top_Detection_json_path) as json_file:
                json_data = json.load(json_file)
            mineral_data['transactionId']=json_data['transactionId']
            top_class_name_Top_Camera=json_data['Top_Class']
            if 'Top_Class_Valid' in json_data.keys(): 
                top_class_name_Top_Camera_valid=json_data['Top_Class_Valid']
            mineral_data['material'],mineral_data['Raw_material_list']='',[]
            mineral_data['material_valid'],mineral_data['Raw_material_list_valid']='',[]

        else:
            mineral_data['inferance_time']=f'{round(time.time()-start,2)}'
            
                
        # if top_class_name_ANPR_Camera=='mining_full' or top_class_name_Top_Camera=='mining_full':
        if top_class_name_Top_Camera_valid=='mining_full' or top_class_name_Top_Camera=='mining_full':
            mineral_data['material'],mineral_data['Raw_material_list'],mineral_data['material_valid'],mineral_data['Raw_material_list_valid']=self.mineral_classification_def(folder_path)
            mineral_data['inferance_time']=f'{round(time.time()-start,2)}'
            
        print(mineral_data['transactionId'],' : ',mineral_data['material'],' : ',mineral_data['inferance_time'])
        logging.info(f"TransactionId  : {str(json_data['transactionId'])}:{mineral_data['material']} : {mineral_data['inferance_time']}")
            
        with open(Mineral_json_path, 'w') as f:
            json.dump(mineral_data, f)

    def main(self):
        # self.get_mineral_class_config()
        folder_path = config.root_path+'/output/*2026*'
        
        while True:
            
            recent_files = self.find_files_created_within_last_minute(folder_path)
            # print("last minute count:",len(recent_files))
            for file_path in recent_files:
                try:   
                    
                    # print('file_path : ',file_path) 
                    # time.sleep(1)
                    logging.info('Process Started file_path : '+str(file_path))
                    
                    self.filter_mining_full_vehicles(file_path)
                except Exception as e:
                    logging.error('Process error file_path : '+str(file_path)+' : '+str(e))
                    if 'Input/output error' in  str(e):
                        logging.error('Mineral_Classification_Inference_Script code Error : Mineral_Classification_Inference_Script.py  Restarted')
                        os.execv(sys.executable, ['python3'] + sys.argv)
                
                    if config.check_error:
                        print("Mineral Classification : ",e)
                    
                    continue
            # break
            time.sleep(1)
if __name__=='__main__':
    main().main()

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
