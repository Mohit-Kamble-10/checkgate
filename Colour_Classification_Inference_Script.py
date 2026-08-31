import sys
import torch
import torch.nn.functional as F
import numpy as np
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from torch.utils.data import Dataset, DataLoader
import torch.nn as nn
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
import logging
import shutil
from custom_utils.save_json import save_json

# Load the saved model
# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# source_path=config.root_path+'/src/weights/'
source_path=config.master_jsons+'/weights/'

now = datetime.datetime.now()
start_script_datetime=now.strftime("%d_%m_%Y_%H_%M")

Current_log_path=config.root_path+f"/logs/Colour_Classification_Logs.log"
backup_logs_path=config.root_path+f"/logs/Colour_Classification_Logs/"
os.makedirs(backup_logs_path,exist_ok=True)
if os.path.exists(Current_log_path):
    shutil.move(Current_log_path,backup_logs_path+f"Colour_Classification_Logs_{start_script_datetime}.log")

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



model=CustomResNet()
num_ftrs = model.resnet.fc.in_features
model.resnet.fc = nn.Linear(num_ftrs, len(config.colour_classes)) 


class colour_classification():
    def __init__(self) -> None:
        self.load_model()
        self.aug_pad=A.PadIfNeeded(min_height=64, min_width=192,value=0,p=1.0)
    def load_model(self):

        Pretrain_path=source_path+'/Bonnet_08072024.pth'      
        save_json('/home/aikernel/metadata/loaded_model/','Colour_Classification.json',{'model':Pretrain_path})  
        model.load_state_dict(torch.load(Pretrain_path,map_location=device))
        self.colour_classification_model=model.cuda()
        self.colour_classification_model.eval()
        
        print('Colour Classification Model Loaded')

        logging.info('Colour Classification Model Loaded Successfully.....')


    def add_aug_pad(self,image):
        return self.aug_pad(image=image)['image']
    
    def resize_or_pad_image(self,image):
        desired_width, desired_height = 192, 64

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
    
    def main_colour_classification(self,image_crop):

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

        outputs = self.colour_classification_model(img_tensor)
        # print('outputs : ',outputs)
        _, predicted = torch.max(outputs, 1)
        predicted_class=predicted.cpu().numpy()[0]
        return config.colour_classes[predicted_class]

class main():
    def __init__(self) -> None:
        self.colour_classification_obj=colour_classification()

    def colour_classification_def(self,path):
        colour_classification_pred_list=[]
        final_colour_class='Not_Found'

        image_crop_path=glob(path+'/processed/*bonnet*')
        if len(image_crop_path)>0:
            for image_path in image_crop_path:
                image=cv2.imread(image_path)
                result=self.colour_classification_obj.main_colour_classification(image)
                colour_classification_pred_list.append(result)
            if len(colour_classification_pred_list)>0:
                final_colour_class=max(colour_classification_pred_list,key=colour_classification_pred_list.count)
        return final_colour_class,colour_classification_pred_list
        

    def find_files_created_within_last_minute(self,folder_path):
        current_time = datetime.datetime.now()
        one_minute_ago = current_time - datetime.timedelta(minutes=2000)
        recent_files = []
        # print('folder_path : ',folder_path)
        for file_path in glob(folder_path):
            if os.path.exists(file_path+'/json/Front_Top_output.json') and \
             os.path.exists(file_path+'/json/Top_Detection_output.json') and \
                not os.path.exists(file_path+'/json/Colour_output.json') and \
                not os.path.exists(file_path+'/json/response.json'):
                # print('file_path : ',file_path)
                creation_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
                if creation_time > one_minute_ago:
                    recent_files.append(file_path)
            # else:
            #     print('File not exist : ',file_path)

        return recent_files   

    def filter_mining_full_vehicles(self,folder_path):
        # print(folder_path)
        start=time.time()
        ANPR_json_path=folder_path+'/json/Front_Top_output.json'
        colour_json_path=folder_path+'/json/Colour_output.json'
        
        if os.path.exists(ANPR_json_path):
            with open(ANPR_json_path) as json_file:
                json_data = json.load(json_file)
            colour_data={}
            colour_data['transactionId']=json_data['id']
            colour_data['datetime']=json_data['datetime']
            # colour_data['top_class_name']=json_data['top_class_name']
            colour_data['colour'],colour_data['Raw_colour_list']='',[]
            colour_data['inferance_time']=f'{round(time.time()-start,2)}'
            
            # if json_data['top_class_name']=='mining_full':
            colour_data['colour'],colour_data['Raw_colour_list']=self.colour_classification_def(folder_path)
            colour_data['inferance_time']=f'{round(time.time()-start,2)}'
            
            print(json_data['id'],' : ',colour_data['colour'],' : ',colour_data['inferance_time'])
            logging.info(f"TransactionId  : {str(json_data['id'])}:{colour_data['colour']} : {colour_data['inferance_time']}")
            
            with open(colour_json_path, 'w') as f:
                json.dump(colour_data, f)
    
    def main(self):
        folder_path = config.root_path+'/output/*2026*'
        
        while True:
            
            recent_files = self.find_files_created_within_last_minute(folder_path)
            # print("colour classification count:",len(recent_files))
            for file_path in recent_files:
                try:   
                    
                    # print('file_path : ',file_path) 
                    # time.sleep(2)
                    logging.info('Process Started file_path : '+str(file_path))
                    
                    self.filter_mining_full_vehicles(file_path)
                except Exception as e:
                    logging.error('Process error file_path : '+str(file_path)+' : '+str(e))
                    if 'Input/output error' in  str(e):
                        logging.error('Colour_Classification_Inference_Script code Error : Colour_Classification_Inference_Script.py  Restarted')
                        os.execv(sys.executable, ['python3'] + sys.argv)
                
                    if config.check_error:
                        print('Colour Classifcation Script : ',e)
                    continue
            # break
            time.sleep(1)

if __name__=='__main__':
    main().main()
    # folder_path='/home/shaurya/output/IND0004270720240100324/'
    # main().filter_mining_full_vehicles(folder_path)


