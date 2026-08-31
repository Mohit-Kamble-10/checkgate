import os
from glob import glo
import numpy as np
import json
import time
import datetime
import cv2
from configs import config
import cv2
import numpy as np
import os
import sys
import shutil 
import threading
import logging
from detection import yolo_pred_surveillance

now = datetime.datetime.now()
start_script_datetime=now.strftime("%d_%m_%Y_%H_%M")

Current_log_path=config.root_path+f"/logs/Surveillance_Inferance_Logs.log"
backup_logs_path=config.root_path+f"/logs/Surveillance_Inferance_Logs/"
os.makedirs(backup_logs_path,exist_ok=True)
if os.path.exists(Current_log_path):
    shutil.move(Current_log_path,backup_logs_path+f"Surveillance_Inferance_Logs_{start_script_datetime}.log")

FORMAT = "%(asctime)s: %(filename)s: %(levelname)s :%(lineno)5s:: - %(funcName)10s() :  %(message)s"
logging.basicConfig(filename=Current_log_path,
                    format=FORMAT,
                    filemode='a',
                    level=logging.DEBUG, # Set logging level
                    force=True)


def read_roi():
    ROI_INFO={}
    if os.path.exists(config.master_config+'/camera_details.json'):
        with open(config.master_config+'/camera_details.json') as json_file:
            get_camera_profile_data = json.load(json_file)
            logging.info('ROI Info Loaded...')
            return get_camera_profile_data
    else:
        print('camera_details.json not found')
        print(config.master_config+'/camera_details.json')
        logging.error('camera_details.json not found')

class AsyncWriteImage(threading.Thread):  
  
    def __init__(self, path,img): 
  
        # calling superclass init 
        threading.Thread.__init__(self,daemon=True)  
        self.img = img 
        self.path = path
        self.start()
  
    def run(self): 
        cv2.imwrite(self.path,self.img)

def read_frames(cap,rtsp_link=None):
    try:
    
        status,frame = cap.read()
        if status:
            return status,frame,cap
        else:
            cap.release()
            frame=np.array([])
            time.sleep(5)
            cap = cv2.VideoCapture(rtsp_link)
            
            return status,frame,cap
        
    except Exception as e:
        print(e)


class main():
    def __init__(self):
        self.ROI_Info=read_roi()
        Gantry_ROI_info=self.ROI_Info['Surveillance_0']['roi_info']
        junction_box_roi_info=self.ROI_Info['Junction_Box_0']['roi_info']
        logging.info("Gantry_ROI_info "+str(Gantry_ROI_info))
        logging.info("junction_box_roi_info "+str(junction_box_roi_info))
        
        self.yolo_pred=yolo_pred_surveillance(junction_box_roi_info=junction_box_roi_info,Gantry_ROI_info=Gantry_ROI_info)
        print('Surveillance Model Loaded...')
        logging.info("Surveillance Model Loaded...")
        
    def main(self,link_type='local'):

        if link_type=='local':
            Surveillance_rtsp_link=self.ROI_Info['Surveillance_0']['localUrl']
            Junction_Box_rtsp_link=self.ROI_Info['Junction_Box_0']['localUrl']
        else:
            Surveillance_rtsp_link=self.ROI_Info['Surveillance_0']['globalUrl']
            Junction_Box_rtsp_link=self.ROI_Info['Junction_Box_0']['globalUrl']
        logging.info("Surveillance_rtsp_link "+Surveillance_rtsp_link) # 10 min
        logging.info("Junction_Box_rtsp_link "+Junction_Box_rtsp_link) # 5 Sec


        gantry_source_path=config.root_path+f'/OUTPUT_Backup/Surveillance_Buffer/Gantry_Surveillance/'
        junction_box_source_path=config.root_path+f'/OUTPUT_Backup/Surveillance_Buffer/Junction_Box_Surveillance/'
        
        # if os.path.exists(gantry_source_path):
        #     shutil.rmtree(gantry_source_path)
        os.makedirs(gantry_source_path,exist_ok=True)
        os.makedirs(junction_box_source_path,exist_ok=True)
        
        gantry_cap = cv2.VideoCapture(Surveillance_rtsp_link)
        junction_box_cap = cv2.VideoCapture(Junction_Box_rtsp_link)
        logging.info("capturing started ")

        while True:
            try:
                time.sleep(5)
                ret,junction_box_frame,junction_box_cap=read_frames(junction_box_cap,Junction_Box_rtsp_link)# 5 sec
                ret,gantry_frame,gantry_cap=read_frames(gantry_cap,Surveillance_rtsp_link)# 5 sec
                

                if ret:
                    now = datetime.datetime.now()
                    captured_time_=now.strftime("%d_%m_%Y_%H_%M_%S")
                    captured_date=now.strftime("%d_%m_%Y")
                    captured_time=now.strftime("%H_%M")
                    
                    image_path=junction_box_source_path+f'/{captured_date}/{captured_time}/'
                    image_path=image_path+f'/junction_box_{captured_time_}.jpg'
                    save_raw=AsyncWriteImage(image_path,junction_box_frame)
                    save_raw.join()

                else:
                    cv2.destroyAllWindows()



            
            except Exception as e:
                logging.error(str(e))
                if config.check_error:
                    print("Surveillance : ",e)
                continue

if __name__ == "__main__":


    main().main(link_type='local')
    
