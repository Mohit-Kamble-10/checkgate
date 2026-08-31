
import streamlit as st
import time
from glob import glob


logs_path='/home/aikernel/logs/'

def tail_log_file(file_path, n=10):
    """
    Mimics the behavior of 'tail -n' by returning the last n lines of a file.
    """
    with open(file_path, "r") as file:
        lines = file.readlines()
        return lines[-n:] if len(lines) >= n else lines
    
def get_logs():
    logs_list=glob(logs_path+'/*.log*')
    st.subheader(f'Log Details :')
    log_placeholder = st.empty()
    log_dict={}
    for log_path in logs_list:
        log_name=log_path.split('/')[-1]
        log_dict[log_name]=log_path
    # st.text(log_dict)
    option = st.sidebar.selectbox(
                "Logs",
                log_dict.keys(),
                index=None,
                placeholder="Select Log File...",
            )
    option_line_count = st.sidebar.selectbox(
                "Line Count",
                [10,25,50,100],
                index=0,
                # placeholder="Select Log File...",
            )
    
    if st.sidebar.button("Submit",type="primary") and option:
        while True:
            try:
                # st.write(option +' : '+log_dict[option] )
                # Fetch the last n lines from the log file
                logs = tail_log_file(log_dict[option],int(option_line_count))
                
                # Update the placeholder text with the new logs
                log_placeholder.text("".join(logs))
                
                # Sleep for a short duration to prevent excessive CPU usage
                time.sleep(1)
            except FileNotFoundError:
                log_placeholder.text("Log file not found. Please check the file path.")
                time.sleep(5)