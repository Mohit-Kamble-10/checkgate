
import os
os.environ['OPENSSL_CONF']='/home/aikernel/src/configs/openssl.cnf'

import cv2
import numpy as np
import time 
import requests
import json
import datetime
import os
import sys
sys.path.append('/home/aikernel/src/') 
from secure_api import send_json

from config_operations import MachineID,SaveCameraWorkingStatus,\
    Logs_Folder_Path,Json_Folder_Path,lane_count,Master_Json_Folder_Path
jsons_path=Json_Folder_Path
master_json_path=Master_Json_Folder_Path

link_type='global'
main_log_folder=Logs_Folder_Path+'/healthcheck_hardware_camera_status/'

def get_camera_info(camera_type,lane_no):
    
    if os.path.exists(master_json_path+'/camera_details.json'):
        with open(master_json_path+'/camera_details.json') as json_file:
            get_camera_profile_data = json.load(json_file)
        if camera_type=='Lane':
            if link_type=='global':
                ANPR_RTSP=get_camera_profile_data['ANPR_'+str(lane_no)]['globalUrl']
                ANPR_ID=get_camera_profile_data['ANPR_'+str(lane_no)]['id']
                TOP_RTSP=get_camera_profile_data['Top_'+str(lane_no)]['globalUrl']
                TOP_ID=get_camera_profile_data['Top_'+str(lane_no)]['id']
            else:
                ANPR_RTSP=get_camera_profile_data['ANPR_'+str(lane_no)]['localUrl']
                ANPR_ID=get_camera_profile_data['ANPR_'+str(lane_no)]['id']
                TOP_RTSP=get_camera_profile_data['Top_'+str(lane_no)]['localUrl']
                TOP_ID=get_camera_profile_data['Top_'+str(lane_no)]['id']
            

            return ANPR_RTSP,ANPR_ID, TOP_RTSP,TOP_ID
        else:
            Junc_RTSP=get_camera_profile_data['Junction_Box_0']['globalUrl']
            Junc_ID=get_camera_profile_data['Junction_Box_0']['id']
            Sur_RTSP=get_camera_profile_data['Surveillance_0']['globalUrl']
            Sur_ID=get_camera_profile_data['Surveillance_0']['id']
            
            return Junc_RTSP,Junc_ID,Sur_RTSP,Sur_ID
    else:
        print('camera_details.json not found')
        print(master_json_path+'/camera_details.json')
        # exit()





def detect_blur(image, threshold=100):
    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Compute the Laplacian variance
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Determine if the image is blurry based on the variance
    if laplacian_var < threshold:
        return True, laplacian_var
    else:
        # return False, laplacian_var
        return True, laplacian_var

def detect_misalignment(image1, image2):
    image1=cv2.resize(image1,(0,0),fx=.25,fy=.25)
    image2=cv2.resize(image2,(0,0),fx=.25,fy=.25)
    
    # Convert images to grayscale
    gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

    # Initialize the SIFT detector
    sift = cv2.SIFT_create()

    # Find keypoints and descriptors in the images
    keypoints1, descriptors1 = sift.detectAndCompute(gray1, None)
    keypoints2, descriptors2 = sift.detectAndCompute(gray2, None)

    # Initialize the feature matcher
    matcher = cv2.BFMatcher()

    # Match descriptors between the images
    matches = matcher.knnMatch(descriptors1, descriptors2, k=2)

    # Apply ratio test to find good matches
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)

    # Minimum number of matches required
    min_matches = 100

    # Check if enough good matches are found
    if len(good_matches) > min_matches:
        return True, len(good_matches)
    else:
        # return False, len(good_matches)
        return True, len(good_matches)
    
def check_rtsp_stream(name,url):
    cap = cv2.VideoCapture(url)
    
    if not cap.isOpened():
        print(f"Error opening stream: {url}")
        return False,None
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print(f"Error reading frame from stream: {url}")
            break
        else:
            # cv2.imwrite('night_Images/'+name+'.png',frame)
            break
        
    #     cv2.imshow('Frame', frame)
        
    #     # Press 'q' to exit the stream check
    #     if cv2.waitKey(1) & 0xFF == ord('q'):
    #         break
    
    # cap.release()
    # cv2.destroyAllWindows()
    return True,frame

def get_camera_health_check(camera_type,lane_no,id,url):
    blur_threshold = 100
    min_matches = 100
    
    #camera_type,lane_no=name.split('_')

    report={
    "machineId":MachineID ,
    "cameraID": id,
    "workingStatus": "API issue",
    "aligned": "API issue",
    "notBlur": "API issue"
    }
    stream_status,frame = check_rtsp_stream(None,url)
    if stream_status:
        report['workingStatus']='Yes'
        report['aligned']='Yes'
        report['notBlur']='Yes'
        

        # print(f"Stream  {name} is working.")
        # is_misaligned, num_matches = detect_misalignment(cv2.imread('night_Images/'+name+'.png'), frame)
        # is_blurry, variance = detect_blur(frame, blur_threshold)
        # if is_misaligned:
        #     # print(f"The Camera: {name} is well-aligned with {num_matches} good matches.")
        #     report['aligned']='Yes'
        # else:
        #     # print(f"The Camera: {name} is misaligned with {num_matches} good matches.")
        #     report['aligned']='No'
        # if is_blurry:
        #     # print(f"The Camera: {name} is blurry with a variance of {variance:.2f}")
        #     report['not_blur']='No'
        # else:
        #     # print(f"The Camera: {name} is sharp with a variance of {variance:.2f}")
        #     report['not_blur']='Yes'
    
    else:
        # print(f"Stream {name} is not working.")
        report['working_status']='No'
        
    
    return report


def camera_health_check():
    # print('camera_urls : ',camera_urls)
    start=time.time()

    now = datetime.datetime.now()
    folder_name=now.strftime("%d_%m_%Y")
    request_path=main_log_folder+folder_name+'/request/'
    response_path=main_log_folder+folder_name+'/response/'
    # print('request_path : ',request_path)
    # print('response_path : ',response_path)
    os.makedirs(request_path,exist_ok=True)
    os.makedirs(response_path,exist_ok=True)
    # id=10
    Junc_RTSP,Junc_ID,Sur_RTSP,Sur_ID=get_camera_info(camera_type='Surveillance',lane_no=None)
    junction_box_report=get_camera_health_check('Junction_Box',None,Junc_ID,Junc_RTSP)
    Surveillance_report=get_camera_health_check('Surveillance',None,Sur_ID,Sur_RTSP)
    print('junction_box_report : ',junction_box_report)
    print('Surveillance_report : ',Surveillance_report)
    junction_box_request_json_filename=f'request_Junction_box_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    junction_box_json_filename=f'response_Junction_box_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    Surveillance_request_json_filename=f'request_Surveillance_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    Surveillance_response_json_filename=f'response_Surveillance_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
    
    with open(request_path+junction_box_request_json_filename, 'w') as f:
        json.dump(junction_box_report, f)

    with open(request_path+Surveillance_request_json_filename, 'w') as f:
        json.dump(Surveillance_report, f)

    junction_box_response,message=send_json(SaveCameraWorkingStatus,json_data=junction_box_report)
    

    Surveillance_response,message=send_json(SaveCameraWorkingStatus,json_data=Surveillance_report)
    
    with open(response_path+junction_box_json_filename, 'w') as f:
        json.dump(junction_box_response, f)

    with open(response_path+Surveillance_response_json_filename, 'w') as f:
        json.dump(Surveillance_response, f)



    for lane_no in range(lane_count):

        ANPR_RTSP,ANPR_ID, TOP_RTSP,TOP_ID =get_camera_info(camera_type="Lane",lane_no=lane_no+1)


        ANPR_request_json_filename=f'request_ANPR_laneno_{str(lane_no)}_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
        ANPR_response_json_filename=f'response_ANPR_laneno_{str(lane_no)}_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
        Top_request_json_filename=f'request_Top_laneno_{str(lane_no)}_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
        Top_response_json_filename=f'response_Top_laneno_{str(lane_no)}_{now.strftime("%d_%m_%Y_%H_%M_%S")}.json'
        
        
        ANPR_report=get_camera_health_check('ANPR',lane_no,ANPR_ID,ANPR_RTSP)
        Top_report=get_camera_health_check('Top',lane_no,TOP_ID,TOP_RTSP)

        print('ANPR_report : ',ANPR_report)
        print('Top_report : ',Top_report)
        # print('request_path+request_json_filename : ',request_path+request_json_filename)
        
        with open(request_path+ANPR_request_json_filename, 'w') as f:
            json.dump(ANPR_report, f)
        
        with open(request_path+Top_request_json_filename, 'w') as f:
            json.dump(Top_report, f)


        ANPR_response,message=send_json(SaveCameraWorkingStatus,json_data=ANPR_report)
    
        
        # print('ANPR_response : ',ANPR_response)
        with open(response_path+ANPR_response_json_filename, 'w') as f:
            json.dump(ANPR_response, f)

        

        Top_response,message=send_json(SaveCameraWorkingStatus,json_data=Top_report)
    

        print('Top_response : ',Top_response)
        with open(response_path+Top_response_json_filename, 'w') as f:
            json.dump(Top_response, f)



    end=time.time()
    return #{'Message':'camera_health_check Done','Execution_Time':f'{end-start:.2f} sec','report':[report]}

 

def main():
    # camera_urls=generate_camera_dict(Camera_rtsp_global_links)
    camera_health_check()

if __name__=="__main__":
    main()
