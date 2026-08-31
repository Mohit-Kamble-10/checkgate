import sys
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
from test_craft import craft
from demo_recognition import recognition
from post_processing import post_processing 
import re
import shutil
from collections import Counter
import logging
# Load the saved model
# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# classes=['Stone_crush_powder','Stone','Soil','Sand','Murum','Crusher_Khadi']
# source_path=config.root_path+'/MP_AISES-main/weights/'



now = datetime.datetime.now()
start_script_datetime=now.strftime("%d_%m_%Y_%H_%M")

Current_log_path=config.root_path+f"/logs/ANPR_Logs.log"
backup_logs_path=config.root_path+f"/logs/ANPR_Logs/"
os.makedirs(backup_logs_path,exist_ok=True)
if os.path.exists(Current_log_path):
    shutil.move(Current_log_path,backup_logs_path+f"ANPR_Logs_{start_script_datetime}.log")

FORMAT = "%(asctime)s: %(filename)s: %(levelname)s :%(lineno)5s:: - %(funcName)10s() :  %(message)s"
logging.basicConfig(filename=Current_log_path,
                    format=FORMAT,
                    filemode='a',
                    level=logging.DEBUG, # Set logging level
                    force=True)

class ANPR():
    # Indian plate: AA00A0000 / AA00AA0000 — require 4 trailing digits (reject truncated OCR)
    _PLATE_RE = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$")

    def __init__(self) -> None:
        self.craft_obj=craft()
        self.recog_obj=recognition()
        self.pp_obj=post_processing()
        print('ANPR Model Loaded...')
        logging.info('ANPR Model Loaded Successfully.....')

    def _looks_like_indian_plate(self, text):
        return bool(self._extract_indian_plate(text))

    def _strip_ind_prefix(self, text):
        t = text.upper()
        for prefix in ('BHARAT', 'IND'):
            if t.startswith(prefix):
                t = t[len(prefix):]
        return t

    def _coerce_plate_slots(self, s):
        """O/0 and I/1 only in digit vs letter slots (Indian AA00AA0000 / AA00A0000)."""
        if len(s) == 10:
            letter_idx, digit_idx = {0, 1, 4, 5}, {2, 3, 6, 7, 8, 9}
        elif len(s) == 9:
            letter_idx, digit_idx = {0, 1, 4}, {2, 3, 5, 6, 7, 8}
        else:
            return s
        chars = list(s)
        for i, ch in enumerate(chars):
            if i in digit_idx:
                if ch == 'O':
                    chars[i] = '0'
                elif ch == 'I':
                    chars[i] = '1'
            elif i in letter_idx:
                if ch == '0':
                    chars[i] = 'O'
                elif ch == '1':
                    chars[i] = 'I'
        return ''.join(chars)

    def _plate_candidates(self, src):
        """Exact length first, then sliding windows; prefer 10-char over 9-char."""
        out = []
        seen = set()
        for n in (10, 9):
            if len(src) == n:
                for cand in (src, self._coerce_plate_slots(src)):
                    if cand not in seen:
                        seen.add(cand)
                        out.append(cand)
        for n in (10, 9):
            if len(src) <= n:
                continue
            for i in range(len(src) - n + 1):
                win = src[i:i + n]
                for cand in (win, self._coerce_plate_slots(win)):
                    if cand not in seen:
                        seen.add(cand)
                        out.append(cand)
        return out

    def _extract_indian_plate(self, text):
        """
        Pull a regex-valid plate from OCR garbage.
        Handles IND prefix, extra chars, and O/0 I/1 in the expected slots.
        """
        cleaned = ''.join(e for e in str(text) if e.isalnum()).upper()
        if not cleaned:
            return ''
        # Unique sources: full, IND-stripped, then try each
        pool = []
        for src in (cleaned, self._strip_ind_prefix(cleaned)):
            if src and src not in pool:
                pool.append(src)
        for src in pool:
            for cand in self._plate_candidates(src):
                if self._PLATE_RE.match(cand):
                    return cand
        return ''

    def _upscale_plate(self, image, min_h=168):
        """Upscale tiny YOLO plate crops before line-split OCR."""
        if image is None or getattr(image, 'size', 0) == 0:
            return image
        h = image.shape[0]
        if h >= min_h:
            return image
        scale = float(min_h) / max(h, 1)
        return cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    def _trim_ind_band(self, img, frac=0.12):
        """Drop left IND hologram strip so PARSeq does not eat it as extra letters."""
        if img is None or getattr(img, 'size', 0) == 0:
            return img
        w = img.shape[1]
        x = int(w * frac)
        if x < 4 or x >= w - 8:
            return img
        return img[:, x:]

    def _ocr_parseq(self, crops):
        """PARSeq on a list of image strips; concatenates alnum uppercase."""
        if not crops:
            return ''
        for crop in crops:
            if crop is None or getattr(crop, 'size', 0) == 0:
                return ''
        recog_output = self.recog_obj.recognition_main([list(crops)])
        if recog_output.get('Status') == 0 and recog_output.get('ANPR_Text_Found'):
            text = recog_output['ANPR_Text'][0]
            return ''.join(e for e in str(text) if e.isalnum()).upper()
        return ''

    def _ocr_full_crop(self, img):
        """PARSeq on the whole upscaled plate crop (no half-split)."""
        return self._ocr_parseq([img])

    def _ocr_two_halves(self, img):
        h = img.shape[0]
        top = img[: h // 2]
        bot = img[h // 2 :]
        return self._ocr_parseq([top, bot])

    def _geometric_two_line_ocr(self, number_plate_image):
        """
        Fallback when CRAFT line boxes are wrong.
        Upscale -> optional IND trim -> full-crop PARSeq, then top/bottom split.
        Full crop first: bumper art on 2-line plates can poison the half-split.
        """
        tried = []
        try:
            img = self._upscale_plate(number_plate_image)
            if img is None or getattr(img, 'size', 0) == 0:
                return ''
            for variant in (self._trim_ind_band(img), img):
                for ocr_fn in (self._ocr_full_crop, self._ocr_two_halves):
                    raw = ocr_fn(variant)
                    if not raw:
                        continue
                    tried.append(raw)
                    extracted = self._extract_indian_plate(raw)
                    if extracted:
                        return extracted
            if tried:
                logging.info(f'geometric OCR no regex match: {tried}')
        except Exception as e:
            logging.error(f'geometric_two_line_ocr error: {e}')
        return ''

    def _record_plate_text(self, index, raw_text):
        """Post-process and store one crop's OCR candidate."""
        if not raw_text:
            return
        raw_text = ''.join(e for e in str(raw_text) if e.isalnum()).upper()
        extracted = self._extract_indian_plate(raw_text)
        if extracted:
            raw_text = extracted
        final_text, _flag = self.pp_obj.main(raw_text)
        # Prefer regex-valid raw if post_process mangled a good plate
        if extracted and not self._looks_like_indian_plate(final_text):
            final_text = extracted
        elif self._looks_like_indian_plate(raw_text) and not self._looks_like_indian_plate(final_text):
            final_text = raw_text
        self.Raw_ANPR_Text_List.append(raw_text)
        self.ANPR_Text_List.append(final_text)
        self.index_text_dict[index] = final_text

    def ANPR_Process(self,Vehicle_Number_Crop_Path_List):
        # Deployed on 06-04-2024; Aug 2026: geometric 2-line fallback when CRAFT OCR fails plate regex
        self.index_text_dict={}
        for index,number_plate_image in enumerate(Vehicle_Number_Crop_Path_List):
            ANPR_Text = ''
            try:
                craft_output = self.craft_obj.craft_main([number_plate_image])
                if craft_output.get('Status') == 0 and craft_output.get('Image_Crop_List_Found'):
                    recog_output = self.recog_obj.recognition_main(
                        craft_output['Sorted_Rotated_Image_Crop_List']
                    )
                    if recog_output.get('Status') == 0 and recog_output.get('ANPR_Text_Found'):
                        try:
                            ANPR_Text = recog_output['ANPR_Text'][0]
                        except Exception:
                            ANPR_Text = ''
            except Exception as e:
                logging.error(f'CRAFT/PARSeq error crop {index}: {e}')
                ANPR_Text = ''

            candidate = ''.join(e for e in str(ANPR_Text) if e.isalnum()).upper() if ANPR_Text else ''
            final_probe = ''
            if candidate:
                final_probe, _ = self.pp_obj.main(candidate)

            extracted = self._extract_indian_plate(candidate) or self._extract_indian_plate(final_probe)
            if extracted:
                ANPR_Text = extracted
            else:
                fb = self._geometric_two_line_ocr(number_plate_image)
                if fb:
                    logging.info(
                        f'Two-line geometric OCR fallback crop {index}: '
                        f'craft={candidate!r} -> geometric={fb!r}'
                    )
                    ANPR_Text = fb

            if ANPR_Text:
                self._record_plate_text(index, ANPR_Text)

    def ANPR_Process_old(self,Vehicle_Number_Crop_Path_List):
        # till 06-04-2024
        
        for index,number_plate_image in enumerate(Vehicle_Number_Crop_Path_List):
            # try:
            craft_output=self.craft_obj.craft_main([number_plate_image])
            if craft_output['Status']==0:
                if craft_output['Image_Crop_List_Found']==True:
                    recog_output=self.recog_obj.recognition_main(craft_output['Sorted_Rotated_Image_Crop_List'])
                    if recog_output['Status']==0:
                        if recog_output['ANPR_Text_Found']==True:
                            try:
                                ANPR_Text=recog_output['ANPR_Text'][0]
                            except Exception as e:
                                
                                # logger.error('ANPR_Text issue : '+str(ANPR_Text))
                                ANPR_Text=''
                            # self.json_dict['raw_vehicleno']=ANPR_Text

                            found = re.findall(r"^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{1,4}$",ANPR_Text)
                            if len(found)>0 and len(found[0])>7:# min predicted seqence length should be 7
                                self.ANPR_Text_List.append(found[0])
                                self.valid_numberplate_index_list.append(index)
                                
                            self.Raw_ANPR_Text_List.append(ANPR_Text)
                                # self.last_text_lst.append(found[0])
                                
                                
                        else: 
                            pass
                            # logger.error('ANPR_Text_Not_Found else : '+str(recog_output['Error']))
                            # print("Error ANPR_Text_Not_Found  ", recog_output)
                    else: 
                        pass
                        # logger.error('Error recog_output else : '+str(recog_output['Error']))
                        # print("Error recog_output ", recog_output)
                else:
                    pass
                    # logger.error('No Number Plate found else : '+str(craft_output['Error']))
                    # print('No Number Plate found',craft_output['Error'])

            else:
                pass
                # logger.error('craft_output else : '+str(craft_output['Error']))
                # print("Error craft_output ", craft_output['Error'])
            # except Exception as e:
            #     # logger.error('ANPR catch Block : '+str(e))
            #     pass
    
    def ANPR_Postprocessing(self):
        final_text=''
        if len(self.ANPR_Text_List)>0:
            counts = Counter(self.ANPR_Text_List)
            sorted_items = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
            sorted_keys = [item[0] for item in sorted_items]
            found_list=[]
            for text in sorted_keys:
                found = re.findall(r"^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$",text)
                if len(found)>0:
                    found_list.append(found[0])
            # print('found_list : ',found_list)
            for text in found_list:
                if len(text)==9 and final_text=='':
                    final_text=text
                    # print("data_dict['final_text'] 1 : ",final_text)

                elif len(text)==10 and len(final_text)!=10:
                        final_text=text
                        # print("data_dict['final_text'] 2 : ",final_text)

        index_list=[key for key, val in self.index_text_dict.items() if val == final_text]
        self.valid_numberplate_index_list.extend(index_list)            
        raw_final_text=max(self.ANPR_Text_List,key=self.ANPR_Text_List.count)
        # final_text,Manual_check_requied_flag=self.pp_obj.main(raw_final_text)

        # logger.info('Number Recognize : '+self.final_text)
        return final_text,raw_final_text,''
    def Capture_Time(self,Image):
        Capture_Time_Text=self.recog_obj.recognition_main([[Image]])['ANPR_Text'][0]
        return Capture_Time_Text
    def main(self,Vehicle_Number_Crop_image_List):
        self.ANPR_Text_List=[]
        self.Raw_ANPR_Text_List=[]
        self.valid_numberplate_index_list=[]

        self.ANPR_Process(Vehicle_Number_Crop_image_List)
        if len(self.ANPR_Text_List)>0:
            final_text,raw_final_text,Manual_check_requied_flag=self.ANPR_Postprocessing()
        else:
            final_text,raw_final_text,Manual_check_requied_flag='','','2'
        if final_text=='':
            Manual_check_requied_flag='2'
        return final_text,raw_final_text,Manual_check_requied_flag,self.ANPR_Text_List,self.Raw_ANPR_Text_List,self.valid_numberplate_index_list
    
    
    

class main():
    def __init__(self) -> None:
        self.ANPR_obj=ANPR()

    
    

    def ANPR_Start(self,folder_path):
        # Only tight plate crops — exclude BigNumberPlate_* (added for wide bonnet context upload)
        Vehicle_Number_Crop_Path_List=sorted(glob(folder_path+'/processed/NumberPlate_Crop*.png'))
        Vehicle_Number_Crop_image_List=[]
        
        for number_place_image_path in Vehicle_Number_Crop_Path_List:
            number_plate_image=cv2.imread(number_place_image_path)
            Vehicle_Number_Crop_image_List.append(number_plate_image)
        # print('Vehicle_Number_Crop_image_List : ',len(Vehicle_Number_Crop_image_List))
        
        if len(Vehicle_Number_Crop_image_List)>0:
            final_text,raw_final_text,Manual_check_requied_flag,ANPR_Text_List,\
                Raw_ANPR_Text_List,valid_numberplate_index_list=self.ANPR_obj.main(Vehicle_Number_Crop_image_List)
            if len(valid_numberplate_index_list)>0:
                valid_numberplate_index=valid_numberplate_index_list[0]
                number_plate_crop_path=Vehicle_Number_Crop_Path_List[valid_numberplate_index]
                # print('number_plate_crop_path : ',number_plate_crop_path)
                path='/'.join(number_plate_crop_path.split('/')[:-1])
                if not os.path.exists(path+'/NumberPlate_Valid.png'):
                    shutil.copy(number_plate_crop_path,path+'/NumberPlate_Valid.png')
                base_name=os.path.basename(number_plate_crop_path)
                big_name=base_name.replace('NumberPlate_Crop_', 'BigNumberPlate_Crop_')
                number_plate_big_crop_path=os.path.join(path, big_name)
                if not os.path.exists(path+'/BigNumberPlate_Valid.png') and os.path.isfile(number_plate_big_crop_path):
                    shutil.copy(number_plate_big_crop_path,path+'/BigNumberPlate_Valid.png')
        else:
            final_text,raw_final_text,Manual_check_requied_flag,ANPR_Text_List,Raw_ANPR_Text_List='Not_Found','Not_Found','2',[],[]
            


        return final_text,raw_final_text,Manual_check_requied_flag,ANPR_Text_List,Raw_ANPR_Text_List

        
    def Find_Capture_Time(self,folder_path):
        Capture_Time_Output=""
        Crop_Time_Image=None
        try:
            ANPR_Image_path=folder_path+'/raw/Anpr_Raw.png'
            ANPR_Image=cv2.imread(ANPR_Image_path)
            if '202401' in folder_path or '202403' in folder_path:
                Crop_Time_Image=ANPR_Image[:int(0.045*1080),:int(0.25*1920)]
            elif '202402' in folder_path or '202404' in folder_path:
                Crop_Time_Image=ANPR_Image[int(0.04*1080):int(0.09*1080),int(0.04*1920):int(0.35*1920)]
            cv2.imwrite(folder_path+'/processed/Capture_ANPR_Crop.jpg',Crop_Time_Image)
            Capture_Time_Output=self.ANPR_obj.Capture_Time(Crop_Time_Image)
            # print('Capture_Time_Output : ',Capture_Time_Output)
        except Exception as e:
            print(e)
            
        return Capture_Time_Output

        

    def find_files_created_within_last_minute(self,folder_path):
        current_time = datetime.datetime.now()
        one_minute_ago = current_time - datetime.timedelta(minutes=2000)
        recent_files = []
        # print('folder_path : ',folder_path)
        for file_path in glob(folder_path):
            if os.path.exists(file_path+'/json/Front_Top_output.json') and \
                not os.path.exists(file_path+'/json/ANPR_output.json') and \
                not os.path.exists(file_path+'/json/response.json'):
                # print('file_path : ',file_path)
                creation_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
                if creation_time > one_minute_ago:
                    recent_files.append(file_path)
            # else:
            #     print('File not exist : ',file_path)

        return recent_files   

    def inferance(self,folder_path):
        # print('folder_path : ',folder_path)
        start=time.time()
        ANPR_json_path=folder_path+'/json/Front_Top_output.json'
        Number_Plate_json_path=folder_path+'/json/ANPR_output.json'
        
        if os.path.exists(ANPR_json_path):
            with open(ANPR_json_path) as json_file:
                json_data = json.load(json_file)
            # print('json_data : ',json_data)
            Number_Plate_data={}
            logging.info(f"TransactionId ANPR Process Started : {str(json_data['id'])}")
            Number_Plate_data['transactionId']=json_data['id']
            Number_Plate_data['datetime']=json_data['datetime']
            Number_Plate_data['vehicleno']='Not_Found'
            Number_Plate_data['raw_vehicleno'],Number_Plate_data['Raw_ANPR_Text_List']='Not_Found',[]
            Number_Plate_data['manual_check_req']=2
            Number_Plate_data['ANPR_Text_List']=[]
            Number_Plate_data['ANPR_Image_Captured_Time']=''

            
            Number_Plate_data['vehicleno'],Number_Plate_data['raw_vehicleno'],Number_Plate_data['manual_check_req'],\
                Number_Plate_data['ANPR_Text_List'],Number_Plate_data['Raw_ANPR_Text_List']=self.ANPR_Start(folder_path)

            Number_Plate_data['ANPR_Image_Captured_Time']=self.Find_Capture_Time(folder_path)
                
            Number_Plate_data['inferance_time']=f'{round(time.time()-start,2)}'
            print(json_data['id'],' : ',Number_Plate_data['vehicleno'],' : ',Number_Plate_data['inferance_time'])
            logging.info(f"TransactionId  : {str(json_data['id'])}:{Number_Plate_data['vehicleno']} : {Number_Plate_data['inferance_time']}")
            with open(Number_Plate_json_path, 'w') as f:
                json.dump(Number_Plate_data, f)
        else:
            logging.error(f"Path does not exist : "+ANPR_json_path)
            

    def main(self):
        
        folder_path = config.root_path+'/output/*2026*'
        
        while True:
            
            recent_files = self.find_files_created_within_last_minute(folder_path)
            # print("last 20 minute count:",len(recent_files))
            # logging.info('Process Pending : '+str(len(recent_files)))
            for file_path in recent_files:
                # self.inferance(file_path)
                try:
                    # time.sleep(2)
                    logging.info('Process Started file_path : '+str(file_path))
                    self.inferance(file_path)
                except Exception as e:
                    logging.error('Process error file_path : '+str(file_path)+' : '+str(e))
                    if 'Input/output error' in  str(e):
                        logging.error('ANPR Inferance main code Error : ANPR_Inferance_Script.py  Restarted')
                        os.execv(sys.executable, ['python3'] + sys.argv)
                    if config.check_error:
                        print("ANPR Inferance Script : ",e)
                    # raise
                    continue
                # break
            # break

            time.sleep(1)
if __name__=='__main__':
    main().main()

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
