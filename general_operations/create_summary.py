import os
import json
import pandas as pd
from glob import glob
import re
import datetime
from config_operations import MachineID,Source_path
import time 
# Base paths
base_path = "/home/aikernel/OUTPUT_Backup"
output_excel_base_path = "/home/aikernel/OUTPUT_Backup/Excelsheets"

# Regex pattern to match folders starting with month_year format (e.g., Sep_2024, Oct_2024)
# month_year_pattern = re.compile(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)_\d{4}$")

# Function to load JSON data
def load_json_data(file_paths):
    data_list = []
    for file_path in file_paths:
        try:
            if os.path.getsize(file_path) > 0:  # Check if the file is not empty
                with open(file_path, 'r') as file:
                    try:
                        json_data = json.load(file)
                        data_list.append(json_data)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON in {file_path}: {e}")
            else:
                print(f"File is empty: {file_path}")
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    return data_list

# Function to extract date from transactionId in the format "dd-mm-yyyy"
def convert_to_date_from_transaction_id(transaction_id):
    try:
        # Extract date portion from transactionId, assuming the date is the 8 characters after the first 7 characters (e.g., '30092024')
        date_str = transaction_id[7:15]  # Extracts '30092024'
        # Convert extracted string to datetime format
        return pd.to_datetime(date_str, format='%d%m%Y').strftime('%d-%m-%Y')
    except Exception as e:
        print(f"Error converting transactionId to date: {e}")
        return None
def summary(path):
    # Traverse through folders in base path
    # for month_folder in os.listdir(base_path):
        # Check if folder name matches the month_year pattern
        # if month_year_pattern.match(month_folder):
            # Extract year from month_folder (e.g., 'Aug_2024' -> '2024')
    month_year,date_folder=path.split('/')[-3:-1]
    month_folder,year = month_year.split("_")  # Get the year from month_folder
    print("month_year,day :",month_year,date_folder)
    print("month,year :",month_folder,year)
    
    date_path = path#os.path.join(month_path, date_folder)
    print("count : ",len(glob(date_path+'**')))
    if os.path.isdir(date_path):
        # Initialize lists to hold data from each folder
        all_request_data = []
        all_raw_request_data = []

        # Process each unique folder (e.g., IND0004290920240100002)
        for sub_folder in sorted(glob(path+'/**'))[:]:
            sub_folder_path = os.path.join(date_path, sub_folder)
            if os.path.isdir(sub_folder_path):
                # Define paths to JSON files for this specific sub-folder
                request_json_path = glob(os.path.join(sub_folder_path, "json/request.json"))
                request_raw_json_path = glob(os.path.join(sub_folder_path, "json/request_raw.json"))
                respose_json_path = glob(os.path.join(sub_folder_path, "json/response.json"))
                respose_json_path_live = glob(os.path.join(sub_folder_path, "json/response_live.json"))
                
                

                # Load JSON data
                json_request_data = load_json_data(request_json_path)
                json_raw_request_data = load_json_data(request_raw_json_path)
                response_data = load_json_data(respose_json_path)
                response_data_live = load_json_data(respose_json_path_live)
                
                Live_Logid=-2
                Live_status_message_live='response_data_live File not found'

                # Check if JSON data is available and if so, normalize it into DataFrames
                if json_request_data:
                    df_request = pd.json_normalize(json_request_data)
                    # Check for the transactionId column and create date column based on it
                    if 'transactionId' in df_request.columns:
                        df_request.insert(df_request.columns.get_loc('transactionId') + 1, 'date', df_request['transactionId'].apply(convert_to_date_from_transaction_id))
                        # print("Request DataFrame with date added from transactionId:")
                        # print(df_request.head())  # Print the DataFrame for debugging
                    all_request_data.append(df_request)

                if json_raw_request_data:
                    df_request_raw = pd.json_normalize(json_raw_request_data)
                    # Check for the transactionId column and create date column based on it
                    if 'transactionId' in df_request_raw.columns:
                        df_request_raw.insert(df_request_raw.columns.get_loc('transactionId') + 1, 'date', df_request_raw['transactionId'].apply(convert_to_date_from_transaction_id))
                        # print("Raw Request DataFrame with date added from transactionId:")
                        # print(df_request_raw.head())  # Print the DataFrame for debugging
                    all_raw_request_data.append(df_request_raw)
                if response_data:
                    response_data=response_data[0]
                    status_message=response_data["statusMessage"]
                    if status_message== "Data Saved Successfully!":
                        Logid=response_data['responseData']['logId']
                    else:
                        Logid=-1

                if response_data_live:
                    """
                    {'statusCode': '200', 'statusMessage': 'Data Saved Successfully!', 'statusMessage1': None, 
                    'responseData': {'logId': 53, 'message': 'Success'}, 'responseData1': None, 'responseData2': None, 
                    'responseData3': None, 'responseData4': Non

                    """
                    response_data_live=response_data_live[0]
                    # print('response_data_live : ',response_data_live)
                    Live_status_message_live=response_data_live["statusMessage"]
                    if Live_status_message_live== "Data Saved Successfully!":
                        response_data['Live_responseData_Message']=Live_status_message_live
                        Live_Logid=response_data_live['responseData']['logId']
                    else:
                        response_data['Live_responseData_Message']=Live_status_message_live
                        Live_Logid=response_data_live['responseData']['logId']

                # Get image paths and counts for this specific sub-folder
                # print("sub_folder_path :",sub_folder_path)
                Anpr_raw_image_path = glob(sub_folder_path+'/raw/*Raw*')
                # print("all : ",glob(sub_folder_path+'/raw/**'))
                Top_Camera_raw_image_path = glob(sub_folder_path+'/raw/top_image**')
                Cross_lane_Top_Camera_raw_image_path = glob(sub_folder_path+'/raw/*Cross_Lane*')
                pred_image_path = glob(sub_folder_path+"/prediction/**")
                Mineral_crop_image_path = glob(sub_folder_path+ "top_crop/*top_image*")
                # print("Top_Camera_raw_image_path :",Top_Camera_raw_image_path)

                Anpr_raw_image_count = len(Anpr_raw_image_path)
                Top_image_raw_image_count = len(Top_Camera_raw_image_path)
                Cross_lane_Top_image_raw_image_count = len(Cross_lane_Top_Camera_raw_image_path)
                
                pred_image_count = len(pred_image_path)
                Mineral_crop_image_count = len(Mineral_crop_image_path)
                total_image_count = Anpr_raw_image_count+Top_image_raw_image_count+ Cross_lane_Top_image_raw_image_count+ pred_image_count + Mineral_crop_image_count 

                # Add image counts to each row in DataFrames
                if json_request_data:
                    df_request['Anpr_raw_image_count'] = Anpr_raw_image_count
                    df_request['Top_image_raw_image_count'] = Top_image_raw_image_count
                    df_request['Cross_lane_Top_image_raw_image_count'] = Cross_lane_Top_image_raw_image_count
                    df_request['prediction_image_count'] = pred_image_count
                    df_request['Mineral_crop_image_count'] = Mineral_crop_image_count
                    df_request['total_image_count'] = total_image_count
                    df_request['Logid'] = Logid
                    df_request['Live_Logid'] = Live_Logid
                    df_request['Live_responseData_Message'] = Live_status_message_live
                    
                    
                    
                if json_raw_request_data:
                    df_request_raw['Anpr_raw_image_count'] = Anpr_raw_image_count
                    df_request_raw['Top_image_raw_image_count'] = Top_image_raw_image_count
                    df_request_raw['Cross_lane_Top_image_raw_image_count'] = Cross_lane_Top_image_raw_image_count
                    df_request_raw['prediction_image_count'] = pred_image_count
                    df_request_raw['Mineral_crop_image_count'] = Mineral_crop_image_count
                    df_request_raw['total_image_count'] = total_image_count
                    df_request_raw['Logid'] = Logid
                    df_request_raw['Live_Logid'] = Live_Logid
                    df_request_raw['Live_responseData_Message'] = Live_status_message_live
                    

        # Combine all folder data into single DataFrames for export
        combined_request_df = pd.concat(all_request_data, ignore_index=True) if all_request_data else pd.DataFrame()
        combined_raw_request_df = pd.concat(all_raw_request_data, ignore_index=True) if all_raw_request_data else pd.DataFrame()

        # Safely count occurrences for additional sheets if columns exist
        if 'final_front_class' in combined_raw_request_df.columns:
            front_class_name_counts = combined_raw_request_df['final_front_class'].value_counts().reset_index()
            front_class_name_counts.columns = ['front_class_vehicle', 'count']
        else:
            front_class_name_counts = pd.DataFrame(columns=['front_class_vehicle', 'count'])

        if 'final_top_class' in combined_raw_request_df.columns:
            top_class_name_counts = combined_raw_request_df['final_top_class'].value_counts().reset_index()
            top_class_name_counts.columns = ['top_class_vehicle', 'count']
        else:
            top_class_name_counts = pd.DataFrame(columns=['top_class_vehicle', 'count'])

        if 'material' in combined_raw_request_df.columns:
            material_counts = combined_raw_request_df['material'].value_counts().reset_index()
            material_counts.columns = ['mineral', 'count']
        else:
            material_counts = pd.DataFrame(columns=['mineral', 'count'])

        # Create the Excel output path for the year-month-year folder
        excel_output_path = os.path.join(output_excel_base_path, year, month_folder, "daily")  # Added year here
        os.makedirs(excel_output_path, exist_ok=True)

        # Format the file name with the date in the filename
        date_str = date_folder.replace("-", "")
        excel_file = os.path.join(excel_output_path, f"{date_str}.xlsx")

        # Write to Excel file
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            if not combined_raw_request_df.empty:
                combined_raw_request_df.to_excel(writer, sheet_name="raw_request_excel", index=False)
            if not combined_request_df.empty:
                combined_request_df.to_excel(writer, sheet_name="request_excel", index=False)
            
            front_class_name_counts.to_excel(writer, sheet_name='front_class_vehicle', index=False)
            top_class_name_counts.to_excel(writer, sheet_name='top_class_vehicle', index=False)
            material_counts.to_excel(writer, sheet_name='mineral', index=False)

        
def main():
    upload_backup_days=2
    now = datetime.datetime.now()
    for day in range(1,upload_backup_days+1):
        target_date=(now-datetime.timedelta(days=day))
        day_str=target_date.strftime("%d%m%Y")
        source_folder_name=Source_path+'/OUTPUT_Backup/'+target_date.strftime("%b_%Y")+'/'+target_date.strftime("%d-%m-%Y")+'/'
        print("source_folder_name : ",source_folder_name)
        start_time=time.time()
        summary(source_folder_name)
        end_time=time.time()
        print("Execution time" ,end_time-start_time)
if __name__=="__main__":
    main()