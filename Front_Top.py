import cv2
import numpy as np
import time
import os
import json
import requests
import logging
import logging.config
import datetime
import requests
from detection import yolo_pred
from async_write_img import AsyncWriteImage#,AsyncUploadImage,MultiProcess_UploadImage
from glob import glob 
import sys
sys.path.append('/home/aikernel/src/') 
from secure_api import send_json
import shutil
# from configs.camera_config import ANPR_3,Front_3,Top_3
# from configs import camera_config
from configs.config import anpr_image_size, anpr_fps, \
    vehicle_not_found_frame_count,\
    show_live_video,save_raw_video,top_process_start,number_of_top_frames_analize,\
    root_path_lane,root_path,fontScale,fontColor,thickness,lineType,\
    Country,MachineID,mining_vehicle_list,non_mining_vehicle_list,Lane_Restart_API,Lane_HealthCheck_API,\
    check_error,master_jsons,\
    Suppress_Until_ANPR_ROI_Empty,Suppress_ROI_Empty_Frame_Count,\
    Allow_Multi_Box_New_Txn,Multi_Box_Min_Count

from general_operations.config_operations import Logs_Folder_Path
#from set_masters import main as set_master_main
#==================================================================
"""
Set all master table
API
"""
# set_master_main()
#==================================================================
lane_no=int(sys.argv[1]) # string 1,2,3
link_type=sys.argv[2] # local/global

#=============================== Create and configure logging ===============================
# rename backup to lane_no start_script_datetime
now = datetime.datetime.now()
start_script_datetime=now.strftime("%d_%m_%Y_%H_%M")

Current_log_path=root_path+f"/logs/front_top_{str(lane_no)}.log"
backup_logs_path=root_path+f"/logs/Front_Top_Logs/"
os.makedirs(backup_logs_path,exist_ok=True)
if os.path.exists(Current_log_path):
    shutil.move(Current_log_path,backup_logs_path+f"front_top_{str(lane_no)}_{start_script_datetime}.log")

FORMAT = "%(asctime)s: %(filename)s: %(levelname)s :%(lineno)5s:: - %(funcName)10s() :  %(message)s"
logging.basicConfig(filename=Current_log_path,
                    format=FORMAT,
                    filemode='a',
                    level=logging.DEBUG, # Set logging level
                    force=True)
    
# Creating an object
# logging = logging.getlogging()
# Setting the threshold of logging to DEBUG
# logging.setLevel(logging.DEBUG)
#==================================================================

if os.path.exists(master_jsons+'/camera_details.json'):
    with open(master_jsons+'/camera_details.json') as json_file:
        get_camera_profile_data = json.load(json_file)
    if link_type=='global':
        ANPR_RTSP=get_camera_profile_data['ANPR_'+str(lane_no)]['globalUrl']
    else:
        ANPR_RTSP=get_camera_profile_data['ANPR_'+str(lane_no)]['localUrl']
    ROI_INFO=get_camera_profile_data['ANPR_'+str(lane_no)]['roi_info']
else:
    print('camera_details.json not found')
    print(master_jsons+'/camera_details.json')
    # exit()

# ANPR_RTSP='/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/Videos/Save_Video/ANPR_Banrasiya.mp4'
class main():
    def __init__(self) -> None:
        self.transaction_start_time=time.time()
        

        #################################################################
        
        
        self.font                   = cv2.FONT_HERSHEY_SIMPLEX
        self.fontScale              = fontScale
        self.fontColor              = fontColor
        self.thickness              = thickness
        self.lineType               = lineType

        ############################################################
        self.lane_id=int(lane_no)
        self.ANPR_rtsp=ANPR_RTSP
        # if link_type=='local':
        #     self.ANPR_rtsp=camera_config.Camera_rtsp_local_links[int(lane_no)]['ANPR']
        # else:
        #     self.ANPR_rtsp=camera_config.Camera_rtsp_global_links[int(lane_no)]['ANPR']
        self.cap_anpr = cv2.VideoCapture(self.ANPR_rtsp)
        # start_frame_number = 200#0
        # self.cap_anpr.set(cv2.CAP_PROP_POS_FRAMES, start_frame_number)

        self.vehicle_count=0
        self.id=0
        self.Raw_ANPR_Text_List=[]
        self.last_text_lst=[]
        self.final_text=''
        self.ANPR_frame_fail_count=0
        self.Top_frame_shape=[]
        self.top_raw_image_count_thresh=number_of_top_frames_analize
        self.show_live_video=show_live_video
        
        self.save_raw_video=save_raw_video
        self.top_process_start=top_process_start
        self.root_path_lane = root_path_lane
        self.root_path = root_path_lane
        # self.create_folder_strct()

        #################################################################
        #Lane3_ROI
        self.yolo_obj=yolo_pred(lane_id=self.lane_id,roi_info=ROI_INFO)
        # self.craft_obj=craft()
        # self.recog_obj=recognition()
        # self.pp_obj=post_processing()

        logging.info('All Model Loaded Successfully.....')
        
        logging.info('Intialization Done Successfully.....')




    
    def auto_detect_last_id(self):
        try:
            # print("self.root_path+'**' : ",self.root_path+'**')
            path_list=glob(self.root_path+'**')
            # print('path_list : ',path_list)
            transaction_count=len(path_list)
            
            self.id=transaction_count+1
            print('current -> transaction_count+1 : ',transaction_count)
            # count=len(os.listdir(self.root_path))
            # self.id+=(count+1)
            logging.info('Last_Id init= '+str(self.id))
        except Exception as e:
            logging.error(str(e))


    def create_id_folder_mp(self):
        try:
            
            main_path=self.root_path+str(self.id).zfill(5)+'/'
            # print('MP main_path : ',main_path)
            os.makedirs(main_path,exist_ok=True)
            os.makedirs(main_path+'/raw',exist_ok=True)
            os.makedirs(main_path+'/processed',exist_ok=True)
            os.makedirs(main_path+'/prediction',exist_ok=True)
            os.makedirs(main_path+'/top_crop',exist_ok=True)
            os.makedirs(main_path+'/json',exist_ok=True)
            # print('Folder Created with Id : ',main_path)
            logging.info('Folder Structure Created Successfully.....')
        except Exception as e:
            logging.error(str(e))
    def show_anpr_video(self):
        # frame=cv2.resize(self.Vehicle_NP_Detection_Frame,(0,0),fx=0.3,fy=0.3)
        frame=self.Vehicle_NP_Detection_Frame
        cv2.imshow('Video Analytic by Charlie',frame)
        
    def show_anpr_video_1(self):
        frame=cv2.resize(self.anpr_frame_1,(0,0),fx=0.3,fy=0.3)
        cv2.imshow('Video Analytic Raw',frame)

    def show_top_video(self):
        frame=cv2.resize(self.top_frame,(0,0),fx=0.3,fy=0.3)
        cv2.imshow('Top Analytic by Charlie',frame)
    
    def read_frames_anpr(self,reintialized=False):
        data={
            'status':0,
            'error_message':''
        }
        try:
            
            if reintialized:
                self.cap_anpr.release()
                del(self.cap_anpr)
                # self.anpr_frame=None
                # logging.error(str('Frame reading issue.....time.sleep(5)')) 
                # time.sleep(5)
                self.cap_anpr = cv2.VideoCapture(self.ANPR_rtsp)#cv2.VideoCapture('rtsp://103.204.39.9:8109/avstream/channel=1/stream=0.sdp') 
                status, self.anpr_frame = self.cap_anpr.read()
                logging.info(str('self.cap_anpr re-intialized.....'))
                print('ANPR reintialized....')
                # data['status']=1
                # self.ANPR_frame_fail_count+=1

                return data
            
            else:
                status, self.anpr_frame = self.cap_anpr.read()
                if status:
                    self.ANPR_frame_fail_count=0
                    return data
                else:
                    # exit()
                    self.cap_anpr.release()
                    self.anpr_frame=None
                    logging.error(str('Frame reading issue.....time.sleep(5)')) 
                    time.sleep(5)
                    self.cap_anpr = cv2.VideoCapture(self.ANPR_rtsp)#cv2.VideoCapture('rtsp://103.204.39.9:8109/avstream/channel=1/stream=0.sdp') 
                    logging.info(str('self.cap_anpr re-intialized.....'))
                    data['status']=1
                    self.ANPR_frame_fail_count+=1

                    return data
                
        except Exception as e:
            data['status']=1
            logging.error(str(e))

    def Write_ANPR_Text(self):
        if len(self.final_text)>0 :# For same vehicle  and len(ANPR_Image_Paths)==0 , and self.vehicle_count==self.yolo_output['Count']
            # and not os.path.exists(self.root_path+str(self.id).zfill(2)+f'/prediction/Anpr_Pred.png'):
            try:
                
                xyxy=self.yolo_output['Vehicle_Number_Crop_Points'][0]
                c1, c2 = (int(xyxy[0]), int(xyxy[1])-10), (int(xyxy[2]), int(xyxy[3]))
                tf = max(self.thickness - 1, 1)  # font thickness
                w, h = cv2.getTextSize('label', 0, fontScale=self.fontScale, thickness=self.thickness)[0]  # text width, height
                outside = c1[1] - h 
                p2 = c1[0] + w+60, c1[1] - h if outside else c1[1] + h 
                cv2.rectangle(self.Vehicle_NP_Detection_Frame, c1, p2, (128,0,128), -1, cv2.LINE_AA)  # filled
                cv2.putText(self.Vehicle_NP_Detection_Frame,
                        self.final_text, 
                        (c1[0], c1[1] - 2 if outside else c1[1] + h ),
                        0,
                        self.thickness / 3,
                        self.fontColor,
                        thickness=tf,
                        lineType=cv2.LINE_AA)
                logging.info('ANPR Write_ANPR_Text Successfully.....')
                
            except Exception as e:
                logging.error(str(e))
    def save_raw_image_mp(self,override=False):
        try:
            raw_image=self.anpr_frame
            path=self.root_path+str(self.id).zfill(5)+f'/raw/Anpr_Raw.png'#_{self.found_date_time}
            if not os.path.exists(path) or override:
                upload_raw=AsyncWriteImage(path,raw_image)
                upload_raw.join()
                # print('save_raw_image_mp : ',self.id,path)
            logging.info('ANPR Raw Image Save Successfully.....')
        except Exception as e:
            logging.error(str(e))
            
    def save_ANPR_Pred_image(self,override=False):
        try:
            path=self.root_path+str(self.id).zfill(5)+f'/prediction/Anpr_Pred.png'
            # print('save_ANPR_Pred_image : ',path)
            if not os.path.exists(path) or override:
                upload_ANPR_Pred=AsyncWriteImage(path,self.Vehicle_NP_Detection_Frame)
                upload_ANPR_Pred.join()
                logging.info('ANPR Pred Image Save Successfully.....')
            else:
                pass
                # print(f'save_ANPR_Pred_image : {self.id} Anpr_Pred.png already exists....')
        except Exception as e:
            print('save_ANPR_Pred_image : ',e)
            logging.error(str(e))
            
    
    def save_raw_anpr_video(self):
        try:
            path=self.root_path+str(self.id).zfill(5)+f'/raw/ANPR_Video.mp4'#_To_analize_{self.found_date_time}.
            if not os.path.exists(path):
                # print('Video Data Found and Storing : ',self.id)
                fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')#cv2.VideoWriter_fourcc('mp4v')#(*'MP4V')
                # writer = cv2.VideoWriter(path, fourcc, 10.0, (1920,1080))+
                writer = cv2.VideoWriter(path, fourcc, anpr_fps, anpr_image_size)
                # 
                # print('video path : ',path)
                for frame in self.anpr_buffer:
                    writer.write(frame)
                    # print('video saving')
                writer.release()             
                logging.info(str('Raw ANPR Video Save Successfully...'))
            else:
                # print('Raw ANPR Video Already Found...')
                logging.info(str('Raw ANPR Video Already Found...'))
        except Exception as e:
            logging.info(str(e))
    
    def save_anpr_prediction_video(self):
        try:

            path=root_path_lane+f'/ANPR_Pred_Video.mp4'
            print('Saved ANPR Prediction Path : ',path)
            # if not os.path.exists(path):
            # print('Video Data Found and Storing : ',self.id)
            fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')#cv2.VideoWriter_fourcc('mp4v')#(*'MP4V')
            # writer = cv2.VideoWriter(path, fourcc, 10.0, (1920,1080))+
            writer = cv2.VideoWriter(path, fourcc, anpr_fps, anpr_image_size)
            # 
            # print('video path : ',path)
            for frame in self.anpr_prediction_buffer:
                writer.write(frame)
                # print('video saving')
            writer.release()             
            logging.info(str('Raw ANPR Video Save Successfully...'))
            # else:
            #     # print('Raw ANPR Video Already Found...')
            #     logging.info(str('Raw ANPR Video Already Found...'))
        except Exception as e:
            logging.info(str(e))
    
    def save_number_plate_crop_image(self,final_ANPR_image=False):
        try:
            Number_plate_crop_list=glob(self.root_path+str(self.id).zfill(5)+f'/processed/NumberPlate_Crop**')
            image_count=len(Number_plate_crop_list)
            # print("Number_plate_crop_list : ",len(Number_plate_crop_list)," : ",Number_plate_crop_list)
            big_list=self.yolo_output.get('Vehicle_Number_Crop_Big_List') or []
            for i in range(len(self.yolo_output['Vehicle_Number_Crop_List'])):
                while True:
                    path=self.root_path+str(self.id).zfill(5)+f'/processed/NumberPlate_Crop_{str(image_count)}.png'#{self.found_date_time}_
                    if not os.path.exists(path) or final_ANPR_image:
                        upload_crop_NP=AsyncWriteImage(path,self.yolo_output['Vehicle_Number_Crop_List'][i][:, :, ::-1])
                        upload_crop_NP.join()
                        if i < len(big_list) and big_list[i] is not None:
                            path_big=self.root_path+str(self.id).zfill(5)+f'/processed/BigNumberPlate_Crop_{str(image_count)}.png'
                            upload_big=AsyncWriteImage(path_big,big_list[i][:, :, ::-1])
                            upload_big.join()
                        break
                    else:
                        image_count+=1

                        

                if i>=1:
                    self.number_plate_crop_count+=1
            logging.info('Number Plate Crop Save Successfully.....')
            
        except Exception as e:
            logging.error(str(e))
    
    def save_mineral_crop_image(self):
        # print('Save Top : ',len(self.yolo_output['Raw_Mining_Full_Crop_List']))
        try:

            counter=len(glob(self.root_path+str(self.id).zfill(5)+f'/top_crop/*.png*'))
                         
            for i in range(len(self.yolo_output['Raw_Mining_Full_Crop_List'])):
                
                path=self.root_path+str(self.id).zfill(5)+f'/top_crop/Top_Crop_{str(i+counter)}.png'
                
                upload_crop_NP=AsyncWriteImage(path,self.yolo_output['Raw_Mining_Full_Crop_List'][i][:, :, ::-1])#[:, :, ::-1]
                upload_crop_NP.join()
                logging.info('Number Plate Crop Save Successfully.....')
            
        except Exception as e:
            logging.error(str(e))
    
    def check_non_mining_category(self):
        # set non-mining top category for non-mining vehicles
        if self.json_dict['top_class_name']=='' and self.json_dict['front_class_name'] in non_mining_vehicle_list:
            self.json_dict['top_class_name']='non_mining'
    def save_json(self,override=False):
        try:
            path=self.root_path+str(self.id).zfill(5)+f'/json/Front_Top_output.json'
            # print('save json path : ',path)
            # set non-mining top category for non-mining vehicles
            self.check_non_mining_category()
            if not os.path.exists(path) or override:    
                with open(path, 'w') as f:
                    json.dump(self.json_dict, f)
                logging.info('Json Save Successfully.....')
        except Exception as e:
            logging.error(str(e))
    def save_top_image(self,Image_Count=1):
        
        try:
            top_path =self.root_path+str(self.id).zfill(5)
            
            raw_image=self.anpr_frame
            raw_dest=top_path+f'/raw/Top_Raw_{str(Image_Count)}.jpg'
            
            pred_image=self.Vehicle_NP_Detection_Frame
            pred_dest=top_path+f'/prediction/Top_Pred_{str(Image_Count)}.jpg'

            cv2.imwrite(raw_dest,raw_image)
            cv2.imwrite(pred_dest,pred_image)
        except Exception as e:
            print(e)
            logging.error('save_top_image : '+str(e))
    def reset_partial_parameters(self):
        try:
            self.json_dict['front_class_name']=''
            self.json_dict['top_class_name']=''
            # self.json_dict['final_text']=''
            # self.json_dict['raw_vehicleno']=''
            # self.final_text=''
            self.vehicle_not_found_from_50_frame=True
            self.id_processed=True
            self.json_dict['Raw_Top_Category_List']=[]
            self.number_plate_crop_count=0
            # self.ANPR_Pred_Frame_For_inconclusive=np.empty(0)
            # print('----------- reset_partial_parameters -----------------')
            logging.info('-------------------reset_partial_parameters Done Successfully-------------------')


        except Exception as e:
            logging.error('rest_parameters catch Block : '+str(e))

    def _arm_suppress_until_roi_empty(self, reason=''):
        """After txn completes: block new starts until mining-front leaves ANPR ROI."""
        if not Suppress_Until_ANPR_ROI_Empty:
            return
        self.waiting_for_roi_exit = True
        self.roi_empty_frames = 0
        # Allow one multi-box escape for a 2nd vehicle that enters while 1st still in ROI
        self.multi_box_escape_used = False
        logging.info(
            f'Suppress until ANPR ROI empty armed ({reason}) '
            f'txn={self.json_dict.get("id")}'
        )

    def _update_suppress_on_empty_roi(self):
        """Count consecutive frames with no mining-front in ANPR ROI; then clear suppress."""
        if not Suppress_Until_ANPR_ROI_Empty or not self.waiting_for_roi_exit:
            return
        mining_n = int(self.yolo_output.get('Mining_Front_In_ROI_Count') or 0)
        if mining_n > 0:
            self.roi_empty_frames = 0
            if mining_n < Multi_Box_Min_Count:
                self.multi_box_escape_used = False
            return
        self.roi_empty_frames += 1
        if self.roi_empty_frames >= Suppress_ROI_Empty_Frame_Count:
            self.waiting_for_roi_exit = False
            self.multi_box_escape_used = False
            self.roi_empty_frames = 0
            logging.info('ANPR ROI empty — suppress cleared; next mining vehicle may start a txn')

    def _may_start_new_transaction(self, multi_box_escape=False):
        """
        Gate new txn folder creation.
        - Option A: while waiting_for_roi_exit, block unless multi-box escape.
        - Always keep >1s debounce.
        """
        now_ts = time.time()
        if int(now_ts - self.transaction_start_time) <= 1:
            return False
        if Suppress_Until_ANPR_ROI_Empty and self.waiting_for_roi_exit and not multi_box_escape:
            return False
        return True

    def _start_new_transaction(self, reason='count_change'):
        """Create folder + Anpr_Raw for a new transaction id."""
        self.transaction_start_time = time.time()
        self.rest_parameters()
        now = datetime.datetime.now()
        self.id += 1
        self.found_date_time = now.strftime("%d_%m_%Y_%H_%M_%S")
        self.json_dict['datetime'] = self.found_date_time
        self.json_dict['id'] = self.pre_seqence + str(self.id).zfill(5)
        self.json_dict['ANPR_frames_process'] = 1
        self.create_id_folder_mp()
        self.top_raw_image_count = 1
        self.save_raw_image_mp()
        self.save_ANPR_Pred_image()
        self.json_dict['double_entry'] = "No"
        logging.info(
            f"Transaction Started: {str(self.json_dict['id'])} reason={reason}"
        )

    def rest_parameters(self):
        try:
            self.json_dict={
                'id':-1,
                'datetime':'',
                'top_class_name':'',
                'front_class_name':'',
                'lane_id':self.lane_id,
                'ANPR_frames_process':0,
                'Processed':False,
                'Raw_Top_Category_List':[],
                'Raw_Front_Category_List':[]
            }
            self.front_frame=None
            self.top_frame=None
            self.anpr_buffer=[]
            self.Vehicle_Not_Found=0
            self.Override_Done=False
            self.id_processed=False
            self.vehicle_not_found_from_50_frame=False
            self.number_plate_crop_count=0
            # Do NOT clear waiting_for_roi_exit / multi_box_escape_used here —
            # suppress must survive rest_parameters until ROI is empty.

            logging.info('-------------------rest_parameters Done Successfully-------------------')


        except Exception as e:
            logging.error('rest_parameters catch Block : '+str(e))

    def save_code_restart_Log(self):
        try:
            main_log_folder=Logs_Folder_Path+'/lane_code_restart_status/'
            folder_name=now.strftime("%d_%m_%Y")
            found_date_time=now.strftime("%d_%m_%Y_%H_%M_%S")
            request_path=main_log_folder+folder_name+'/request/'
            response_path=main_log_folder+folder_name+'/response/'
            os.makedirs(request_path,exist_ok=True)
            os.makedirs(response_path,exist_ok=True)
            report={
            "machineId": int(MachineID),
            "laneId": self.lane_id,
            "code_restart_datetime":found_date_time,
            "aI_CreatedDate":found_date_time
            }
            request_json_filename=f'request_Front_Top_lane_{str(self.lane_id)}_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
            response_json_filename=f'response_Front_Top_lane_{str(self.lane_id)}_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'

            with open(request_path+'/'+request_json_filename, 'w') as f:
                json.dump(report, f)

            response,message=send_json(Lane_Restart_API,json_data=report)
    
            # response=response.json()
            print('response : ',response)

            with open(response_path+'/'+response_json_filename, 'w') as f:
                json.dump(response, f)

        except Exception as e:
            print(e)
    
    def save_code_health_check_Log(self):
        try:
            main_log_folder=Logs_Folder_Path+'/code_health_check/'
            folder_name=now.strftime("%d_%m_%Y")
            found_date_time=now.strftime("%d_%m_%Y_%H_%M_%S")
            request_path=main_log_folder+folder_name+'/request/'
            response_path=main_log_folder+folder_name+'/response/'
            os.makedirs(request_path,exist_ok=True)
            os.makedirs(response_path,exist_ok=True)
            report={
            "machineId": int(MachineID),
            "laneId": self.lane_id,
            "Status":"running",
            "aI_CreatedDate":found_date_time
            }
            request_json_filename=f'request_Front_Top_lane_{str(self.lane_id)}_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'

            response_json_filename=f'response_Front_Top_lane_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'

            with open(request_path+'/'+request_json_filename, 'w') as f:
                json.dump(report, f)

            response,message=send_json(Lane_HealthCheck_API,json_data=report)
    
            response=response.json()
            print('response : ',response)

            with open(response_path+'/'+response_json_filename, 'w') as f:
                json.dump(response, f)

        except Exception as e:
            print(e)

    def main(self):
        self.save_code_restart_Log()
        self.save_code_health_check_Log()
        self.code_start_time=time.time()
        now = datetime.datetime.now()
        self.pre_seqence=f'{Country}{MachineID}'+now.strftime("%d%m%Y")+f'{str(self.lane_id).zfill(2)}'
        self.root_path=self.root_path_lane+self.pre_seqence
        print('self.root_path : ',self.root_path)
        self.auto_detect_last_id()
        self.found_date_time=now.strftime("%d:%m:%Y_%H:%M:%S")
        Tomorrow_Date = datetime.date.today() + datetime.timedelta(days=1)
        self.rest_parameters()
        self.top_raw_image_count=1
        self.last_front_class_name_list=[]
        self.last_Raw_Top_Category_List=[]
        self.anpr_prediction_buffer=[]
        # Duplicate-txn suppress state (Option A + multi-box)
        self.waiting_for_roi_exit = False
        self.roi_empty_frames = 0
        self.multi_box_escape_used = False
        frame_count=1
        while True:
            try:
                
                if datetime.date.today() >= Tomorrow_Date:
                    now = datetime.datetime.now()
                    self.pre_seqence=f'{Country}{MachineID}'+now.strftime("%d%m%Y")+f'{str(self.lane_id).zfill(2)}'
                    self.root_path=self.root_path_lane+self.pre_seqence#+now.strftime("%d_%m_%Y")
                    self.auto_detect_last_id()
                    Tomorrow_Date = datetime.date.today() + datetime.timedelta(days=1)
                read_frame_output=self.read_frames_anpr()
                if frame_count%1000==0:
                    logging.info(f'Frame Count : {str(frame_count)} ')
                elif frame_count>=100000:
                     frame_count=1
                if read_frame_output['status']!=0:
                    print('Frame reading issue....wait for 5 sec....')
                    logging.error(f'Frame reading issue....wait for 5 sec....')
                    continue
                self.yolo_output=self.yolo_obj.yolo_ANPR_main(self.anpr_frame)

                if self.yolo_output['Status']==0:
                    if self.yolo_output['Error']!='':
                        logging.error('Detection Error : '+str(self.yolo_output['Error']))
                    self.Vehicle_NP_Detection_Frame=self.yolo_output['Return_Disply_Frame'][0]

                    if self.yolo_output['Vehicle_Found'] and self.yolo_output['Front_IN_ROI']:#
                        self.Vehicle_Not_Found=0
                        mining_n = int(self.yolo_output.get('Mining_Front_In_ROI_Count') or 0)
                        # Occupied ROI while suppressed — reset empty counter; re-arm multi-box if only 1 left
                        if Suppress_Until_ANPR_ROI_Empty and self.waiting_for_roi_exit:
                            self.roi_empty_frames = 0
                            if mining_n < Multi_Box_Min_Count:
                                self.multi_box_escape_used = False

                        count_changed = self.vehicle_count != self.yolo_output['Count']
                        multi_box_escape = (
                            Suppress_Until_ANPR_ROI_Empty
                            and Allow_Multi_Box_New_Txn
                            and self.waiting_for_roi_exit
                            and mining_n >= Multi_Box_Min_Count
                            and not self.multi_box_escape_used
                        )
                        want_new_txn = count_changed or multi_box_escape

                        # print(f"not id_processed : {not self.id_processed } or vehicle_count!=self.yolo_output['Count'] : {self.vehicle_count}!={self.yolo_output['Count']} : {self.vehicle_count!=self.yolo_output['Count']}")
                        if not self.id_processed or want_new_txn:
                            if want_new_txn:
                                if self.id_processed==False and count_changed:
                                    if self.save_raw_video:
                                        self.save_raw_anpr_video()
                                    # if self.json_dict['vehicleno']=='':
                                    #     self.json_dict['manual_check_req']="2"
                                    self.json_dict['Raw_Front_Category_List']=self.last_front_class_name_list
                                    self.json_dict['Raw_Top_Category_List']=self.last_Raw_Top_Category_List
                                    # print('1--->Mining_Full_Crop_Found : ', self.yolo_output['Mining_Full_Crop_Found'])

                                    if self.yolo_output['Mining_Full_Crop_Found']==True:
                                            self.save_mineral_crop_image()
                                    if len(self.json_dict['Raw_Top_Category_List'])>0:
                                        self.json_dict['top_class_name']=max(self.json_dict['Raw_Top_Category_List'],key=self.json_dict['Raw_Top_Category_List'].count)
                                        

                                    if len(self.json_dict['Raw_Front_Category_List'])>0:
                                        self.json_dict['front_class_name']=max(self.json_dict['Raw_Front_Category_List'],key=self.json_dict['Raw_Front_Category_List'].count)
                            
                                    print(self.json_dict['id'],' : ',' ',self.json_dict['front_class_name'],' ',self.json_dict['top_class_name'])
                                    self.save_json()
                                    logging.info(f"Transaction : {str(self.json_dict['id'])} :Previous Transaction Json Saved")
                                if self._may_start_new_transaction(multi_box_escape=multi_box_escape):
                                    reason = 'multi_box' if multi_box_escape else 'count_change'
                                    self._start_new_transaction(reason=reason)
                                    if multi_box_escape:
                                        self.multi_box_escape_used = True
                                        # Still suppress until ROI empty so A+B don't spam more txns
                                        self.waiting_for_roi_exit = True
                                        self.roi_empty_frames = 0
                                        logging.info(
                                            f'Multi-box new txn (mining_front_in_roi={mining_n}); '
                                            f'suppress stays on until ROI empty'
                                        )
                                else:
                                    # Ignore Double Entries / suppress active
                                    if Suppress_Until_ANPR_ROI_Empty and self.waiting_for_roi_exit and not multi_box_escape:
                                        logging.debug(
                                            f'New txn blocked by ROI suppress '
                                            f'(mining_front_in_roi={mining_n})'
                                        )
                                    pass
                                    # print("Double Enrty---><=0:",int(start_time-self.transaction_start_time))
                                    # ... commented double_entry=Yes path kept historically in git
                            self.vehicle_count=self.yolo_output['Count']
                            # print("self.top_process_start , self.yolo_output['Capture_Top'] , top_raw_image_count,self.top_raw_image_count_thresh : ",self.top_process_start , self.yolo_output['Capture_Top'] , self.top_raw_image_count,self.top_raw_image_count_thresh)
                            if self.top_process_start and self.yolo_output['Capture_Top'] and self.top_raw_image_count<=self.top_raw_image_count_thresh:
                                self.top_frame=self.anpr_frame
                                if self.yolo_output['Top_IN_ROI']==True:
                                    self.top_pred_frame=self.Vehicle_NP_Detection_Frame
                                if len(self.yolo_output['Raw_Top_Category_List'])>0:
                                    self.json_dict['Raw_Top_Category_List'].extend(self.yolo_output['Raw_Top_Category_List'])
                                else:
                                    self.json_dict['Raw_Top_Category_List'].extend(['Not_Found'])
                                self.save_top_image(self.top_raw_image_count)
                                logging.info(f"Transaction : {str(self.json_dict['id'])} : Top Image Saved")
                                self.top_raw_image_count+=1
                            
                            # print("Vehicle_Number_Crop_List : ",len(self.yolo_output['Vehicle_Number_Crop_List'])," : self.final_text : ",self.final_text)
                            if len(self.yolo_output['Vehicle_Number_Crop_List'])>0 :#and self.json_dict['ANPR_frames_process']<max_frame_process_limit
                                self.json_dict['ANPR_frames_process']+=1
                                # self.ANPR()
                                self.save_number_plate_crop_image()
                                self.number_plate_crop_count+=1
                                logging.info(f"Transaction : {str(self.json_dict['id'])} : Number Plate Crop Saved")

                            if self.yolo_output['Front_Class']!='unclassified':
                                self.json_dict['Raw_Front_Category_List'].append(self.yolo_output['Front_Class'])
                                # self.json_dict['front_class_name']=
                            self.last_front_class_name_list=self.json_dict['Raw_Front_Category_List']
                            self.last_Raw_Top_Category_List=self.json_dict['Raw_Top_Category_List']
                        
                    else:
                        #Vehicle Not Found (or not Front_IN_ROI)
                        # pass
                        self.Vehicle_Not_Found+=1
                        self._update_suppress_on_empty_roi()
                        # print('self.id_processed and self.vehicle_count : ',self.Vehicle_Not_Found,':',self.id_processed , self.vehicle_count)
                        if self.Vehicle_Not_Found>=vehicle_not_found_frame_count and not self.id_processed and self.vehicle_count!=0:
                            
                            self.Vehicle_Not_Found=0
                            
                            if len(self.json_dict['Raw_Top_Category_List'])>0:
                                self.json_dict['top_class_name']=max(self.json_dict['Raw_Top_Category_List'],key=self.json_dict['Raw_Top_Category_List'].count)
                                
                                if self.yolo_output['Mining_Full_Crop_Found']==True and len(self.yolo_output['Raw_Mining_Full_Crop_List'])>0:
                                    self.save_mineral_crop_image()

                            if len(self.json_dict['Raw_Front_Category_List'])>0:
                                self.json_dict['front_class_name']=max(self.json_dict['Raw_Front_Category_List'],key=self.json_dict['Raw_Front_Category_List'].count)
                            print(self.json_dict['id'],' : ',self.json_dict['front_class_name'],' ',self.json_dict['top_class_name'])
                            self.save_json()
                            logging.info(f"Transaction : {str(self.json_dict['id'])} :Else Json Saved")
                            self._arm_suppress_until_roi_empty(reason='else_json')
                            if self.save_raw_video:
                                self.save_raw_anpr_video()

                            self.reset_partial_parameters()
                            # self.read_frames_anpr(reintialized=True)
                            # self.read_frames_top(reintialized=True)
                            # self.rest_parameters()
                        elif self.Vehicle_Not_Found>=vehicle_not_found_frame_count:
                            self.Vehicle_Not_Found=0

                if self.yolo_output['Mining_Full_Crop_Found']==True:
                        self.save_mineral_crop_image()
                        logging.info(f"Transaction : {str(self.json_dict['id'])} : Mineral Crop Saved")
                if len(self.json_dict['Raw_Front_Category_List'])>0:
                    self.json_dict['front_class_name']=max(self.json_dict['Raw_Front_Category_List'],key=self.json_dict['Raw_Front_Category_List'].count)
                
                if len(self.json_dict['Raw_Top_Category_List'])>0:
                        self.json_dict['top_class_name']=max(self.json_dict['Raw_Top_Category_List'],key=self.json_dict['Raw_Top_Category_List'].count)
                    
                if not self.id_processed and self.json_dict['front_class_name']!='' and \
                ((self.json_dict['front_class_name'] in mining_vehicle_list and self.json_dict['top_class_name']!='')) and self.number_plate_crop_count>=3:#
                    if self.Override_Done==False:
                        self.id_processed=True
                        self.json_dict['Processed']=True
                        print(self.json_dict['id'],' : ',self.json_dict['front_class_name'],' ',self.json_dict['top_class_name'])
                        self.save_json(True)
                        logging.info(f"Transaction: {str(self.json_dict['id'])} :Final Json Saved")
                        self.Override_Done=True
                        logging.info(f"Transaction Completed: {str(self.json_dict['id'])}")
                        self._arm_suppress_until_roi_empty(reason='final_json')
                        

                    if self.save_raw_video:
                        self.save_raw_anpr_video()
                    self.reset_partial_parameters()


                if self.show_live_video:
                    cv2.putText(self.Vehicle_NP_Detection_Frame,f'id:{str(self.id)}', 
                    (100,100), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    fontScale,
                    fontColor,
                    thickness,
                    lineType)
                    self.show_anpr_video()
                    if cv2.waitKey(20) & 0xFF == ord('q'):
                        break
                
                    


                                
                # print('================================================================')

            except Exception as e:
                logging.error('Front Top main code Error : '+str(e))
                if 'Input/output error' in  str(e):
                    logging.error('Front Top main code Error : Front_Top.py Restarted')
                    os.execv(sys.executable, ['python3'] + sys.argv)
                if check_error:
                    print('Front Top : ',e)
                continue

        

        

        


            
if __name__=='__main__':
    main().main()

#python3 -m nuitka --module --clang --no-pyi-file  hello_world.py