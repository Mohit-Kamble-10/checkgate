import os
from glob import glob
import pandas as pd
import numpy as np
import requests
import json
import time
import datetime
import cv2
from IPython.display import Image
from configs import config
# from configs import camera_config
import cv2
import numpy as np
import os
import sys
import shutil 
import threading
import logging
lane_no=sys.argv[1] # string 1,2,3
link_type=sys.argv[2] # local/global
Buffer_size=2000


now = datetime.datetime.now()
start_script_datetime=now.strftime("%d_%m_%Y_%H_%M")

Current_log_path=config.root_path+f"/logs/Capture_Top_Logs_{str(lane_no)}.log"
backup_logs_path=config.root_path+f"/logs/Capture_Top_Logs/"
os.makedirs(backup_logs_path,exist_ok=True)
if os.path.exists(Current_log_path):
    shutil.move(Current_log_path,backup_logs_path+f"Capture_Top_Logs_{str(lane_no)}_{start_script_datetime}.log")

FORMAT = "%(asctime)s: %(filename)s: %(levelname)s :%(lineno)5s:: - %(funcName)10s() :  %(message)s"
logging.basicConfig(filename=Current_log_path,
                    format=FORMAT,
                    filemode='a',
                    level=logging.DEBUG, # Set logging level
                    force=True)

if os.path.exists(config.master_jsons+'/camera_details.json'):
    with open(config.master_jsons+'/camera_details.json') as json_file:
        get_camera_profile_data = json.load(json_file)
        logging.info("camera_details Loaded")
else:
    logging.error("camera_details not found")

class AsyncWriteImage(threading.Thread):  
  
    def __init__(self, path,img): 
  
        # calling superclass init 
        threading.Thread.__init__(self,daemon=True)  
        self.img = img 
        self.path = path
        self.start()
  
    def run(self): 
        cv2.imwrite(self.path,self.img)

def read_frames_top(cap_top,rtsp_link=None):
    try:
    
        status, top_frame = cap_top.read()
        if status:
            return status,top_frame,cap_top
        else:
            cap_top.release()
            top_frame=np.array([])
            time.sleep(5)
            cap_top = cv2.VideoCapture(rtsp_link)#cv2.VideoCapture('rtsp://103.204.39.9:8109/avstream/channel=1/stream=0.sdp') 
            
            return status,top_frame,cap_top
        
    except Exception as e:
        print(e)


class main():
    def main(self):

        if link_type=='local':
            rtsp_link=get_camera_profile_data['Top_'+str(lane_no)]['localUrl']
            
            

            # rtsp_link=camera_config.Camera_rtsp_local_links[int(lane_no)]['Top']
        else:
            rtsp_link=get_camera_profile_data['Top_'+str(lane_no)]['globalUrl']
            # rtsp_link=camera_config.Camera_rtsp_global_links[int(lane_no)]['Top']
        logging.info("rtsp_link "+rtsp_link)

        
    
        # print('Top_rtsp : ',rtsp_link)



        source_path=config.root_path+f'/OUTPUT_Backup/Top_Buffer/Lane_{str(lane_no)}/'
        if os.path.exists(source_path):
            shutil.rmtree(source_path)
        os.makedirs(source_path,exist_ok=True)
        cap = cv2.VideoCapture(rtsp_link)
        logging.info("capturing started ")


        start_time = time.time()
        # count=0
        frame_count=0
        image_path_list=glob(source_path+'/top_image**')
        # print('image_path_list :',len(image_path_list))
        while True:
            try:
                elapsed_time = time.time() - start_time
                ret,top_frame,cap=read_frames_top(cap,rtsp_link)
                if frame_count%1==0:
                    frame_count+=1
                    if ret:
                        now = datetime.datetime.now()
                        captured_time_=now.strftime("%d_%m_%Y_%H_%M_%S")
                        count=0
                        while True:
                            image_path=source_path+f'/top_image_{captured_time_}_{str(count)}.jpg'
                            if os.path.exists(image_path):
                                count+=1
                            else:
                                break
                        # Sync write — AsyncWrite+join() was not async and doubled work/peak RAM
                        cv2.imwrite(image_path, top_frame)
                        image_path_list.append(image_path)
                        if len(image_path_list)>=Buffer_size:
                            to_remove_image_path=image_path_list.pop(0)
                            if os.path.exists(to_remove_image_path):
                                os.remove(to_remove_image_path)
                        del top_frame

                    

                        
                else:
                    frame_count+=1
                    if frame_count>=1000:
                        print('frame count reached : 1000 , reset to 0')
                        logging.info("frame count reached : 1000 , reset to 0")
                        frame_count=0
                        cap.release()
                        cv2.destroyAllWindows()
                        cap = cv2.VideoCapture(rtsp_link)



            
            except Exception as e:
                logging.error(str(e))
                if 'Input/output error' in  str(e):
                    logging.error('Capture Top code Error : Capture_Top.py  Restarted')
                    os.execv(sys.executable, ['python3'] + sys.argv)
                
                if config.check_error:
                    print("Capture Top : ",e)
                continue

if __name__ == "__main__":


    main().main()
    
