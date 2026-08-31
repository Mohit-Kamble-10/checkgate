import sys
sys.path.append('../')
import os
from glob import glob
import datetime
import time
import os
from glob import glob
import shutil
import cv2
import json
from config_operations import Source_path as source_path

def get_creation_time(folder):
    return os.path.getctime(folder)

def create_videos(sorted_image_path_list,dest_path):

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Define the codec
    h,w,_=cv2.imread(sorted_image_path_list[0]).shape
    video = cv2.VideoWriter(dest_path, fourcc, 5.0, (w, h))  # Set FPS to 30

    for image_path in sorted_image_path_list:  
        try:
            image=cv2.imread(image_path)
            video.write(image)  
        except Exception as e:
            continue
    video.release()
def remove_image(sorted_image_path_list):
    for image_path in sorted_image_path_list:
        os.remove(image_path)
def main_create_video(backup_date_folder_path):
    transaction_path_list=sorted(glob(backup_date_folder_path+'/**'))
    print('transaction_path_list : ',len(transaction_path_list))
    top_count=0
    top_pred_count=0
    resized_count=0
    top_image_path_list_count=0
    Cross_Lane_top_image_path_list_count=0
    pred_top_image_path_list_count=0
    for index,path in enumerate(transaction_path_list):
        try:
            # print('path : ',path)
            if index%100==0:
                print(index)
            dest_path=path+'/video/'
            request_path_raw=path+'/json/request_raw.json'
            os.makedirs(dest_path,exist_ok=True)
            top_image_path_list=sorted(glob(path+'/raw/top_image**')) 
            
            # print("top_image_path_list : ",len(top_image_path_list))
            Cross_Lane_top_image_path_list=sorted(glob(path+'/raw/Cross_Lane**'))
            # print("Cross_Lane_top_image_path_list : ",len(Cross_Lane_top_image_path_list))
            pred_top_image_path_list=sorted(glob(path+'/prediction/pred_top_image**'))
            # print("pred_top_image_path_list : ",len(pred_top_image_path_list))
            
            top_video_name='top_video_5fps.mp4'
            pred_video_name='pred_top_video_5fps.mp4'
            cross_lane_video_name='cross_lane_top_video_5fps.mp4'
            if len(top_image_path_list)>0:
                create_videos(top_image_path_list,dest_path+top_video_name)
                top_image_path_list_count+=len(top_image_path_list)
                remove_image(top_image_path_list)
            if len(Cross_Lane_top_image_path_list)>0:
                create_videos(Cross_Lane_top_image_path_list,dest_path+cross_lane_video_name)
                
                Cross_Lane_top_image_path_list_count+=len(Cross_Lane_top_image_path_list)
                remove_image(Cross_Lane_top_image_path_list)
            if len(pred_top_image_path_list)>0:
                create_videos(pred_top_image_path_list,dest_path+pred_video_name)
                pred_top_image_path_list_count+=len(pred_top_image_path_list)
                remove_image(pred_top_image_path_list)
            if os.path.exists(request_path_raw):
                with open(request_path_raw) as json_file:
                    json_data = json.load(json_file)
                if json_data['final_top_class']!='mining_full':
                    resized_folder_path=path+f'/raw_resized/' 
                    if os.path.exists(resized_folder_path):
                        shutil.rmtree(resized_folder_path)
                        resized_count+=1

                for i in range(1,4):
                    top_image_anpr_camera=path+f'/raw/Top_Raw_{str(i)}.jpg' 
                    top_image_anpr_camera_pred=path+f'/prediction/Top_Pred_{str(i)}.jpg' 
                    if os.path.exists(top_image_anpr_camera):
                        os.remove(top_image_anpr_camera)
                        top_count+=1
                    if os.path.exists(top_image_anpr_camera_pred):
                        os.remove(top_image_anpr_camera_pred)
                        top_pred_count+=1
        except Exception as e:
            continue
                       
    print(f'top_image_path_list count : ',top_image_path_list_count, " Cross_Lane_top_image_path_list count : ",Cross_Lane_top_image_path_list_count,' pred_top_image_path_list Count : ',pred_top_image_path_list_count)
    print(f'Top count : ',top_count, " Prediction count : ",top_pred_count,' Resized Count : ',resized_count)

def create_videos_from_images():
    upload_backup_days=15
    now = datetime.datetime.now()
    for day in range(1,upload_backup_days+1):
        target_date=(now-datetime.timedelta(days=day))
        # day_str=target_date.strftime("%d%m%Y")
        input_folder_name=source_path+'/OUTPUT_Backup/'+target_date.strftime("%b_%Y")+'/'+target_date.strftime("%d-%m-%Y")+'/'
        print('input_folder_name : ',input_folder_name)
        main_create_video(input_folder_name)
        # break




if __name__=="__main__":
    create_videos_from_images()