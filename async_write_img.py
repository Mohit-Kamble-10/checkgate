import threading 
from multiprocessing import Process
import logging
import time 
import cv2
import json
import requests
from glob import glob
# Inherting the base class 'Thread' 
from configs.config import root_path
FORMAT = "%(asctime)s: %(filename)s:%(lineno)s - %(funcName)20s() %(message)s"
logging.basicConfig(filename=root_path+"/logs/dataupload.log",
                    format=FORMAT,#'%(asctime)s %(message)s',
                    filemode='w',force=True)

# Creating an object
logger = logging.getLogger()
 
# Setting the threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)
class AsyncWriteImage(threading.Thread):  
  
    def __init__(self, path,img): 
  
        # calling superclass init 
        threading.Thread.__init__(self,daemon=True)  
        self.img = img 
        self.path = path
        self.start()
  
    def run(self): 
        cv2.imwrite(self.path,self.img)
                                
class AsyncUploadImage(threading.Thread):  
  
    def __init__(self,Id,path): 
  
        # calling superclass init 
        threading.Thread.__init__(self,daemon=True)  
        self.id = Id
        self.image_upload_url='https://mahakhanij.maharashtra.gov.in/mineral-mapping/uploads/insert-toll-plaza-photo'
        #'https://awsapi.mahamining.com/mineral-mapping/uploads/insert-toll-plaza-photo'
        #'https://awsapi.mahamining.com/mineral-mapping/uploads/insert-log-photo'
        self.root_path = path#'../output/transactions/'
        self.start()
  
    def run(self): 
        try:
            json_path=self.root_path+str(self.id).zfill(2)+f'/json/response.json'
            with open(json_path) as json_file:
                json_data = json.load(json_file)
            #sync
            Respons_Id=json_data['responseData']['logId']
            isPhotoRequired=json_data['responseData']['isPhotoRequired']
            # print('isPhotoRequired : ',isPhotoRequired)
            if isPhotoRequired:
                image_path_list=glob(f'{self.root_path}{str(self.id).zfill(2)}/**/**.png')
                image_path_list.extend(glob(f'{self.root_path}{str(self.id).zfill(2)}/**/**.jpg'))
                # print('id : ',self.id,len(image_path_list))
                for image_path in image_path_list:
                    # print('image_path : ',id,image_path)
                    files1 = {'files': open(image_path, 'rb')}
                    json_dict={'Log_ID':Respons_Id,'ImagePath':''}

                    response=requests.post(self.image_upload_url,data=json_dict,files=files1)
                    # response=response.json()
                    # print('response : ',response)
                
                # print('Uploading Done : ',self.id)
                logger.info('Uploading Done : '+str(self.id))
                json_data['responseData']['isPhotoRequired']=False
                with open(json_path, 'w') as f:
                    json.dump(json_data, f)
        except Exception as e:
            logger.error('Error: '+str(self.id)+'_ Error : '+str(e))
            print('id',str(id),'Error',str(e))
                              
def MultiProcess_UploadImage(Id,path):  
    try:
        id = Id
        image_upload_url='https://mahakhanij.maharashtra.gov.in/mineral-mapping/uploads/insert-toll-plaza-photo'
        #'https://awsapi.mahamining.com/mineral-mapping/uploads/insert-toll-plaza-photo'
        #'https://awsapi.mahamining.com/mineral-mapping/uploads/insert-log-photo'
        root_path = path#'../output/transactions/'
        json_path=root_path+str(id).zfill(2)+f'/json/response.json'
        with open(json_path) as json_file:
            json_data = json.load(json_file)
        #sync
        Respons_Id=json_data['responseData']['logId']
        isPhotoRequired=json_data['responseData']['isPhotoRequired']
        # print('isPhotoRequired : ',isPhotoRequired)
        if isPhotoRequired:
            image_path_list=glob(f'{root_path}{str(id).zfill(2)}/**/**.png')
            image_path_list.extend(glob(f'{root_path}{str(id).zfill(2)}/**/**.jpg'))
            # print('id : ',self.id,len(image_path_list))
            for image_path in image_path_list:
                # print('image_path : ',id,': ',image_path)
                files1 = {'files': open(image_path, 'rb')}
                json_dict={'Log_ID':Respons_Id,'ImagePath':''}

                response=requests.post(image_upload_url,data=json_dict,files=files1)
                # response=response.json()
                # print('response : ',response)
            
            # print('Uploading Done : ',self.id)
            logger.info('Uploading Done : '+str(id))
            json_data['responseData']['isPhotoRequired']=False
            with open(json_path, 'w') as f:
                json.dump(json_data, f)
    except Exception as e:
        logger.error('Error: '+str(id)+'_ Error : '+str(e))
        print('id',str(id),'Error',str(e))
        
#id 1068
# path 
# p1=Process(target=MultiProcess_UploadImage,args=(1067,'../output/transactions_lane3/31_08_2023/'))
# p1.start()
# p1.join()
# print('Done')
# MultiProcess_UploadImage(1068,'../output/transactions_lane3/31_08_2023/')