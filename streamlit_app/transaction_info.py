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
import sys

def show_images(transaction_id,transaction_path,image_type_option,search=False):
        if search:
            output_path=transaction_path
        else:
            output_path=f'/home/aikernel/output/{transaction_id}/'
       
        st.subheader(f"***Transaction No: {transaction_id}***")
        raw_request_json_path=output_path+f'/json/request_raw.json'
        if os.path.exists(raw_request_json_path):
            with open(raw_request_json_path, 'r') as file:
                json_dict = json.load(file)
            st.write('request_raw.json')
            st.json(json_dict,expanded=False)
        else:
            st.warning(f"File not found : {output_path}/json/request_raw.json")
        image_path_list=sorted(glob(output_path+f'/{image_type_option}/**'),reverse=True)
        if len(image_path_list)>0:
            count=0

            col1, col2= st.columns(2)
            if image_type_option!="json":
                for i in range(len(image_path_list)):
                    count+=1
                    if count%2 ==0:
                        with col1:
                            st.image(image_path_list[i])
                        count=0
                    else:
                        with col2:
                            st.image(image_path_list[i])
            else:
                json_dict={}
                for json_path in image_path_list:
                    json_name=json_path.split('/')[-1]
                    json_dict[json_name]=json_path
                json_type_option = st.sidebar.selectbox(
                    "Json",
                    sorted(json_dict.keys()),
                    index=None,
                    placeholder="Select Type...",
                )
                if json_type_option:
                    st.write(json_type_option)
                    json_path=json_dict[json_type_option]
                    with open(json_path, 'r') as file:
                        json_dict = json.load(file)
                    st.json(json_dict)
        else:
            st.warning('No Image Found')

def get_last_n_transaction():
   
    output_path='/home/aikernel/output/'
    # st.write(f"Transaction Count {len(transaction_list)}")
    
    option_lane_number = st.sidebar.selectbox(
                "Lane",
                ["ALL",'Lane_1','Lane_2','Lane_3','Lane_4'],
                index=None,
                placeholder="Select Log File...",
            )
    if option_lane_number and option_lane_number!='ALL':
        lane__dict={
            'Lane_1':'01',
            'Lane_2':'02',
            'Lane_3':'03',
            'Lane_4':'04',
        }
        st.write("Selected Lane : "+option_lane_number)
        transaction_list=glob(output_path+f'/*2026{lane__dict[option_lane_number]}*')
    else:
        transaction_list=glob(output_path+f'/**')
    st.subheader(f'Transaction Details : {len(transaction_list)}')
    if len(transaction_list)==0:
        st.warning("No Data Found...")
    option_line_count = st.sidebar.selectbox(
                "Transaction Count",
                [10,25,50,100],
                index=0,
                # placeholder="Select Log File...",
            )
    transaction_list.sort(reverse=True)
    transaction_list.sort(key=lambda x: os.stat(x).st_ctime, reverse=True)
    if len(transaction_list)>int(option_line_count):
        last_5_transaction=transaction_list[:option_line_count]
    else:
        last_5_transaction=transaction_list
    transaction_dict={}
    for transaction_path in last_5_transaction:
        transaction_number=transaction_path.split('/')[-1]
        transaction_dict[transaction_number]=transaction_path
    option = st.sidebar.selectbox(
                "Transactions",
                transaction_dict.keys(),
                index=None,
                placeholder="Select Transactions...",
            )
    image_type_option = st.sidebar.selectbox(
                "Image Type",
                ['raw','prediction','processed','top_crop','json'],
                index=None,
                placeholder="Select Type...",
            )
    
    if option and image_type_option:
        show_images(option,output_path,image_type_option)
    st.sidebar.markdown("---")
