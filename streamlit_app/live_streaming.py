import cv2
import numpy as np
import streamlit as st
import time
import pandas as pd
import plotly.figure_factory as ff
import datetime
from glob import glob
import pandas as pd
import json
import os

# camera_config_json_path='/home/aikernel/src/configs/jsons/camera_details.json'
camera_config_json_path='/home/aikernel/metadata/camera_details.json'

def load_json():
    if os.path.exists(camera_config_json_path):
        with open(camera_config_json_path, 'r') as file:
            rtsp_dict = json.load(file)
        return rtsp_dict
    else:
        st.error('File Not Found : ',camera_config_json_path)

frame_queue=[]


def get_roi_points(roi_info, width, height):
    points = []
    # print('In get roi : ',roi_info,width,height)
    for idx,data in enumerate(roi_info.keys()):
        idx=idx+1
        # print(idx,':',roi_info[str(idx)]['xRatio'],roi_info[str(idx)]['yRatio'])
        x = int(roi_info[str(idx)]['xRatio'] * width)
        y = int(roi_info[str(idx)]['yRatio'] * height)
        points.append([x, y])
    return np.array(points, dtype=np.int32)
# Draw ROI mask
def apply_roi(frame, points):
    overlay = frame.copy()
    mask = np.zeros_like(frame, dtype=np.uint8)
    cv2.fillPoly(mask, [points], (255, 0, 0))
    return cv2.addWeighted(frame, 1.0, mask, 0.3, 0)

def read_frames_anpr(cap_anpr,rtsp_url):
    data={
        'status':0,
        'error_message':''
    }
    try:
        status, anpr_frame = cap_anpr.read()
        if status:
            frame_queue.append(anpr_frame)
            time.sleep(0.015)
            return data,anpr_frame,cap_anpr
        else:
            print("else : ")
            cap_anpr.release()
            anpr_frame=None
            time.sleep(5)
            cap_anpr = cv2.VideoCapture(rtsp_url)#cv2.VideoCapture('rtsp://103.204.39.9:8109/avstream/channel=1/stream=0.sdp') 
            status, anpr_frame = cap_anpr.read()
            frame_queue.append(anpr_frame)
            time.sleep(0.015)
            data['status']=1
            return data,anpr_frame,cap_anpr
    except Exception as e:
        data['status']=1

def main_live_streaming():
    config_dict=load_json()
    option = st.sidebar.selectbox(
                "Camera",
                config_dict.keys(),
                index=None,
                placeholder="Select Camera...",
            )
            
    if option:
        # rtsp_url=rtsp_dict[option]['globalUrl']
        st.write("You selected : "+ option)
        frame_placeholder = st.empty()
        mode = st.sidebar.radio("Select Stream Type", ["localUrl", "globalUrl"])
        display_mode = st.sidebar.radio("Display Mode", ["Raw", "With ROI"])
        stream_url = config_dict[option][mode]
        roi_info = config_dict[option]["roi_info"]
        # print('roi_info : ',roi_info)
        if st.sidebar.button("Start Streaming"):
            with st.spinner("Streaming"):
                if stream_url:
                    st.write(stream_url)
        
                    # Open the RTSP stream
                    cap = cv2.VideoCapture(stream_url)


                    if not cap.isOpened():
                        st.error("Unable to open video stream. Check RTSP URL.")
                        return

                    # Loop to read and display frames

                    count=0
                    height, width=0,0
                    while True:
                        data,frame,cap=read_frames_anpr(cap,stream_url)
                        frame=cv2.resize(frame,(0,0),fx=0.25,fy=0.25)
                        if frame_queue:
                            frame = frame_queue.pop(0)
                            if count%5==0:
                                # print('data : ',data,count,frame.shape)
                                if display_mode == "With ROI":
                                    if height==0 and width==0:
                                        height, width = frame.shape[:2]
                                    points = get_roi_points(roi_info, width, height)
                                    frame = apply_roi(frame, points)

                                # Convert frame to RGB format for display
                                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                                # Use the frame placeholder to display the video frame
                                frame_placeholder.image(frame_rgb, channels="RGB",width=640)#use_column_width=True
                            
                            count+=1
                cap.release()

if __name__ == "__main__":
    
    rtsp_url=''
    main_live_streaming(rtsp_url)
