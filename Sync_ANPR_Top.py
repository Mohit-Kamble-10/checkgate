
from glob import glob
import datetime
import time
import os
import sys
import json
from configs import config
import shutil
from multiprocessing import Process
from Top_Inference_Script import main as Top_Inferance_Main
import logging




lane_no=sys.argv[1] # string 1,2,3

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

class main():
    def __init__(self) -> None:
        self.copied_images={}
        self.copied_cross_images={}
        self.copy_top_images_transaction_count=0
        try:
            with open('/home/aikernel/metadata/ANPR_Top_Sync.json', 'r') as f:
                self.Time_Slot = json.load(f)
            print('self.Time_Slot : ',self.Time_Slot)
        except FileNotFoundError:
            print("Error: The file '/home/aikernel/metadata/ANPR_Top_Sync.json' was not found.")
        
        # {transaction_id=[image_path]}
        # self.Top_Inferance_Main_obj=Top_Inferance_Main()



    def check_time(self,current_time):
        day_start = 6
        day_end = 18
        current_hour = current_time.hour
        if day_start <= current_hour < day_end:
            return 'day'
        else:
            return 'night'

    def find_files_created_within_last_minute(self,folder_path):
        current_time = datetime.datetime.now()
        one_minute_ago = current_time - datetime.timedelta(minutes=5)
        recent_files = []
        # print('folder_path : ',folder_path)
        # print('self.check_time : ',self.check_time(current_time))
        if self.check_time(current_time)=='day' and False:
            # Day time code
            for file_path in glob(folder_path):
                top_class_name=''
                Front_Top_json_path=file_path+'/json/Front_Top_output.json'
                if os.path.exists(Front_Top_json_path) and \
                len(glob(file_path+'/raw/top_image**'))==0 and \
                not os.path.exists(file_path+'/json/Top_Detection_output.json') and \
                not os.path.exists(file_path+'/json/response.json'):
                

                    
                    if os.path.exists(Front_Top_json_path):
                        with open(Front_Top_json_path) as json_file:
                            Front_Top_json_data = json.load(json_file)
                        top_class_name=Front_Top_json_data['top_class_name']
                    
                    
                    if top_class_name=='mining_full':
                        creation_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
                        if creation_time > one_minute_ago:
                            recent_files.append(file_path)
                            # print('recent_files : ',recent_files)
                    else:
                        
                        self.Top_Inferance_Main_obj.inferance(file_path,lane_no=-1,non_mining=True)
                        # transaction_datetime=Front_Top_json_data['datetime']
                        # datetime_format= "%d_%m_%Y_%H_%M_%S"
                        # transaction_datetime = datetime.datetime.strptime(transaction_datetime, datetime_format)
        else:
            # Keep filling buffer until Top inference claims the txn (old semantics).
            # sleep in main() is 0.5s — do not use 0.001s (CPU spin).
            for file_path in glob(folder_path):
                Front_Top_json_path=file_path+'/json/Front_Top_output.json'
                Top_Detection_json_path=file_path+'/json/Top_Detection_output.json'
                if os.path.exists(Front_Top_json_path) and \
                not os.path.exists(Top_Detection_json_path):
                    creation_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
                    if creation_time > one_minute_ago:
                        recent_files.append(file_path)

        return recent_files   
    def get_time_range(self,base_time):
        # Convert the base_time to a datetime object
        datetime_format= "%d_%m_%Y_%H_%M_%S"
        final_list=[]
        if base_time!='':
            base_time_dt = datetime.datetime.strptime(base_time, datetime_format)

            
            # Calculate the next two seconds
            if config.Fast_Moving:
                # Calculate the previous two seconds
                # prev_two_sec = [base_time_dt - datetime.timedelta(seconds=i) for i in range(1, 2)]
                start_time,end_time=self.Time_Slot['Fast_Moving'][0],self.Time_Slot['Fast_Moving'][1]
                # print("start_time,end_time : ",start_time,end_time)
                next_two_sec = [base_time_dt + datetime.timedelta(seconds=i) for i in range(start_time, end_time)]
                # final_list.extend([base_time_dt])
                final_list.extend(next_two_sec)
            else:
                start_time,end_time=self.Time_Slot['Slow_Moving'][0],self.Time_Slot['Slow_Moving'][1]
                next_two_sec = [base_time_dt + datetime.timedelta(seconds=i) for i in range(start_time, end_time)]
                final_list.extend(next_two_sec)

            for i in range(len(final_list)):
                final_list[i]=final_list[i].strftime("%d_%m_%Y_%H_%M_%S")#strftime('%H%M%S')
            return final_list
        else:
            return []
    
    def copy_top_images(self,folder_path):
        # print('folder_path : ',folder_path)
        
        start=time.time()
        second_iteration=False
        transactionId=folder_path.split('/')[-1]
        if transactionId not in self.copied_images.keys():
            self.copied_images[transactionId]=[]
            
        else: second_iteration=True
        if transactionId not in self.copied_cross_images.keys():
            self.copied_cross_images[transactionId]=[]
        Front_Top_json_path=folder_path+'/json/Front_Top_output.json'
        Sync_ANPR_TOP_json_path=folder_path+'/json/Sync_ANPR_TOP_output.json'
        response_json_path=folder_path+'/json/response.json'
        if os.path.exists(Front_Top_json_path) and not os.path.exists(response_json_path):
            with open(Front_Top_json_path) as json_file:
                Front_Top_json_data = json.load(json_file)
            transactionId=Front_Top_json_data['id']
            front_class_name=Front_Top_json_data['front_class_name']
            top_class_name=Front_Top_json_data['top_class_name']
            transaction_datetime=Front_Top_json_data['datetime']
            time_list=self.get_time_range(transaction_datetime)
            lane_series_no_dict={
                '202601':1,
                '202602':2,
                '202603':3,
                '202604':4,
                '202605':5,
                '202606':6,
                
            }
            # need to remove condition cross lane data is captured 
            Top_image_count=0
            Top_Cross_Lane_image_count=0
            #if top_class_name=='mining_full' or front_class_name=='hywa':
            
            for series,lane_no in lane_series_no_dict.items():
                if series in  folder_path:
                    image_path_list=[]
                    image_path_list_cross_lane=[]
                    if config.MachineID not in config.Sync_ANPR_Top_Exception:
                        for captured_time_ in time_list:
                            image_path_list.extend(glob(config.root_path+ f'/OUTPUT_Backup/Top_Buffer/Lane_{str(lane_no)}/top_image_{captured_time_}**'))
                        for captured_time_ in time_list:
                            if int(lane_no)==1:
                                cross_lane=2
                            else:
                                cross_lane=1
                            if config.Store_Cross_Lane_Images:
                                image_path_list_cross_lane.extend(glob(config.root_path+ f'/OUTPUT_Backup/Top_Buffer/Lane_{str(cross_lane)}/top_image_{captured_time_}**'))
                        Top_image_count+=len(image_path_list)
                        time.sleep(1)
                    else:
                        for captured_time_ in time_list:
                            image_path_list.extend(glob(config.root_path+ f'/OUTPUT_Backup/Top_Buffer/Lane_{str(1)}/top_image_{captured_time_}**'))
                        if config.Store_Cross_Lane_Images:
                            for captured_time_ in time_list:
                                image_path_list_cross_lane.extend(glob(config.root_path+ f'/OUTPUT_Backup/Top_Buffer/Lane_{str(2)}/top_image_{captured_time_}**'))
                        Top_image_count+=len(image_path_list)
                        time.sleep(1)
                    logging.info('image_path_list : '+str(len(image_path_list)))
                    for image_path in image_path_list:
                        # if image_path not in self.copied_images[transactionId]['top_images_path_list']:
                        if image_path not in self.copied_images[transactionId]:
                            shutil.copy(image_path,folder_path+'/raw/')
                            self.copied_images[transactionId].append(image_path)
                            # print(folder_path,' : copied')
                    if config.Store_Cross_Lane_Images:
                        Top_Cross_Lane_image_count+=len(image_path_list_cross_lane)
                        logging.info('image_path_list_cross_lane : '+str(len(image_path_list_cross_lane)))
                    
                        for index,image_path in enumerate(image_path_list_cross_lane):
                            if image_path not in self.copied_cross_images[transactionId]:
                                image_name=image_path.split('/')[-1]
                                shutil.copy(image_path,folder_path+'/raw/Cross_Lane_'+image_name)
                                self.copied_cross_images[transactionId].append(image_path)
                                # print(folder_path,' : cross Lane copied : '+image_name)
                
                    # self.copied_images[transactionId]['top_images_path_list'].extend(image_path_list)
                    # self.copied_images[transactionId]['top_cross_lane_images_path_list'].extend(image_path_list_cross_lane)
                    # print(self.copied_images)
                        
            # if len(self.copied_images)>=50:
            #     self.copied_images={}
            
            
            final_data={'transactionId':transactionId,'Top_image_count':Top_image_count,'Top_Cross_Lane_image_count':Top_Cross_Lane_image_count,'execution_time':time.time()-start}
            logging.info(f"transactionId : {transactionId} Top_image_count : {str(Top_image_count)} Top_Cross_Lane_image_count : {str(Top_Cross_Lane_image_count)}")
            if second_iteration:
                with open(Sync_ANPR_TOP_json_path, 'w') as f:
                    json.dump(final_data, f) 
            
            self.copy_top_images_transaction_count+=1
            if self.copy_top_images_transaction_count==100:
                self.copied_cross_images={}
                self.copied_images={}
                


    def main(self):
        
        folder_path = config.root_path+f'/output/*20260{lane_no}*'
        # print(folder_path)
        while True:
            
            recent_files = self.find_files_created_within_last_minute(folder_path)
            
            # print('recent_files : ',recent_files)
            for file_path in recent_files[:]:
                try:
                    # print('file_path : ',file_path)
                    logging.info('file_path : '+file_path)
                    self.copy_top_images(file_path)     
                except Exception as e:
                    logging.error('file_path : ',file_path +': '+str(e))
                    if 'Input/output error' in  str(e):
                        logging.error('Sync_ANPR_Top code Error : Sync_ANPR_Top.py  Restarted')
                        os.execv(sys.executable, ['python3'] + sys.argv)
                    
                    if config.check_error:
                        print('Sync ANPR_Top : ',e)
                    continue

            time.sleep(0.5)
if __name__=='__main__':
    main().main()
