
import os
import sys
sys.path.append('/home/aikernel/metadata')
import master_config
from dotenv import load_dotenv

# Secrets live outside git: /home/aikernel/metadata/.env
load_dotenv('/home/aikernel/metadata/.env')
 
Country='IND'#IND0001150120240200001 IND->MachineID->Date->laneID->transacrion_count 
# # Bangrsia 
# MachineID='0002'
# LocationId='002'
# lane_count=2
# active_lane=[1]
# Fast_Moving=False

# #Neelbad
# MachineID='0004'
# LocationId='004'
# lane_count=4
# active_lane=[1,3]
# Fast_Moving=False

# #Eintkhedi
# MachineID='0003'
# LocationId='003'
# lane_count=1
# active_lane=[1]
# Fast_Moving=False

# #11 Mile, Obaidulla
# MachineID='0041'
# LocationId='041'
# lane_count=3
# active_lane=[1,2]
# Fast_Moving=True

# # Gadariyanala,Sehore
# MachineID='0018'
# LocationId='018'
# lane_count=3
# active_lane=[1,3]#2
# Fast_Moving=True

# # Tikamgarh
# MachineID='0025'
# LocationId='025'
# lane_count=2
# active_lane=[1,2]
# Fast_Moving=True

# # Kanjai (Lalbarra Seoni Marg),BALAGHAT
# MachineID='0038'
# LocationId='038'
# lane_count=2
# active_lane=[1,2]
# Fast_Moving=True

# Near Toll Gate, Bhorasa , Dewas
MachineID=master_config.MachineID#'0021'
LocationId=master_config.LocationId
lane_count=master_config.lane_count
active_lane=master_config.active_lane
Fast_Moving=master_config.Fast_Moving

# # Bhadanpur, Satna 
# MachineID='0017'
# LocationId='017'
# lane_count=2
# active_lane=[1,2]
# Fast_Moving=True

# # Test Nagar Live Department
# MachineID='0001'
# LocationId='002'
# lane_count=1
# Fast_Moving=True

anpr_image_size=(1920,1080)#(w,h)
anpr_fps=15#25

# top_image_size=(1280,720)#(w,h)
top_image_size=(2592, 1944)#(w,h)
top_fps=5


vehicle_not_found_frame_count=10
show_live_video=False
save_raw_video=False
top_process_start=True
number_of_top_frames_analize=3
check_error=False

# ---------------------------------------------------------------------------
# Duplicate transaction prevention (Front_Top) — Option A + multi-box escape
# ---------------------------------------------------------------------------
# After a txn completes, block new txn while a mining-front vehicle
# (hywa/truck/mini_truck/tractor) is still in ANPR front ROI.
# Clear only after N consecutive frames with no mining-front in that ROI.
# Bikes/cars/other are already ignored by YOLO front filter — they do not
# keep suppress stuck.
Suppress_Until_ANPR_ROI_Empty = True
# Frames of empty mining-front ROI before allowing the next txn (same idea
# as vehicle_not_found_frame_count; keep >= 10 to avoid flicker duplicates).
Suppress_ROI_Empty_Frame_Count = 10
# While suppress is on: if YOLO sees >= Multi_Box_Min_Count mining-front
# boxes in ANPR ROI (A still in + B entered), allow ONE new txn — works
# whether B has a plate or not. Re-arms when count drops below min.
Allow_Multi_Box_New_Txn = True
Multi_Box_Min_Count = 2

# Keep only number_plate crops that belong to the selected mining-front vehicle
# (hywa/truck/…). Stops attaching a car/bike/other plate to a mining txn.
Filter_Plate_To_Selected_Vehicle = True
# Expand selected vehicle box when testing plate ownership (extra pad below for
# low bumper plates). Fraction of vehicle width/height.
Plate_Vehicle_Assoc_Pad_Frac = 0.20


root_path = '/home/aikernel/'
# root_path = '/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/'
root_path_lane=root_path+'/output/'
jsons_path=root_path+'/src/configs/jsons/'
master_jsons=root_path+'/metadata/'
Cron_path=root_path+'/src/crons/'


# font      = cv2.FONT_HERSHEY_SIMPLEX
fontScale = 2
fontColor = (255,255,255)
thickness = 3
lineType  = 2

mining_vehicle_list=['hywa','truck','tractor','mini_truck']
non_mining_vehicle_list=['car','bus','other','two_wheeler']
mining_category=['mining_full','covered_mining_full']
# mineral_classes=['Stone_crush_powder','Stone','Soil','Sand','Murum','Crusher_Khadi']
mineral_classes=['Brown_Sand','Crusher_Khadi','Khadi','Murum','Sand','Soil','Stone','Stone_crush_powder','Tar']
colour_classes=['Black','Blue','Brown','Green','Grey_Silver','Red','White','Yellow_orange']
Sync_ANPR_Top_Exception=['0021']
# ---------------------------------------------------
# AWS keys from metadata/.env (not in source / not pushed with src)
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID', '')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY', '')
if not aws_access_key or not aws_secret_access_key:
    raise RuntimeError(
        'Missing AWS keys — set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY '
        'in /home/aikernel/metadata/.env (see .env.example)'
    )
public_bucket_name = 'mp-dss-ai-images'
mahakhanij_updaload=False
mahakhanij_API='https://mahakhanij.maharashtra.gov.in/mineral-mapping/monitoring/Add_MonitoringVehicle'
mahakhanij_Demo_API_v1= 'https://awsapi.mahamining.com/mineral-mapping/monitoring/Add_MonitoringVehicle_v1'
# depricated 
Add_MonitoringVehicle_v1='https://mp-dss-api.mahamining.com/MP/monitoring/Add_MonitoringVehicle_v1'

# DSS API (keep URLs defined; set Dss_Data_Upload=False to disable)
Add_MonitoringVehicle='https://mp-dss-api.mahamining.com/MP/monitoring/SaveMonitoringVehicleRecord_v4'
Image_path_upload_API='https://mp-dss-api.mahamining.com/MP/monitoring/SaveMonitoringVehiclePhotoDetails'

# Test API
# Add_MonitoringVehicle_Test="https://mp-dss-test-api.mahamining.com/MP/monitoring/SaveMonitoringVehicleRecord_v4"
Add_MonitoringVehicle_Test="https://mp-dss-test-api.mahamining.com/MP/AI_Monitoring/SaveMonitoringVehicleRecordTollPlazza" # v5 with extra 5 parameters
Image_path_upload_API_Test="https://mp-dss-test-api.mahamining.com/Mp/Uplods/Insert_Toll_Plaza_Photo_v1"


# Live API
Add_MonitoringVehicle_Live="https://echeckgate.mp.gov.in/dss-api/MP/AI_Monitoring/SaveMonitoringVehicleRecordTollPlazza"
Image_path_upload_API_Live="https://echeckgate.mp.gov.in/dss-api/Mp/Uplods/Insert_Toll_Plaza_Photo_v1"

Dss_Data_Upload=False
Test_Data_Upload=True           # record API (upload_json) — can stay True for Test logId
Live_Data_Upload=True
Upload_Test_Images=True       # False = image JSONs/upload only to Live (~22 files). True = Live+Test (~44)
Store_Cross_Lane_Images=False
# top_crop: Mineral_Top_Crop_Valid + Mineral_Top_Crop_1 only (not 6 mineral slots)
Upload_Mineral_Top_Crop_Images=True
Upload_Mineral_Top_Crop_Max_Valid=1
Upload_Mineral_Top_Crop_Max_Top_Images=1
Upload_Max_Dynamic_Raw_Top=1   # fallback only: top_image_* if no top_image_valid_* in raw/
Upload_BigNumberPlate_Max=2
Upload_NumberPlate_Crop_Max=2
# Max top_image_valid_* photos sent as Raw_Top_4..; upload min(count, this) — 1 to 3 typical
top_image_valid=3
Lane_Restart_API=''
Lane_HealthCheck_API=''
# ---------------------------------------------------                                                                                                                                                                        



