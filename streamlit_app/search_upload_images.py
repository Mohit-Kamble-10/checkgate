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
from streamlit_js_eval import streamlit_js_eval

sys.path.append("../")
from APIS.supporting_function import upload_old_images




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


def upload_transaction_images():
    Serach_transaction=st.sidebar.text_input("Serach",max_chars=22)
        # Upload .xlsx file
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
    number_plate_flag = st.sidebar.checkbox("Number Plate Crop",key="number_plate_flag")
    anpr_flag = st.sidebar.checkbox("ANPR",key="anpr_flag")
    top_valid = st.sidebar.checkbox("Valid Top")
    top_flag = st.sidebar.checkbox("All Top")


    if len(Serach_transaction)==22:
        respose,error_message='','None'
        if number_plate_flag or anpr_flag or top_flag or top_valid:
            if st.sidebar.button("Upload Images", type="primary"):
                start_time=time.time()
                try:
                    with st.spinner("Uploading... please wait"):
                        # time.sleep(3)
                        if top_valid==True: top_flag=True
                        respose,error_message=upload_old_images(Serach_transaction,number_plate_flag,anpr_flag,top_flag,top_valid)
                        end_time=time.time()
                        if respose==0:
                            st.success("Uploading :"+' : '+Serach_transaction+' : Uploading Time : '+str(round(end_time-start_time,2)))
                        else:
                            st.error("Uploading Failed:"+' : '+Serach_transaction+f'{str(error_message)} : Uploading Time : '+str(round(end_time-start_time,2)))
                except Exception as e:
                    end_time=time.time()
                    st.error("Uploading Failed:"+' : '+Serach_transaction+f' Error : {str(e)} : Uploading Time : '+str(round(end_time-start_time,2)))
                
                
    if  uploaded_file:
        try:
            df = pd.read_excel(uploaded_file,sheet_name='sheet')
        except Exception as e:
            df=pd.DataFrame()
            st.error("Sheet not found in uploaded xlsx sheet.")
            return
        transaction_id_list=df['TransactionId'].to_list()
        st.dataframe(df)
        if number_plate_flag or anpr_flag or top_flag:
            if st.button("Upload Images", type="primary"):
                st.subheader("Transaction Count : "+str(len(transaction_id_list)))
                for index,transaction_id in enumerate(transaction_id_list):
                    start_time=time.time()
                    with st.spinner("Uploading... please wait"):
                        if top_valid==True: top_flag=True
                        respose,error_message=upload_old_images(transaction_id,number_plate_flag,anpr_flag,top_flag,top_valid)
                        
                        end_time=time.time()
                        if respose==0:
                            st.success("Uploading :"+str(index)+' : '+transaction_id+' : Uploading Time : '+str(round(end_time-start_time,2)))
                        else:
                            st.error("Uploading Failed:"+str(index)+' : '+transaction_id+f'{str(error_message)} : Uploading Time : '+str(round(end_time-start_time,2)))
                # streamlit_js_eval(js_expressions="parent.window.location.reload()")


        st.warning('In XLSX sheet "TransactionId" and sheet name is "sheet" column required.')