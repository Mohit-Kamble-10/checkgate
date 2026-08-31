import cv2
import numpy as np
import streamlit as st
import time
import pandas as pd
import plotly.figure_factory as ff
import datetime
from glob import glob
import pandas as pd

top_categories =['Covered', 'Non-Mining', 'Mining_Full', 'Mining_Empty','Image_Not_Found']
front_categories =['Truck','Hywa','Bus','Car','Other']
mineral_categories =['Sand','Soil','Brown_Sand','Stone','Khadi','Gitti']
rtsp_dict={
            "ANPR":["rtsp://admin:abcd2024@137.97.251.30:1111/enr/live/1/1",15],
            "Top":["rtsp://admin:abcd2024@137.97.251.30:1112/enr/live/1/1",15],
            "Gantry_sueveillance":["rtsp://admin:abcd2024@137.97.251.30:1132/Streaming/Channels/101",25],
            "Junction_Box_surveillance":["rtsp://admin:abcd2024@137.97.251.30:1131/Streaming/Channels/101",25],
        }


main_option = st.sidebar.selectbox(
    "Menu",
    ("Dashbord", "Live Surveillance","Transaction","Health Check", "Settings"),
    # index=None,
    placeholder="Dashbord",
)

if main_option:
    st.empty()
    st.title(main_option+" : By AIKernel")

if main_option=="Dashbord":
    from_date =  datetime.date.today()
    to_date =  datetime.date.today()
        
    dashboard_d = st.sidebar.date_input(
            "Select From Date and To Date",
            (from_date,to_date),
            format="DD.MM.YYYY",
        )
    st.sidebar.button("Submit",type="primary")
    front_data=pd.DataFrame({
        "Vehicle Type":front_categories,
        "Count":[200,500,300,100,250]
    })
    top_data=pd.DataFrame({
        "Top Categories":top_categories,
        "Count":[200,500,300,100,250]
    })
    mineral_data=pd.DataFrame({
        "Minerals":mineral_categories,
        "Count":[200,500,300,100,250,300]
    })
    
    col1, col2 = st.columns(2)
    # with col1:
    st.bar_chart(front_data, x="Vehicle Type", y="Count",color=['#ffffff'], stack=False,horizontal=False,height=300,)

        
    # with col2:
    st.bar_chart(top_data, x="Top Categories", y="Count",color=['#ffffff'], stack=False,horizontal=False,height=300)
    
    st.bar_chart(mineral_data, x="Minerals", y="Count",color=['#ffffff'], stack=False,horizontal=False,height=300)
    
    


    chart_data_area = pd.DataFrame(
        {
            "col1": np.random.randn(20),
            "col2": np.random.randn(20),
            "col3": np.random.choice(["A", "B", "C"], 20),
        }
    )

    chart_data = pd.DataFrame(
        np.random.randn(20, 3), columns=["col1", "col2", "col3"]
    )

        
    # Add histogram data
    x1 = np.random.randn(200) - 2
    x2 = np.random.randn(200)
    x3 = np.random.randn(200) + 2

    # Group data together
    hist_data = [x1, x2, x3]

    group_labels = ['Group 1', 'Group 2', 'Group 3']

    # Create distplot with custom bin_size
    fig = ff.create_distplot(
            hist_data, group_labels, bin_size=[.1, .25, .5])

    # Plot!
    st.plotly_chart(fig, use_container_width=True)
    st.area_chart(chart_data_area, x="col1", y="col2", color="col3")
    st.line_chart(
        chart_data,
        x="col1",
        y=["col2", "col3"],
        color=["#FF0000", "#0000FF"],  # Optional
    )


elif main_option=="Live Surveillance":
    option = st.sidebar.selectbox(
        "Camera",
        ("ANPR", "Top","Gantry_sueveillance", "Junction_Box_surveillance"),
        index=None,
        placeholder="Select Camera...",
    )
    
    

    st.write("You selected:", option)
    try:
        rtsp_url=rtsp_dict[option][0]
        fps=rtsp_dict[option][1]
    except Exception as e:
        pass

elif main_option == "Transaction":
    from_date =  datetime.date.today()
    to_date =  datetime.date.today()
    
    d = st.sidebar.date_input(
        "Select From Date and To Date",
        (from_date,to_date),
        format="DD.MM.YYYY",
    )
    transaction_input=st.sidebar.text_input('Transaction/Vehicle Number')
    front_option = st.sidebar.selectbox(
        "Front Vehicle",
        front_categories,
        index=None,
        placeholder="Select Front Side",
    )
    top_option = st.sidebar.selectbox(
        "Top View",
        top_categories,
        index=None,
        placeholder="Select Top Side",
    )

    mineral_option = st.sidebar.selectbox(
        "Minerals",
        mineral_categories,
        index=None,
        placeholder="Select Minerals",
    )
    st.sidebar.button("Submit",type="primary")
    
    
    

    
    col3, col4,col5 = st.columns([2,2,2])
    bcol1,_, bcol2,_,bcol3 = st.columns([1,1,1,1,1])

    

    with col3:
        st.button("IND0041280920240200250",)
        st.button("IND0041280920240200251")
    with col4:
        st.button("IND0041280920240200254")
        st.button("IND0041280920240200255")
    
    with col5:
        st.button("IND0041280920240200252")
        st.button("IND0041280920240300153")

    
    
    image_path_list=sorted(glob('./transactions/IND0041280920240300153/raw/**'),reverse=False)
    print('image_path_list : ',image_path_list)
    length_data=int(len(image_path_list)/3)
    print('length_data',length_data)
    
    with bcol1:
        st.button('Previous',type="primary")
    with bcol2:
        with open(image_path_list[0], "rb") as file:
            btn = st.download_button(
                label="Download",
                data=file,
                file_name="vehicle.png",
                mime="image/png",
            )
    
    with bcol3:
        st.button('Next',type="primary")
    

    count=0
    image_path_temp=[]
    st.subheader("***Transaction No: IND0041280920240300153***")
    for i in range(len(image_path_list)):
        count+=1
        if count%4 ==0:
            st.image(image_path_temp, width=250)
            image_path_temp=[]
            count=0
        else:
            image_path_temp.append(image_path_list[i])
        
elif main_option == "Health Check":

    if st.sidebar.button("Push Health Check", type="secondary"):
        st.toast('Health Check Sent!!!', )
        time.sleep(.5)

    col1, col2 ,col3= st.columns(3)
    with col1:
        st.checkbox('Machine Profile',value=True)
        st.checkbox('Machine Progress',value=True)
        st.checkbox('Lane Status',value=True)
        
        
    with col2:
        st.checkbox('Power Status',value=True)
        st.checkbox('Code Status',value=True)
        st.checkbox('Camera Status',value=True)
        
        
    with col3:
        st.checkbox('Storage Status',value=True)
        st.checkbox('Ram Status',value=True)
        
    st.subheader('_Hardware Status_')
    col1, col2 ,col3= st.columns(3)
    with col1:
        st.checkbox('GPU',value=True)
        st.checkbox('Microcontroller',value=True)
        
        
    with col2:
        st.checkbox('Heat Sensor',value=True)
        st.checkbox('Solar',value=True)
        
        
    with col3:
        st.checkbox('Power Generstion',value=True)
    
    st.subheader('_Software Status_')
    col1, col2 ,col3= st.columns(3)
    with col1:
        st.checkbox('Storage',value=True)
        st.checkbox('Ram',value=True)
        
        
    with col2:
        st.checkbox('CPU Temperature',value=True)
        st.checkbox('GPU Temperature',value=True)
        
        
    with col3:
        st.checkbox('Machine Restart',value=True)
        st.checkbox('Code Restart',value=True)
        st.checkbox('Code Running',value=True) 
    
    st.text_area("\n\n\n\n\n\n\n\n\n\n\n\n")

elif main_option == "Settings":
    st.subheader("***To configure LEDs for the application:***")
    on = st.toggle("LED ON",value=True)
    if on:
        st.toast('LED ON!!!', )
        time.sleep(.5)
        
    st.subheader("***To restart the AI application:***")
    if st.button("Restart Code"):
        st.toast('Code Restarted!!!', )
        time.sleep(.5)
    st.subheader("***To Push latest health check:*** ")
    if st.button("Push Health Check", type="secondary"):
        st.toast('Health Check Sent!!!', )
        time.sleep(.5)
        



frame_queue=[]

def read_frames_anpr(cap_anpr):
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

def main():

    frame_placeholder = st.empty()
    if st.sidebar.button("Start Streaming"):
        with st.spinner("Streaming"):
            if rtsp_url:
                # Open the RTSP stream
                cap = cv2.VideoCapture(rtsp_url)


                if not cap.isOpened():
                    st.error("Unable to open video stream. Check RTSP URL.")
                    return

                # Loop to read and display frames

                count=0
                while True:
                    data,frame,cap=read_frames_anpr(cap)
                    frame=cv2.resize(frame,(0,0),fx=0.25,fy=0.25)
                    if frame_queue:
                        frame = frame_queue.pop(0)
                        if count%5==0:
                            # print('data : ',data,count,frame.shape)

                            # Convert frame to RGB format for display
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                            # Use the frame placeholder to display the video frame
                            frame_placeholder.image(frame_rgb, channels="RGB",width=640)#use_column_width=True
                        
                        count+=1


if __name__ == "__main__":
    
    if main_option=="Live Surveillance" and option in rtsp_dict.keys():
        main()
