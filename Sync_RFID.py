from glob import glob
import datetime
import time
import os
import json
from configs import config
import sys 
import shutil
import logging

lane_no=sys.argv[1] # string 1,2,3 lane no
now = datetime.datetime.now()
start_script_datetime=now.strftime("%d_%m_%Y_%H_%M")

Current_log_path=config.root_path+f"/logs/Sync_RFID_Logs_{str(lane_no)}.log"
backup_logs_path=config.root_path+f"/logs/Sync_RFID_Logs/"
os.makedirs(backup_logs_path,exist_ok=True)
if os.path.exists(Current_log_path):
    shutil.move(Current_log_path,backup_logs_path+f"Sync_RFID_Logs_{str(lane_no)}_{start_script_datetime}.log")

FORMAT = "%(asctime)s: %(filename)s: %(levelname)s :%(lineno)5s:: - %(funcName)10s() :  %(message)s"
logging.basicConfig(filename=Current_log_path,
                    format=FORMAT,
                    filemode='a',
                    level=logging.DEBUG, # Set logging level
                    force=True)

class main():
    def __init__(self) -> None:
        pass


    def find_files_created_within_last_minute(self,folder_path):
        current_time = datetime.datetime.now()
        one_minute_ago = current_time - datetime.timedelta(minutes=2000)
        recent_files = []
        # print('folder_path : ',folder_path)
        for file_path in glob(folder_path):
            if os.path.exists(file_path+'/json/Front_Top_output.json') and \
                not os.path.exists(file_path+'/json/RFID_output.json'):# and \
                # not os.path.exists(file_path+'/json/response.json'):
                creation_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
                if creation_time > one_minute_ago:
                    recent_files.append(file_path)
            # else:
            #     print('File not exist : ',file_path)

        return recent_files   
    def get_time_range(self,base_time):
        # Convert the base_time to a datetime object
        base_time_dt = datetime.datetime.strptime(base_time, "%d_%m_%Y_%H_%M_%S")

        # Calculate the previous two seconds
        prev_two_sec = [base_time_dt - datetime.timedelta(seconds=i) for i in range(1, 3)]

        # Calculate the next two seconds
        next_two_sec = [base_time_dt + datetime.timedelta(seconds=i) for i in range(1, 3)]

        final_list=[]
        final_list.extend(prev_two_sec)
        final_list.extend([base_time_dt])
        final_list.extend(next_two_sec)
        for i in range(len(final_list)):
            final_list[i]=final_list[i].strftime("%d_%m_%Y_%H_%M_%S")
        return final_list
    def find_strings_with_substring(self,strings_list, substring):
        return [string for string in strings_list if substring in string]
    def copy_RFID_Data(self,folder_path):
        # print('folder_path : ',folder_path)
        # start=time.time()
        Front_Top_json_path=folder_path+'/json/Front_Top_output.json'
        RFID_logs_file_path=config.root_path+f"/logs/syrotech_rfid_logs_{str(lane_no)}.txt"
        RFID_output_path=folder_path+'/json/RFID_output.json'
            
        if os.path.exists(RFID_logs_file_path):
            lines_list = open(RFID_logs_file_path,"r").readlines()
            if len(lines_list)>50:
                last_raws_list=lines_list[-50:]
            else:
                last_raws_list=lines_list
        else:
            # print("Sync RFID Log File Not Found....")
            return
        if os.path.exists(Front_Top_json_path):
            try:
                with open(Front_Top_json_path) as json_file:
                    Front_Top_json_data = json.load(json_file)
            except Exception as e:
                Front_Top_json_data={'datetime':''}
                print('Sync RFID : Front_Top_json_data issue ')
        else:
            print("Front_Top_json_path  Not Found....")
        time_list=[]
        datetime=Front_Top_json_data['datetime']
        if datetime!='':
            time_list=self.get_time_range(datetime)
        # if '202401' in  folder_path:
        final_rfid_data=[]
        for captured_time_ in time_list:
            # print('captured_time : ',captured_time_)
            found_data=self.find_strings_with_substring(last_raws_list,captured_time_)
            if len(found_data)>0:
                final_rfid_data.append(found_data)
        print("final_rfid_data : lane_no :",lane_no,RFID_output_path,len(final_rfid_data))
        logging.info("len(final_rfid_data) : "+str(len(final_rfid_data)))
        with open(RFID_output_path, 'w') as f:
            json.dump({'RFID_data':final_rfid_data}, f)

        
    def main(self):
        
        folder_path = config.root_path+f'/output/*20260{str(lane_no)}*'
        
        while True:
            
            recent_files = self.find_files_created_within_last_minute(folder_path)
            # print("recent_files : ",len(recent_files))
            for file_path in recent_files:
                
                # print("file_path : ",file_path)
                try:
                    # time.sleep(2)
                    logging.info("file_path : Started"+file_path)
                    self.copy_RFID_Data(file_path)
                except Exception as e:
                    logging.error(f"file_path : error {file_path} : {str(e)}")
                    if 'Input/output error' in  str(e):
                        logging.error('Sync_RFID code Error : Sync_RFID.py  Restarted')
                        os.execv(sys.executable, ['python3'] + sys.argv)
                    
                    if config.check_error:
                        print('Sync RFID : ',e)
                        # raise
                    
                    continue
                # break
            # break
            time.sleep(0.2)
if __name__=='__main__':
    main().main()
