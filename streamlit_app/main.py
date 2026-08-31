import sys 
sys.path.append('/home/aikernel/metadata')
import master_config 
import cv2
import numpy as np
import streamlit as st
import time
import pandas as pd
import plotly.figure_factory as ff
import datetime
from glob import glob
import pandas as pd
import subprocess
from live_streaming import main_live_streaming
from transaction_info import get_last_n_transaction
from search_upload_images import upload_transaction_images
from logs import get_logs
from model_loaded import model_loaded_main
top_categories =['Covered', 'Non-Mining', 'Mining_Full', 'Mining_Empty','Image_Not_Found']
front_categories =['Truck','Hywa','Bus','Car','Other']
mineral_categories =['Sand','Soil','Brown_Sand','Stone','Khadi','Gitti']

st.set_page_config(page_title="My App", page_icon="🚀", layout="wide")

main_option = st.sidebar.selectbox(
    "Menu",
    # ("Dashbord", "Live Surveillance","Transaction","Logs","Health Check", "Settings"),
    ( "Live Surveillance","Transaction","Upload Images","Logs","Model Info","Settings"),
    # index=None,
    placeholder="Live Surveillance",
)

if main_option:
    st.empty()
    st.title(main_option+" : By AIKernel")
    st.subheader(f"Location : {master_config.LocationName}")

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
    main_live_streaming()
elif main_option == "Transaction":
    get_last_n_transaction()
elif main_option == "Upload Images":
    upload_transaction_images()

elif main_option == "Logs":
    get_logs()
elif main_option == "Model Info":
    model_loaded_main()

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
    # st.subheader("***To configure LEDs for the application:***")
    # on = st.toggle("LED ON",value=True)
    # if on:
    #     st.toast('LED ON!!!', )
    #     time.sleep(.5)
        
    st.subheader("***To Start the AI application:***")
    if st.button("Start Code"):
        st.toast('Code Started!!!', )
        with st.spinner("Starting... please wait"): 
            subprocess.run(["/home/aikernel/src/crons/main.sh"])
            time.sleep(2)
            st.success("Code Started.")
    st.subheader("***To Stop the AI application:***")
    if st.button("Stop Code"):
        st.toast('Code stopped!!!', )
        st.success("Code stopped.")
        subprocess.run(["/home/aikernel/src/crons/stop_code.sh"])

        
    st.subheader("***To Push latest health check:*** ")
    if st.button("Push Health Check", type="secondary"):
        st.toast('Health Check Sent!!!', )
        time.sleep(.5)
        with st.spinner("Pushing... please wait"): 
            subprocess.run(["/home/aikernel/src/crons/health_check_main.sh"])
            st.success("Letest Health Check Published.")
    
    st.subheader("***To Get latest config:*** ")
    if st.button("Get Config", type="secondary"):
        st.toast('Get Config!!!', )
        time.sleep(.5)
        with st.spinner("Pulling Data... please wait"): 
            subprocess.run(["python3", "/home/aikernel/src/general_operations/get_raw_jsons.py"])
            st.success("All Config data pulled.")
            st.warning("Restart the code.(Stop -> Start)")
            
        
        


if __name__ == "__main__":
    pass
# streamlit run main.py --server.port 1135