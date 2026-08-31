import torch
from PIL import Image
# from torchvision import transforms
from strhub.data.module import SceneTextDataModule
from glob import glob
from fuzzywuzzy import fuzz
import pandas as pd
import os
import cv2
import numpy as np
import albumentations as A
from torch import Tensor
from torch.nn.utils.rnn import pad_sequence
from typing import List, Optional, Tuple
os.environ["CUDA_VISIBLE_DEVICES"]="0"
font                   = cv2.FONT_HERSHEY_SIMPLEX
bottomLeftCornerOfText = (800,200)
fontScale              = 2
fontColor              = (0,255,0)
thickness              = 3
lineType               = 2


cuda_available=torch.cuda.is_available()


def recog_main_folder():
    paths=glob('../data/crops_folder/**')
    print('len(paths) : ',len(paths))

    data=[]
    for folder_path in paths:
        pred_number_plate=''
        image_paths=glob(folder_path+'/*rotated*')
        for i in range(len(image_paths)):
            image_path=glob(folder_path+f'/*{str(i)}_rotated*')[0]
            image_name=image_path.split('/')[-1]
            gt=image_name.split('-')[0]
            img = Image.open(image_path).convert('RGB')
            # Preprocess. Model expects a batch of images with shape: (B, C, H, W)
            img = img_transform(img).unsqueeze(0)

            logits = parseq(img)
            logits.shape  # torch.Size([1, 26, 95]), 94 characters + [EOS] symbol

            # Greedy decoding
            pred = logits.softmax(-1)
            label, confidence = parseq.tokenizer.decode(pred)
            pred_number=label[0]
            pred_number_plate+=pred_number

        pred_number_processed=''.join(e for e in pred_number_plate if e.isalnum())
        match_ratio=fuzz.ratio(pred_number_processed,gt)
        print(image_name,' => {}, {}'.format(pred_number_processed,pred_number_plate),match_ratio)
        data.append({'image_name':image_name,'pred_number_processed':pred_number_processed,'pred_number':pred_number_plate,'match':match_ratio})
        # break
    pd.DataFrame(data).to_csv('../data/NP_Recognition/recognition.csv',index=False)
# recog_main()

def recog_main_xlsx():

    dataframe=pd.read_excel('../data/csvs/ANPR_Analysis_1.xlsx')
    final_list=[]
    for k, row_data in dataframe.iterrows():
        # print('row_data : \n',row_data)
        org_image_path=row_data['Image_Path']
        org_image=cv2.imread(org_image_path)
        org_image_name=org_image_path.split('/')[-1]
        final_list.append(row_data)
        pred_number_plate_lst=[]
        pred_number_processed_lst=[]
        match_ratio_lst=[]
        craft_crop_path_data=row_data['craft_crop_paths']
        

        gt=org_image_name.split('-')[0]
        # print('gt : ',gt)
        gt=update_gt(gt)
        row_data['Ground_Truth']=gt
        # print('image_path_list : ',craft_crop_path_data)
        if type(craft_crop_path_data)!=str:
            continue
        image_path_list=craft_crop_path_data.split('&&')#.to_list()[0]
        
        for image_paths in image_path_list:
            pred_number_plate=''
            
            # image_paths=glob(folder_path+'/*rotated*')
            for image_path in image_paths.split(','):
                # print('image_path : ',image_path)
                if len(image_path)<=1:
                    continue
                # image_path=glob(folder_path+f'/*{str(i)}_rotated*')[0]
                # image_name=image_path.split('/')[-1]
                
                img = Image.open(image_path).convert('RGB')
                # Preprocess. Model expects a batch of images with shape: (B, C, H, W)
                img = img_transform(img).unsqueeze(0)

                logits = parseq(img)
                logits.shape  # torch.Size([1, 26, 95]), 94 characters + [EOS] symbol

                # Greedy decoding
                pred = logits.softmax(-1)
                label, confidence = parseq.tokenizer.decode(pred)
                pred_number=label[0]
                pred_number_plate+=pred_number

            pred_number_plate_lst.append(pred_number_plate)
            pred_number_processed=''.join(e for e in pred_number_plate if e.isalnum())
            pred_number_processed_lst.append(pred_number_processed)
            match_ratio=fuzz.ratio(pred_number_processed,gt)
            match_ratio_lst.append(match_ratio)

        max_ration_index=match_ratio_lst.index(max(match_ratio_lst))
        print(org_image_name,' => {}, {}'.format(pred_number_processed_lst[max_ration_index],
                                             pred_number_processed_lst[max_ration_index]),max(match_ratio_lst))#Raw_Prediction	Match%
        if len(pred_number_plate_lst)>0:
            ANPR_txt=pred_number_processed_lst[max_ration_index]+': '+str(max(match_ratio_lst))
            # print('ANPR_txt : ',ANPR_txt)
        else:
            ANPR_txt='Not Found'
        cv2.putText(org_image,str(ANPR_txt), 
        bottomLeftCornerOfText, 
        font, 
        fontScale,
        fontColor,
        thickness,
        lineType)
        
        ANPR_Output_Path='../data/NP_Recognition/'+org_image_name


        cv2.imwrite(ANPR_Output_Path,org_image)
        



        row_data['Predicted']=pred_number_processed_lst[max_ration_index]
        row_data['Raw_Prediction']=pred_number_plate_lst
        row_data['Match%']=match_ratio_lst[max_ration_index]
        row_data['Match_Individual%']=match_ratio_lst
        row_data['ANPR_Final_Output']=ANPR_Output_Path
        
        row_data['Text']='Done'
        

            # data.append({'image_name':image_name,'pred_number_processed':pred_number_processed,'pred_number':pred_number_plate,'match':match_ratio})
            # break
        # break
    # pd.DataFrame(final_list).to_csv('../data/NP_Recognition/recognition.csv',index=False)
    pd.DataFrame(final_list).to_excel('../data/csvs/ANPR_Analysis_2.xlsx',index=False)
# recog_main()


#pip install pytorch-lightning==1.8.4.post0
class recognition():
    def __init__(self) -> None:
        # self.parseq=torch.jit.load('weights/parseq.pth').eval().to('cpu')
        self.parseq = torch.hub.load('baudm/parseq', 'parseq', pretrained=True).eval()
        if cuda_available:
            self.parseq=self.parseq.cuda()
            print('Parseq Model Loaded On GPU....')
        else:
            print('Parseq Model Loaded On Default....')
        self.img_transform = SceneTextDataModule.get_transform(self.parseq.hparams.img_size)

    def recognition_main(self,craft_crop_list):#list of list : one number plate has one or more crops
        data={
            'Status':1,# Error 1 Done 0
            'Error':1,# Error 1 Done 0
            'ANPR_Text':[],# 
            'ANPR_Text_Found':False,# Return True,False
        }

        try:


            pred_number_plate_lst=[]
            pred_number_processed_lst=[]
            match_ratio_lst=[]
            for number_plate_crops in craft_crop_list:
                pred_number_plate=''
                
                # image_paths=glob(folder_path+'/*rotated*')
                for image_crop in number_plate_crops:
                    # print('image_crop.shape : ',image_crop.shape)
                    #image_crop=cv2.resize(image_crop,(128,32))
                    #image_crop=cv2.cvtColor(image_crop,cv2.COLOR_BGR2RGB)
                    #img=np.transpose(image_crop,(2,0,1))
                    #img=np.array([img])
                    #print('new img.shape : ',img.shape)


                    
                    img = image_crop#Image.open(image_path).convert('RGB')
                    img=Image.fromarray(np.uint8(img)).convert('RGB')
                    # Preprocess. Model expects a batch of images with shape: (B, C, H, W)
                    img = self.img_transform(img).unsqueeze(0)
                    # img=img.resize((32,128))
                    
                    img=torch.FloatTensor(img)
                    if cuda_available:
                        img=img.cuda()

                    # print('img.size : ',img.size)

                    logits = self.parseq(img)
                    
                    # print('Inferace Done')
                    # logits.shape  # torch.Size([1, 26, 95]), 94 characters + [EOS] symbol

                    # Greedy decoding

                    pred = logits.softmax(-1)
                    if cuda_available:
                        logits=logits.cpu().detach().numpy()
                    # print(len(pred[0][0]),torch.argmax(pred[0][0]),':',torch.argmax(pred[0][1]),':',torch.argmax(pred[0][2]))
                    label, confidence = self.parseq.tokenizer.decode(pred)
                    pred_number=label[0]
                    pred_number_plate+=pred_number
                    # print('pred_number : ',pred_number)

                pred_number_plate_lst.append(pred_number_plate)
                pred_number_processed=''.join(e for e in pred_number_plate if e.isalnum())
                pred_number_processed_lst.append(pred_number_processed)
                # match_ratio=fuzz.ratio(pred_number_processed,gt)
                # match_ratio_lst.append(match_ratio)

            if len(pred_number_plate_lst)>0:
                ANPR_txt=pred_number_processed_lst #[max_ration_index]+': '+str(max(match_ratio_lst))
                # print('ANPR_txt : ',ANPR_txt)
            else:
                ANPR_txt='Not Found'
                
            data['Status']=0
            data['Error']=0
            data['ANPR_Text']=ANPR_txt
            if ANPR_txt!='Not Found':
                data['ANPR_Text_Found']=True
            return data


        except Exception as e:
            data['Status']=1
            data['Error']=e
            return data 

# recog_obj=recognition()
# img_list=[[cv2.imread('../input/AP39V5777-anpr-raw-lane2_14_0_rotated.jpg')]]
# print(recog_obj.recognition_main(img_list))
