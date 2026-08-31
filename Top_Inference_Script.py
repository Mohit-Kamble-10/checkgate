import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
from glob import glob
import cv2
import datetime
import time
import os
import json
from configs import config
from configs.config import mining_category, top_image_valid
import re
import shutil
from collections import Counter
from detection import yolo_pred, vehicle_type_pred
import sys
import logging
# lane_no=sys.argv[1] # string 1,2,3

# Load the saved model
# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# source_path=config.root_path+'/src/weights/'
source_path=config.root_path+'/metadata/weights/'
now = datetime.datetime.now()
start_script_datetime=now.strftime("%d_%m_%Y_%H_%M")

Current_log_path=config.root_path+f"/logs/Top_Inferance_Logs.log"
# backup_logs_path=config.root_path+f"/logs/Top_Inferance_Logs/"
# os.makedirs(backup_logs_path,exist_ok=True)
# if os.path.exists(Current_log_path):
#     shutil.move(Current_log_path,backup_logs_path+f"Top_Inferance_Logs_{start_script_datetime}.log")

FORMAT = "%(asctime)s: %(filename)s: %(levelname)s :%(lineno)5s:: - %(funcName)10s() :  %(message)s"
logging.basicConfig(filename=Current_log_path,
                    format=FORMAT,
                    filemode='a',
                    level=logging.DEBUG, # Set logging level
                    force=True)

def read_roi():
    ROI_INFO={}
    if os.path.exists(config.master_jsons+'/camera_details.json'):
        with open(config.master_jsons+'/camera_details.json') as json_file:
            get_camera_profile_data = json.load(json_file)
            logging.info('ROI Info Loaded...')
            return get_camera_profile_data
        
        # for lane_no in range(1,6):
        #     if 'Top_'+str(lane_no) in get_camera_profile_data.keys():
        #         ROI_INFO[lane_no]=get_camera_profile_data['Top_'+str(lane_no)]['roi_info']
        #     else:
        #         return None
    else:
        print('camera_details.json not found')
        print(config.master_jsons+'/camera_details.json')
        logging.error('camera_details.json not found')
        
        # exit()


class Top_Prediction():
    def __init__(self,lane_id) -> None:
        self.ROI_Info=read_roi()
        
        self.yolo_pred=yolo_pred(lane_id,image_type='TOP',roi_info= self.ROI_Info)
        try:
            self.vehicle_type_obj=vehicle_type_pred()
            logging.info("Vehicle type model (19-06-2026.pt) loaded")
        except Exception as e:
            self.vehicle_type_obj=None
            logging.error(f"Vehicle type model load failed: {e}")
        print('Top Model Loaded...')
        logging.info("Top Model Loaded...")
        

    
    
    def main(self,image_List,lane_id):
        Top_Class_List=[]
        Top_Class_List_valid=[]
        
        Front_Class_List=[]
        Front_Class_List_valid=[]

        Top_image_crop_list=[]
        Top_image_crop_list_valid=[]

        Bonnet_crop_list=[]
        Top_Pred_image_list=[]
        Top_Class='Not_Found'
        Front_Class='Not_Found'
        Top_Class_valid='Not_Found'
        Front_Class_valid='Not_Found'
        Front_Valid_Image_list=[]
        Front_Class_per_frame_list=[]
        for image in image_List:
            top_output=self.yolo_pred.Top_main(image,lane_no=lane_id)
            if top_output['Status']==0:
                top_pred_image=top_output['Return_Disply_Frame'][0]
                Top_Pred_image_list.append(top_pred_image)
                # Keep per-frame lists aligned 1:1 with Top_Pred_image_list
                Front_Valid_Image_list.append(bool(top_output.get('Front_Valid_Image')))
                Front_Class_per_frame_list.append(top_output.get('Front_Class') or '')
                if top_output['Front_Class']!='':
                    Front_Class_List.append(top_output['Front_Class'])
                    if top_output['Front_Valid_Image']:
                            Front_Class_List_valid.append(top_output['Front_Class'])

                if len(top_output['Raw_Top_Category_List'])>0:
                    Top_Class_List.append(top_output['Raw_Top_Category_List'][0])
                    if top_output['Front_Valid_Image']:
                            Top_Class_List_valid.append(top_output['Raw_Top_Category_List'][0])

                if len(top_output['Raw_Mining_Full_Crop_List'])>0:
                    for mining_full_crop in top_output['Raw_Mining_Full_Crop_List']:
                        Top_image_crop_list.append(mining_full_crop)
                        if top_output['Front_Valid_Image']:
                            Top_image_crop_list_valid.append(mining_full_crop)

                if top_output['Bonnet_Crop_Found']:
                    for bonnet_crop in top_output['Bonnet_Crop_List']:
                        Bonnet_crop_list.append(bonnet_crop)
    
        if len(Top_Class_List)>0:
            Top_Class=max(Top_Class_List,key=Top_Class_List.count)
        if len(Front_Class_List)>0:
            Front_Class=max(Front_Class_List,key=Front_Class_List.count)

        if len(Top_Class_List_valid)>0:
            Top_Class_valid=max(Top_Class_List_valid,key=Top_Class_List_valid.count)
        if len(Front_Class_List_valid)>0:
            Front_Class_valid=max(Front_Class_List_valid,key=Front_Class_List_valid.count)

        return Top_Class,Top_Class_List,Top_Class_valid,Top_Class_List_valid,Front_Class,Front_Class_List,Front_Class_valid,Front_Class_List_valid,Bonnet_crop_list,\
    Top_Pred_image_list,Top_image_crop_list,Front_Valid_Image_list,Top_image_crop_list_valid,Front_Class_per_frame_list
    

class main():
    def __init__(self) -> None:
        self.Top_obj=Top_Prediction(lane_id=None)

    def _is_mining_top(self, Top_Class, Top_Class_valid):
        return Top_Class in mining_category or Top_Class_valid in mining_category

    @staticmethod
    def _center_window(items, max_count):
        """Pick up to max_count items from the middle of a chronologically ordered list."""
        if not items:
            return []
        n = min(max_count, len(items))
        start = (len(items) - n) // 2
        return items[start:start + n]

    @staticmethod
    def _matches_expected_front(front_cls, expected_front, dominant_front):
        """True if frame front class matches the transaction vehicle (hywa, etc.)."""
        if not front_cls or front_cls == 'Not_Found':
            return False
        for target in (expected_front, dominant_front):
            if target and target not in ('', 'Not_Found') and front_cls == target:
                return True
        return False

    def promote_last_top_images_to_valid(
        self,
        folder_path,
        top_class,
        top_class_valid,
        top_image_name_list=None,
        front_valid_image_list=None,
        front_class_per_frame_list=None,
        expected_front_class=None,
        dominant_front_class=None,
    ):
        """
        Mining only: rename selected raw top_image_* → top_image_valid_* (not copy).
        Prefer frames where YOLO set Front_Valid_Image AND front class matches the
        transaction vehicle (from Front_Top_output / majority vote). Avoids promoting
        a previous vehicle still in the top-camera view (e.g. tractor before hywa).
        """
        if not self._is_mining_top(top_class, top_class_valid):
            return 0

        raw_path = folder_path + '/raw/'
        pred_path = folder_path + '/prediction/'
        max_valid = max(1, int(top_image_valid) if top_image_valid else 3)

        for existing in glob(raw_path + 'top_image_valid_*'):
            try:
                os.remove(existing)
            except OSError as e:
                logging.error(f'promote_last_top_images_to_valid remove raw valid: {e}')
        for existing in glob(pred_path + 'pred_top_image_valid_*'):
            try:
                os.remove(existing)
            except OSError as e:
                logging.error(f'promote_last_top_images_to_valid remove pred valid: {e}')

        non_valid = sorted(
            p for p in glob(raw_path + 'top_image_*')
            if '_valid_' not in os.path.basename(p) and 'Cross_Lane_' not in p
        )
        if not non_valid:
            logging.warning('promote_last_top_images_to_valid: no top_image_* frames found')
            return 0

        non_valid_by_name = {os.path.basename(p): p for p in non_valid}
        all_names = sorted(non_valid_by_name.keys())

        n_pred = min(
            len(top_image_name_list or []),
            len(front_valid_image_list or []),
            len(front_class_per_frame_list or []),
        )

        def _names_matching_front(require_valid):
            names = []
            if not top_image_name_list:
                return names
            for i in range(n_pred):
                if require_valid and not front_valid_image_list[i]:
                    continue
                fc = front_class_per_frame_list[i]
                if self._matches_expected_front(fc, expected_front_class, dominant_front_class):
                    name = top_image_name_list[i]
                    if name in non_valid_by_name:
                        names.append(name)
            return names

        valid_names = _names_matching_front(require_valid=True)
        selection = 'Front_Valid_Image+expected_front'

        if not valid_names:
            valid_names = _names_matching_front(require_valid=False)
            selection = 'expected_front_only'

        if valid_names:
            chosen_names = self._center_window(valid_names, max_valid)
        else:
            chosen_names = self._center_window(all_names, max_valid)
            selection = 'center_fallback'

        to_promote = [non_valid_by_name[n] for n in chosen_names]
        promoted = 0
        for src in to_promote:
            basename = os.path.basename(src)
            valid_basename = basename.replace('top_image', 'top_image_valid', 1)
            valid_dest = raw_path + valid_basename
            try:
                os.rename(src, valid_dest)
                pred_src = pred_path + 'pred_' + basename
                pred_dest = pred_path + 'pred_' + valid_basename
                if os.path.exists(pred_src):
                    os.rename(pred_src, pred_dest)
                promoted += 1
                logging.info(f'Renamed to valid top frame: {valid_basename}')
            except OSError as e:
                logging.error(f'promote_last_top_images_to_valid rename {basename}: {e}')

        logging.info(
            f'promote_last_top_images_to_valid: {promoted}/{len(to_promote)} '
            f'(max={max_valid}, selection={selection}, '
            f'expected_front={expected_front_class}, dominant_front={dominant_front_class}, '
            f'matching_candidates={len(valid_names)}, top_class={top_class}, '
            f'top_class_valid={top_class_valid})'
        )
        return promoted

    def run_vehicle_type_on_valid_images(self, folder_path):
        """Run 19-06-2026.pt only on raw/top_image_valid_* (skips axle class)."""
        if self.Top_obj.vehicle_type_obj is None:
            return 'Not_Found', []
        valid_paths = sorted(glob(folder_path + '/raw/top_image_valid_*'))
        predictions = []
        for image_path in valid_paths:
            image = cv2.imread(image_path)
            if image is None:
                continue
            try:
                output = self.Top_obj.vehicle_type_obj.vehicle_type_main(image)
                if output.get('Status') == 0 and output.get('Vehicle_Type_Class', 'Not_Found') != 'Not_Found':
                    predictions.append(output['Vehicle_Type_Class'])
            finally:
                del image
        if not predictions:
            return 'Not_Found', []
        winner = max(set(predictions), key=predictions.count)
        logging.info(f"Vehicle type from valid tops: {winner} votes={predictions}")
        return winner, predictions

    def save_bonnet_image(self,folder_path,bonnet_image_list):
        dest_path=folder_path+'/processed/'
        for i in range(len(bonnet_image_list)):
            try:
                cv2.imwrite(dest_path+f'/bonnet_crop_{str(i)}.png',cv2.cvtColor(bonnet_image_list[i], cv2.COLOR_BGR2RGB))
            except Exception as e:
                logging.error(e)
                continue

    def save_top_prediction(self, folder_path, Top_image_name_list, Top_Pred_image_list):
        """Write pred_top_image_* only; valid raw frames are renamed in promote_last_top_images_to_valid."""
        dest_path = folder_path + '/prediction/'
        for i in range(len(Top_Pred_image_list)):
            try:
                cv2.imwrite(dest_path + f'/pred_{Top_image_name_list[i]}', Top_Pred_image_list[i])
            except Exception as e:
                logging.error(e)
                continue

    
    def save_top_crop(self,folder_path,Top_image_name_list,Top_image_crop_list):
        dest_path=folder_path+'/top_crop/'
        for i in range(len(Top_image_crop_list)):
            try:
                cv2.imwrite(dest_path+f'/Top_Camera_{Top_image_name_list[i]}',cv2.cvtColor(Top_image_crop_list[i], cv2.COLOR_BGR2RGB))
            except Exception as e:
                logging.error(e)
                continue
    
    def save_top_valid_crop(self,folder_path,Top_image_crop_list_valid):
        dest_path=folder_path+'/top_crop/'
        for i in range(len(Top_image_crop_list_valid)):
            try:
                cv2.imwrite(dest_path+f'/Top_Camera_Valid_{i}.png',cv2.cvtColor(Top_image_crop_list_valid[i], cv2.COLOR_BGR2RGB))
            except Exception as e:
                logging.error(e)
                continue
    
    def Top_Start(self,folder_path,lane_no):
        Top_image_Path_List=sorted(glob(folder_path+'/raw/*top_image*'))
        Top_image_List=[]
        Top_image_name_list=[]
        Top_Class_List_valid=[]
        Front_Class_List_valid=[]


        
        for top_image_path in Top_image_Path_List:
            if 'Cross_Lane_' not in top_image_path and '_valid_' not in top_image_path:
                top_image=cv2.imread(top_image_path)
                if top_image is None:
                    logging.error(f'Top image read failed: {top_image_path}')
                    continue
                Top_image_name_list.append(top_image_path.split('/')[-1])
                Top_image_List.append(top_image)
        
        if len(Top_image_List)>0:
            Top_Class,Raw_Top_List,Top_Class_valid,Top_Class_List_valid,Front_Class,Raw_Front_List,Front_Class_valid,Front_Class_List_valid,\
            Bonnet_Crop_List,Top_Pred_image_list,Top_image_crop_list,Front_Valid_Image_list,Top_image_crop_list_valid,Front_Class_per_frame_list=self.Top_obj.main(Top_image_List,lane_no)
            is_mining = self._is_mining_top(Top_Class, Top_Class_valid)

            expected_front_class = None
            front_top_json = folder_path + '/json/Front_Top_output.json'
            if os.path.exists(front_top_json):
                try:
                    with open(front_top_json) as f:
                        expected_front_class = json.load(f).get('front_class_name')
                except Exception as e:
                    logging.error(f'Front_Top_output read failed: {e}')
            if len(Bonnet_Crop_List)>0:
                self.save_bonnet_image(folder_path,Bonnet_Crop_List)
                logging.info('save_bonnet_image')
            if len(Top_Pred_image_list)>0:
                n = min(len(Top_image_name_list), len(Top_Pred_image_list))
                self.save_top_prediction(
                    folder_path,
                    Top_image_name_list[:n],
                    Top_Pred_image_list[:n],
                )
                logging.info('save_top_prediction done')
            
            if len(Top_image_crop_list)>0:
                self.save_top_crop(folder_path,Top_image_name_list,Top_image_crop_list)
                logging.info('save_top_crop')
            if is_mining and len(Top_image_crop_list_valid)>0:
                self.save_top_valid_crop(folder_path,Top_image_crop_list_valid)
                logging.info('save_top_valid_crop Done')

            if is_mining:
                self.promote_last_top_images_to_valid(
                    folder_path,
                    Top_Class,
                    Top_Class_valid,
                    top_image_name_list=Top_image_name_list[:len(Top_Pred_image_list)],
                    front_valid_image_list=Front_Valid_Image_list,
                    front_class_per_frame_list=Front_Class_per_frame_list,
                    expected_front_class=expected_front_class,
                    dominant_front_class=Front_Class,
                )
                try:
                    vehicle_type_class, vehicle_type_list = self.run_vehicle_type_on_valid_images(folder_path)
                except Exception as e:
                    logging.error(f'vehicle type inference failed: {e}')
                    vehicle_type_class, vehicle_type_list = 'Not_Found', []
                if vehicle_type_class != 'Not_Found':
                    Front_Class_valid = vehicle_type_class
                    Front_Class_List_valid = vehicle_type_list
            else:
                logging.info(
                    f'Skip top_image_valid / vehicle-type: Top_Class={Top_Class} '
                    f'Top_Class_Valid={Top_Class_valid}'
                )

            # Free large in-memory frames before next txn (keep Bonnet_Crop_List for return)
            del Top_image_List, Top_Pred_image_list, Top_image_crop_list, Top_image_crop_list_valid
            if torch.cuda.is_available():
                try:
                    torch.cuda.empty_cache()
                except Exception:
                    pass

        else:
            Top_Class,Raw_Top_List,Top_Class_valid,Top_Class_List_valid='Not_Found',[],'Not_Found',[]
            Front_Class,Raw_Front_List,Front_Class_valid,Front_Class_List_valid='Not_Found',[],'Not_Found',[]
            Bonnet_Crop_List=[]
            logging.error('Top_image_Path_List / readable frames = 0')

        # print('Top_Class : ',Top_Class)
        return Top_Class,Raw_Top_List,Top_Class_valid,Top_Class_List_valid,Front_Class,Raw_Front_List,Front_Class_valid,Front_Class_List_valid,Bonnet_Crop_List

        


        

    def find_files_created_within_last_minute(self,folder_path):
        current_time = datetime.datetime.now()
        current_time_sec=time.time()
        one_minute_ago = current_time - datetime.timedelta(minutes=2000)
        recent_files = []
        # print('folder_path : ',folder_path)
        for file_path in glob(folder_path):
            # print('file_path : ',file_path)
            if os.path.exists(file_path+'/json/Front_Top_output.json') and \
                os.path.exists(file_path+'/json/Sync_ANPR_TOP_output.json') and \
                not os.path.exists(file_path+'/json/Top_Detection_output.json') and \
                not os.path.exists(file_path+'/json/response.json'):
                # print('file_path : ',file_path)
                creation_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
                creation_time_sec = os.path.getctime(file_path)
                if creation_time > one_minute_ago:
                    if  current_time_sec-creation_time_sec>=5:
                        recent_files.append(file_path)
                        # print(file_path," :  complete 5 sec")
                    else:
                        pass
                        # print(file_path," : waiting to complete 5 sec")
            # else:
            #     print('File not exist : ',file_path)

        return recent_files   

    def inferance(self,folder_path,non_mining=False):
        lane_no=int(folder_path.split('/')[-1][15:17])
        # print('Top Detection inferance folder_path : ',folder_path)
        start=time.time()
        Front_Top_output_json_path=folder_path+'/json/Front_Top_output.json'
        Top_Detection_output_json_path=folder_path+'/json/Top_Detection_output.json'
        Top_Detection_output_json_path_updated=folder_path+'/json/Top_Detection_output_updated.json'
        
        if os.path.exists(Front_Top_output_json_path):
            with open(Front_Top_output_json_path) as json_file:
                json_data = json.load(json_file)
            # print('json_data : ',json_data)
            Top_Analysis_data={}
            Top_Analysis_data['transactionId']=json_data['id']
            Top_Analysis_data['datetime']=json_data['datetime']
            Top_Analysis_data['Top_Class']=json_data['top_class_name']
            Top_Analysis_data['Raw_Top_List']=[]
            Top_Analysis_data['Top_Class_Valid']='Not_Found'
            Top_Analysis_data['Raw_Top_List_Valid']=[]
            Top_Analysis_data['Front_Class']=json_data['front_class_name']
            Top_Analysis_data['Raw_Front_List']=[]
            Top_Analysis_data['Front_Class_Valid']='Not_Found'
            Top_Analysis_data['Raw_Front_List_Valid']=[]
            

            if non_mining==False:
                Top_Analysis_data['Top_Class'],Top_Analysis_data['Raw_Top_List'],Top_Analysis_data['Top_Class_Valid'],Top_Analysis_data['Raw_Top_List_Valid'],Top_Analysis_data['Front_Class'],\
                    Top_Analysis_data['Raw_Front_List'],Top_Analysis_data['Front_Class_Valid'],Top_Analysis_data['Raw_Front_List_Valid'],Bonnet_Crop_List=self.Top_Start(folder_path,lane_no)
                
            Top_Analysis_data['inferance_time']=f'{round(time.time()-start,2)}'
            print(json_data['id'],' : ',Top_Analysis_data['Front_Class'],' : ',Top_Analysis_data['Top_Class'],' : ',Top_Analysis_data['inferance_time'])
            logging.info(f"TransactionId  : {str(json_data['id'])}:{Top_Analysis_data['Front_Class']} : {Top_Analysis_data['Top_Class']} : {Top_Analysis_data['inferance_time']}")
            if not os.path.exists(Top_Detection_output_json_path):
                with open(Top_Detection_output_json_path, 'w') as f:
                    json.dump(Top_Analysis_data, f)
            else:
                print("Top_Detection_output_json_path File Found....Writing Top_Detection_output_json_path_updated.json")
                with open(Top_Detection_output_json_path_updated, 'w') as f:
                    json.dump(Top_Analysis_data, f)
        else:
            logging.error("Top Detection File not found Front_Top_output_json_path")
            print('Top Detection File not found Front_Top_output_json_path')

    def main(self):
        
        folder_path = config.root_path+'/output/*2026*'
        # print('folder_path : ',folder_path)
        while True:
            
            recent_files = self.find_files_created_within_last_minute(folder_path)
            # print("last 20 minute count:",len(recent_files))
            for file_path in recent_files:
                # self.inferance(file_path)
                try:
                    logging.info('Process Started file_path : '+str(file_path))
                    
                    time.sleep(2)
                    self.inferance(file_path)
                except Exception as e:
                    logging.error('Process error file_path : '+str(file_path)+' : '+str(e))
                    if 'Input/output error' in  str(e):
                        logging.error('Top_Inference_Script code Error : Top_Inference_Script.py  Restarted')
                        os.execv(sys.executable, ['python3'] + sys.argv)
                    
                    if config.check_error:
                        print('Top Inferance Script : ',e)
                    continue
                # break
            # break

            time.sleep(1)
if __name__=='__main__':
    main().main()
    # main().inferance('/home/shaurya/output/IND0001210820240101197',lane_no=1)

# if __name__=='__main__':
#     image_paths=glob('/home/linux/DeepLearning/Uday/MP_AVDR/model_training/Mineral_Classification/support_data/training_data_original/train_224_512/**/**/**')
#     mineral_classification_obj=mineral_classification()
#     for image_path in image_paths:
#         # print(image_path)
#         #image_path='/home/linux/DeepLearning/Uday/MP_AVDR/model_training/Mineral_Classification/support_data/training_data_original/train/1_12March_Mineral_Classification/Murum/IND0002070320240101186_Anpr_Raw_6_11.png'
#         #image_path='/home/linux/DeepLearning/Uday/MP_AVDR/model_training/Mineral_Classification/support_data/training_data_original/train/13_14March_Mineral_Classification/Soil/IND0002140320240102157_Anpr_Raw_5_11.png'
#         image_path='/home/linux/DeepLearning/Uday/MP_AVDR/model_training/Mineral_Classification/support_data/training_data_original/train/13_14March_Mineral_Classification/Stone/IND0002130320240100941_Anpr_Raw_5_11.png'
#         image=cv2.imread(image_path)
#         mineral_classification_obj.main_mineral_classification(image)
#         break
