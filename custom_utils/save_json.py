import json
import datetime

def save_json(dest_path,file_name,data):
    now = datetime.datetime.now()                              
    found_date_time=now.strftime("%d_%m_%Y_%H_%M_%S")
    data['datetime']=found_date_time
    with open(dest_path+file_name, "w") as outfile:
        json.dump(data, outfile, indent=4)
