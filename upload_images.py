"""
# send json to server 
# take logID and 
# Save logID to send image to server
"""
# from fastapi import FastAPI
import json
import time
import boto3
from io import BytesIO
import mimetypes  
import cv2
import os
from configs.config import aws_access_key,aws_secret_access_key,\
    public_bucket_name,Image_path_upload_API,Image_path_upload_API_Live,Image_path_upload_API_Test,root_path,\
    Live_Data_Upload,Test_Data_Upload,Upload_Test_Images,Upload_Mineral_Top_Crop_Images,\
    Upload_Mineral_Top_Crop_Max_Valid,Upload_Mineral_Top_Crop_Max_Top_Images,\
    Upload_Max_Dynamic_Raw_Top,Upload_BigNumberPlate_Max,Upload_NumberPlate_Crop_Max,\
    top_image_valid
from secure_api import send_images,send_json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import os
import requests
from glob import glob
import datetime
import logging
import shutil
import httpx
import ssl

now = datetime.datetime.now()
start_date_time=now.strftime("%d%m%Y")
start_script_datetime=now.strftime("%d_%m_%Y_%H_%M")

# os.makedirs('../logs',exist_ok=True)
# logging.basicConfig(filename=root_path+f'/logs/upload_images_{start_date_time}.log', 
#                     level=logging.INFO, 
#                     format='%(asctime)s - %(levelname)s - %(message)s')

Current_log_path=root_path+f"/logs/Upload_images_Logs.log"
# backup_logs_path=root_path+f"/logs/Upload_images_backup/"
# os.makedirs(backup_logs_path,exist_ok=True)
# if os.path.exists(Current_log_path):
#     shutil.move(Current_log_path,backup_logs_path+f"Upload_Data_Logs_{start_script_datetime}.log")
FORMAT = "%(asctime)s: %(filename)s: %(levelname)s :%(lineno)5s:: - %(funcName)10s() :  %(message)s"
logging.basicConfig(filename=Current_log_path,
                    format=FORMAT,
                    filemode='a',
                    level=logging.DEBUG, # Set logging level
                    force=True)

# Path to the CA bundle
ca_cert_path = root_path+'/metadata/ca-bundle.pem'

# Create a custom SSL context with legacy renegotiation
def create_custom_ssl_context():
    context = ssl.create_default_context()
    context.options |= 0x4  # OP_LEGACY_SERVER_CONNECT (allows legacy renegotiation)
    context.load_verify_locations(cafile=ca_cert_path)
    return context



# Configure boto3's logger
boto3_logger = logging.getLogger('boto3')
boto3_logger.setLevel(logging.WARNING)

# Configure botocore's logger (if you are using boto3, botocore is used internally)
botocore_logger = logging.getLogger('botocore')
botocore_logger.setLevel(logging.WARNING)


def resize_image(image_path):
    try:
        dest_path=image_path.replace('/raw/','/raw_resized/')
        # print('dest_path : ',dest_path)
        img=cv2.imread(image_path)
        # print('img.shape : ',img.shape)
        img=cv2.resize(img,(0,0),fx=0.25,fy=0.25)
        cv2.imwrite(dest_path,img)
        
    except Exception as e:
        print('e',e)

def upload_file_to_s3(file, folder_name, file_name):
    try:
        s3 = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_access_key, region_name='ap-south-1')

        with BytesIO() as new_memory_stream:
            new_memory_stream.write(file.read())
            new_memory_stream.seek(0)  # Reset the file position to the beginning

            # Determine the content type based on the file name
            content_type, _ = mimetypes.guess_type(file_name)

            # Upload the file to S3 with the determined content type
            s3.upload_fileobj(new_memory_stream, public_bucket_name, (folder_name+'/'+ file_name), ExtraArgs={'ACL': 'public-read', 'ContentType': content_type})
            boto3_logger.info(f'Successfully uploaded {file_name} to {public_bucket_name}/{folder_name}')
            return True
    except Exception as e:
        # print(e)
        boto3_logger.info(f'Failed to upload {file_name} to {public_bucket_name}/{folder_name}')
        return False

def generate_url(folder_name,file_name):
    s3_client = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_access_key, region_name='ap-south-1')

    
    try:
        url = s3_client.generate_presigned_url('get_object', Params={'Bucket': public_bucket_name, 'Key': (folder_name+'/'+ file_name) }, ExpiresIn=3600, HttpMethod='GET')
        response = url.split('?')[0]
        boto3_logger.info(f'Successfully generate_url {file_name}')
           
        return response
    except Exception as e:
        # print(f"Error generating presigned URL: {e}")
        boto3_logger.info(f'Failed to generate_url {file_name}')
        return None

 
def check_time(current_time):
    day_start = 6
    day_end = 18
    current_hour = current_time.hour
    if day_start <= current_hour < day_end:
        return 'day'
    else:
        return 'night'


def _collect_top_crop_files(top_crop_dir, glob_patterns):
    seen = set()
    matched = []
    for pat in glob_patterns:
        for fp in glob(pat):
            nfp = os.path.normpath(fp)
            if nfp not in seen and os.path.isfile(nfp):
                seen.add(nfp)
                matched.append(nfp)
    return sorted(matched)


def add_mineral_top_camera_crops_to_paths(
    paths, transaction_path,
    max_count=None, max_valid_count=None,
):
    """
    Register Top_Camera* crops from top_crop/ (limits from config.py).

    - Top_Camera_Valid_* -> Mineral_Top_Crop_Valid only (not Valid_2, Valid_3)
    - Top_Camera_top_image_* -> Mineral_Top_Crop_1, Mineral_Top_Crop_2, ... (capped)
    Does not upload Top_Crop_*.png (Front_Top ANPR mineral crops).
    """
    if max_count is None:
        max_count = Upload_Mineral_Top_Crop_Max_Top_Images
    if max_valid_count is None:
        max_valid_count = Upload_Mineral_Top_Crop_Max_Valid
    top_crop_dir = os.path.join(transaction_path, 'top_crop')
    if not os.path.isdir(top_crop_dir):
        return

    top_image_patterns = [
        os.path.join(top_crop_dir, 'Top_Camera_top_image_*.jpg'),
        os.path.join(top_crop_dir, 'Top_Camera_top_image_*.jpeg'),
        os.path.join(top_crop_dir, 'Top_Camera_top_image_*.JPG'),
        os.path.join(top_crop_dir, 'Top_Camera_top_image_*.JPEG'),
    ]
    for idx, fp in enumerate(_collect_top_crop_files(top_crop_dir, top_image_patterns)[:max_count]):
        paths[f'Mineral_Top_Crop_{idx + 1}'] = ['top_crop', os.path.basename(fp)]

    valid_patterns = [
        os.path.join(top_crop_dir, 'Top_Camera_Valid_*.png'),
        os.path.join(top_crop_dir, 'Top_Camera_Valid_*.jpg'),
        os.path.join(top_crop_dir, 'Top_Camera_Valid_*.jpeg'),
        os.path.join(top_crop_dir, 'Top_Camera_Valid_*.PNG'),
        os.path.join(top_crop_dir, 'Top_Camera_Valid_*.JPG'),
    ]
    for idx, fp in enumerate(_collect_top_crop_files(top_crop_dir, valid_patterns)[:max_valid_count]):
        paths['Mineral_Top_Crop_Valid'] = ['top_crop', os.path.basename(fp)]
        break


def add_dynamic_raw_top_paths(paths, transaction_path):
    """
    Upload up to top_image_valid (config) raw/top_image_valid_* as Raw_Top_4+.
    Prefer last N when more exist (better exit frames). flag=1 set in upload loop.
    If none exist, fall back to capped raw/top_image_* (Upload_Max_Dynamic_Raw_Top).
    """
    max_valid = max(1, int(top_image_valid)) if top_image_valid else 3
    top_images_valid = sorted(glob(transaction_path + '/raw/top_image_valid_*'))
    # 1..max_valid: take last N when overflow (chronologically later frames)
    selected_valid = top_images_valid[-max_valid:] if top_images_valid else []
    for index, top_image_path in enumerate(selected_valid):
        paths[f'Raw_Top_{index + 4}'] = ['raw', os.path.basename(top_image_path)]
    if not top_images_valid:
        top_images_non_valid = sorted(
            p for p in glob(transaction_path + '/raw/top_image_*')
            if '_valid_' not in os.path.basename(p)
        )
        # Fallback: last synced top frame (best exit shot), not first
        fallback = top_images_non_valid[-Upload_Max_Dynamic_Raw_Top:]
        for index, top_image_path in enumerate(fallback):
            paths[f'Raw_Top_{index + 4}'] = ['raw', os.path.basename(top_image_path)]


def build_live_test_upload_paths(path):
    """
    Fixed upload set plus capped raw/top_image_valid_* (see top_image_valid in config).
    """
    paths = {
        'Raw_ANPR': ['raw_resized', 'Anpr_Raw.png'],
        'Raw_Top_1': ['raw', 'Top_Raw_1.jpg'],
        'Raw_Top_2': ['raw_resized', 'Top_Raw_2.jpg'],
        'Raw_Top_3': ['raw_resized', 'Top_Raw_3.jpg'],
        'Crop_NP_Valid': ['processed', 'NumberPlate_Valid.png'],
        'Crop_NP_0': ['processed', 'NumberPlate_Crop_0.png'],
        'Crop_NP_Big_Valid': ['processed', 'BigNumberPlate_Valid.png'],
        'Crop_NP_Big_0': ['processed', 'BigNumberPlate_Crop_0.png'],
    }
    add_dynamic_raw_top_paths(paths, path)
    if Upload_Mineral_Top_Crop_Images:
        add_mineral_top_camera_crops_to_paths(paths, path)
    return paths


# @app.get("/upload_data/")
# async def upload_data(path:str):
def upload_image(logid,path,top_class_name,created_data,Valid_Image=False):
    

    start=time.time()

    
    images_captured_by_top_camera=path+'/raw/top_image**'
    images_captured_by_top_camera_prediction=path+'/prediction/pred_top_image**'
    
    save_path='output/'+path.split('/')[-1]+'/' #'/'.join((path.split('/')[1:-1]))+'/'

    save_json_path=path+'/json/image_upload_jsons/'

    os.makedirs(path+'/raw_resized',exist_ok=True)
    os.makedirs(save_json_path,exist_ok=True)
    
    raw_images_path_list=glob(path+'/raw/*Raw*')
    # top_image_path_list=glob(path+'/raw/top_image**')
    
    start_time_resize_image=time.time()
    logging.info(f'resize_image Started :')
    for image_path in raw_images_path_list:
        # print('image_path : ',image_path)
        resize_image(image_path)
    # for image_path in top_image_path_list:
    #     # print('image_path : ',image_path)
    #     resize_image(image_path)
    

    logging.info(f'resize_image Done : {str(round(time.time()-start_time_resize_image,2))}')


        


    paths={
        'Raw_ANPR':['raw','Anpr_Raw.png'],
        'Pred_ANPR':['prediction','Anpr_Pred.png'],
        'Raw_Top_1':['raw','Top_Raw_1.jpg'],
        'Raw_Top_2':['raw','Top_Raw_2.jpg'],
        'Raw_Top_3':['raw','Top_Raw_3.jpg'],
        'Pred_Top_1':['prediction','Top_Pred_1.jpg'],
        'Pred_Top_2':['prediction','Top_Pred_2.jpg'],
        'Pred_Top_3':['prediction','Top_Pred_3.jpg'],
        'Crop_NP_Valid':['processed','NumberPlate_Valid.png'],
        'Crop_NP_Big_Valid':['processed','BigNumberPlate_Valid.png'],
        'Crop_NP_0':['processed','NumberPlate_Crop_0.png'],
        'Crop_NP_1':['processed','NumberPlate_Crop_1.png'],
        'Crop_NP_Big_0':['processed','BigNumberPlate_Crop_0.png'],
        'Crop_NP_Big_1':['processed','BigNumberPlate_Crop_1.png']
        }
    current_time = datetime.datetime.now()
    # if check_time(current_time)=='day' and False:
    #     for image_path in raw_images_path_list:
    #         if 'Top_Raw' in image_path and top_class_name =='mining_full':
    #             print('Path : mining_full : ',path )
            
    #             paths['Raw_Top_1']=['raw','Top_Raw_1.jpg']
    #             paths['Raw_Top_2']=['raw','Top_Raw_2.jpg']
    #             paths['Raw_Top_3']=['raw','Top_Raw_3.jpg']
    #             #images_captured by top cameras : 
    #             top_images_path_list=glob(images_captured_by_top_camera)
    #             # print('top_images_path_list : ',len(top_images_path_list))
    #             # 'Raw_Top_3': ['raw', 'Top_Raw_3.jpg']
    #             # if len(top_images_path_list)>5:
    #             #     top_images_path_list=top_images_path_list[-5:]
    #             for index,top_image_path in enumerate(sorted(top_images_path_list)):
    #                 paths[f'Raw_Top_{str(index+4)}']=['raw',top_image_path.split('/')[-1]]
    # else:

    for image_path in raw_images_path_list:
        if 'Top_Raw' in image_path:            
            paths['Raw_Top_1']=['raw','Top_Raw_1.jpg']
            paths['Raw_Top_2']=['raw','Top_Raw_2.jpg']
            paths['Raw_Top_3']=['raw','Top_Raw_3.jpg']
            #images_captured by top cameras : 
    top_images_path_list=glob(images_captured_by_top_camera)
    top_pred_images_path_list=glob(images_captured_by_top_camera_prediction)
    
    # if len(top_images_path_list)>5:
    #     top_images_path_list=top_images_path_list[-5:]
    # if len(top_pred_images_path_list)>5:
    #     top_pred_images_path_list=top_pred_images_path_list[-5:]

    # print("top_images_path_list : ",len(top_images_path_list))
    for index,top_image_path in enumerate(sorted(top_images_path_list)):
        paths[f'Raw_Top_{str(index+4)}']=['raw',top_image_path.split('/')[-1]]

    for index,top_image_pred_path in enumerate(sorted(top_pred_images_path_list)):
        paths[f'Pred_Top_{str(index+4)}']=['prediction',top_image_pred_path.split('/')[-1]]

    if Upload_Mineral_Top_Crop_Images:
        add_mineral_top_camera_crops_to_paths(paths, path)
    

        
    # print('paths : ',paths)
        
    start_time_s3_upload=time.time()
    logging.info(f'S3 Image Uploding Started')
    for imageCategory,relative_path in paths.items():
        # AWS
        request_data={
            "logId": logid,
            "remark": "",
            "imageCategory": "",
            "imagePath": "",
            "isProccessed": True,
            "flag": 0,
            "createdDate":created_data
        }

        # New API MP
        # request_data={
        #     "LogId": logid,
        #     "ImagePath": "test",
        #     "ImageCategory": imageCategory,
        #     "IsProccessed": True,
        #     "Flag": 0,
        #     "CreatedDate": created_data,
        #     "Remark":"ok"
        # }
        
        
        folder_name=relative_path[0] 
        file_name=relative_path[1]
        file_path=path+'/'+folder_name+'/'+file_name

        # print('file_path : ',file_path)
        if os.path.exists(file_path):
            if Valid_Image:# Taking valid images only
                if not '_valid_' in file_path:
                    continue




            # print("Uploading Started : ",file_path)
            # Upload Images using AWS
            with open(file_path, 'rb') as file:
                if upload_file_to_s3(file,save_path+folder_name, file_name):
                    # AWS data upload and generate
                    result=generate_url(save_path+folder_name,file_name)
                    # print('url : ',result)
                    if '_valid_' in file_path:
                        request_data['flag']=1
                    request_data['imageCategory']=imageCategory
                    request_data['imagePath']=result
                    
                    image_count=len(glob(save_json_path+f'/{imageCategory}**'))
                    if image_count==0:
                        request_json_name=f'request_{imageCategory}.json'
                        response_json_name=f'response_{imageCategory}.json'
                    else:
                        request_json_name=f'request_{imageCategory}_{str(image_count+1)}.json'
                        response_json_name=f'response_{imageCategory}_{str(image_count+1)}.json'

                    logging.info(f'request save: {imageCategory} {file_name}')
                    with open(save_json_path+request_json_name, 'w') as f:
                        json.dump(request_data, f)
                    response={}
                    try:
                        logging.info(f'request sent: {imageCategory} {file_name}')
                        # print('request_data : ',request_data)
                        response,message=send_json(Image_path_upload_API,json_data=[request_data])
                        logging.info(f'response recived: {imageCategory} {file_name}')
                    except Exception as e:
                        print('e : ',e)
                        
                        continue
                    
                    with open(save_json_path+response_json_name, 'w') as f:
                        json.dump(response, f)
                        logging.info(f'response save: {imageCategory} {file_name}')

                else:
                    print(f"Upload failed: {file_path}")
                    logging.info(f'Upload failed: {file_path}')

        else:
            print(f"image not found : {file_path}")
            logging.info(f'image not found : {file_path}')
            # print('File Not Found :  ',file_path)
    logging.info(f'S3 Image Uploding Done : {str(round(time.time()-start_time_s3_upload,2))}')
        
def upload_image_live(logid_Live,logid_Test,path,created_data,Valid_Image=False):
    


    start=time.time()

    
    images_captured_by_top_camera=path+'/raw/top_image**'
    images_captured_by_top_camera_valid=path+'/raw/top_image_valid_**'
    
    images_captured_by_top_camera_prediction=path+'/prediction/pred_top_image**'
    save_path='output/'+path.split('/')[-1]+'/' #'/'.join((path.split('/')[1:-1]))+'/'

    save_json_path=path+'/json/image_upload_jsons/'

    os.makedirs(path+'/raw_resized',exist_ok=True)
    os.makedirs(save_json_path,exist_ok=True)
    
    raw_images_path_list=glob(path+'/raw/*Raw*')
    
    start_time_resize_image=time.time()
    logging.info(f'resize_image Started :')
    for image_path in raw_images_path_list:
        # print('image_path : ',image_path)
        resize_image(image_path)

    logging.info(f'resize_image Done : {str(round(time.time()-start_time_resize_image,2))}')


        


    paths = build_live_test_upload_paths(path)
    top_images_valid_path_list = glob(images_captured_by_top_camera_valid)
    # print('final paths : ',paths)
        
    start_time_s3_upload=time.time()
    # logging.info(f'S3 Image Uploding Started')

    for imageCategory,relative_path in paths.items():
        # print(imageCategory,': ',relative_path)
        # AWS
        # request_data={
        #     "logId": logid,
        #     "remark": "",
        #     "imageCategory": "",
        #     "imagePath": "",
        #     "isProccessed": True,
        #     "flag": 0,
        #     "createdDate":created_data
        # }

        

        # New API MP
        # request_data={
        #     "LogId": logid,
        #     "ImagePath": "test",
        #     "ImageCategory": imageCategory,
        #     "IsProccessed": True,
        #     "Flag": 0,
        #     "CreatedDate": created_data,
        #     "Remark":"ok"
        # }

        #Live 
        request_data_Live={
            "LogId": logid_Live,
            "Remark": "Remark ok",
            "ImageCategory":imageCategory,
            "ImagePath": "",
            "IsProccessed": True,
            "flag": 0,
            "CreatedDate":created_data
        }

        #Test
        request_data_Test={
            "LogId": logid_Test,
            "Remark": "Remark ok",
            "ImageCategory":imageCategory,
            "ImagePath": "",
            "IsProccessed": True,
            "flag": 0,
            "CreatedDate":created_data
        }
        
        
        folder_name=relative_path[0] 
        file_name=relative_path[1]
        file_path=path+'/'+folder_name+'/'+file_name
        # print("image_path : ",image_path)
        request_data_Test['ImagePath']=folder_name
        request_data_Live['ImagePath']=folder_name
        
        if os.path.exists(file_path):
            if len(top_images_valid_path_list) > 0 and Valid_Image:
                # When valid top frames exist, skip only non-valid top_image_* in raw/
                # (old check used 'Raw' and skipped all /raw/top_image_* and top_crop paths)
                norm_path = file_path.replace('\\', '/')
                if (
                    '/raw/top_image_' in norm_path
                    and '_valid_' not in norm_path
                    and 'NumberPlate' not in file_path
                    and 'BigNumberPlate' not in file_path
                ):
                    continue

            if '_valid_' in file_path:
                request_data_Test['flag']=1
                request_data_Live['flag']=1
            
            # request_data_Test['imageCategory']=imageCategory
            # request_data_Test['imagePath']=result

            # request_data_Live['imageCategory']=imageCategory
            # request_data_Live['imagePath']=result


            # print('Found file_path : ',file_path)
            # print("file_path : ",file_path)
            files1 = {'Files': open(file_path, 'rb')}
                
            image_count=len(glob(save_json_path+f'/{imageCategory}**'))
            if image_count==0:
                request_json_name_Live=f'request_{imageCategory}_Live.json'
                response_json_name_Live=f'response_{imageCategory}_Live.json'
                request_json_name_Test=f'request_{imageCategory}_Test.json'
                response_json_name_Test=f'response_{imageCategory}_Test.json'
                
            else:
                request_json_name_Live=f'request_{imageCategory}_{str(image_count+1)}_Live.json'
                response_json_name_Live=f'response_{imageCategory}_{str(image_count+1)}_Live.json'
                
                request_json_name_Test=f'request_{imageCategory}_{str(image_count+1)}_Test.json'
                response_json_name_Test=f'response_{imageCategory}_{str(image_count+1)}_Test.json'


            
            
            logging.info(f'request save: {imageCategory}')

            if Live_Data_Upload and logid_Live!=-1:
                with open(save_json_path+request_json_name_Live, 'w') as f:
                    json.dump(request_data_Live, f)

                try:
                    logging.info(f'request sent: {imageCategory}')
                    # print('request_data_Live : ',request_data_Live)
                    # response=requests.post(Image_path_upload_API,json=[request_data])
                    
                    response_Live,message=send_images(Image_path_upload_API_Live,base_data=request_data_Live,files1=files1)
                    print("Image upload response_Live ",response_Live)
                    print("Image upload message ",message)
                    

                    logging.info(f'Live response recived: {imageCategory}')

                    with open(save_json_path+response_json_name_Live, 'w') as f:
                        json.dump(response_Live, f)
                        logging.info(f'response Live save: {imageCategory}')

                except Exception as e:
                    print('Live image upload error : ',e)
                    continue
            
                
            if Upload_Test_Images and Test_Data_Upload and logid_Test != -1:
                with open(save_json_path+request_json_name_Test, 'w') as f:
                    json.dump(request_data_Test, f)

                try:
                    logging.info(f'request sent: {imageCategory}')
                    response_Test,message=send_images(Image_path_upload_API_Test,base_data=request_data_Test,files1=files1)
                    response_Test=response_Test#.json()
                    logging.info(f'Test response recived: {imageCategory}')

                    with open(save_json_path+response_json_name_Test, 'w') as f:
                        json.dump(response_Test, f)
                        logging.info(f'response Test save: {imageCategory}')

                except Exception as e:
                    print('e : ',e)
                    continue

        else:
            print("Image File not found : ",file_path) 
    logging.info(f'Server Image Uploding Done : {str(round(time.time()-start_time_s3_upload,2))}')

def upload_image_live_api_st(logid_Live,logid_Test,path,created_data,number_plate_flag,anpr_flag,top_flag,Valid_Image=False):
    


    start=time.time()

    
    images_captured_by_top_camera=path+'/raw/top_image**'
    images_captured_by_top_camera_valid=path+'/raw/top_image_valid_**'
    
    images_captured_by_top_camera_prediction=path+'/prediction/pred_top_image**'
    save_path='output/'+path.split('/')[-1]+'/' #'/'.join((path.split('/')[1:-1]))+'/'

    save_json_path=path+'/json/image_upload_jsons/'

    os.makedirs(path+'/raw_resized',exist_ok=True)
    os.makedirs(save_json_path,exist_ok=True)
    
    raw_images_path_list=glob(path+'/raw/*Raw*')
    
    start_time_resize_image=time.time()
    logging.info(f'resize_image Started :')
    for image_path in raw_images_path_list:
        # print('image_path : ',image_path)
        resize_image(image_path)

    logging.info(f'resize_image Done : {str(round(time.time()-start_time_resize_image,2))}')


    paths={}

    paths = {}
    if number_plate_flag:
        paths['Crop_NP_Valid'] = ['processed', 'NumberPlate_Valid.png']
        paths['Crop_NP_0'] = ['processed', 'NumberPlate_Crop_0.png']
        paths['Crop_NP_Big_Valid'] = ['processed', 'BigNumberPlate_Valid.png']
        paths['Crop_NP_Big_0'] = ['processed', 'BigNumberPlate_Crop_0.png']
    if anpr_flag:
        paths['Raw_ANPR'] = ['raw_resized', 'Anpr_Raw.png']
    top_images_valid_path_list = glob(images_captured_by_top_camera_valid)
    if top_flag:
        paths['Raw_Top_1'] = ['raw', 'Top_Raw_1.jpg']
        add_dynamic_raw_top_paths(paths, path)
    if Upload_Mineral_Top_Crop_Images:
        add_mineral_top_camera_crops_to_paths(paths, path)
        
    # print('final paths : ',paths)
    # return 
    start_time_s3_upload=time.time()
    # logging.info(f'S3 Image Uploding Started')
    all_image_upload_status={}
    all_image_upload_json_path='all_image_upload'
    all_image_upload_json_path_list=glob(save_json_path+all_image_upload_json_path+'**')
    if len(all_image_upload_json_path_list)==0:
        all_image_upload_json_path_name='all_image_upload_1.json'
    else:
        all_image_upload_json_path_name=f'all_image_upload_{len(all_image_upload_json_path_list)+1}.json'
    for imageCategory,relative_path in paths.items():
        # print(imageCategory,': ',relative_path)


        #Live 
        request_data_Live={
            "LogId": logid_Live,
            "Remark": "Remark ok",
            "ImageCategory":imageCategory,
            "ImagePath": "",
            "IsProccessed": True,
            "flag": 0,
            "CreatedDate":created_data
        }

        #Test
        request_data_Test={
            "LogId": logid_Test,
            "Remark": "Remark ok",
            "ImageCategory":imageCategory,
            "ImagePath": "",
            "IsProccessed": True,
            "flag": 0,
            "CreatedDate":created_data
        }
        
        
        
        folder_name=relative_path[0] 
        file_name=relative_path[1]
        file_path=path+'/'+folder_name+'/'+file_name
        # print("image_path : ",image_path)
        request_data_Test['ImagePath']=folder_name
        request_data_Live['ImagePath']=folder_name

        #temp_all_data
        #
        temp_all_data={
            "file_path":path+'/'+folder_name+'/'+file_name,
            "request_data":{},
            "respose_data":{},
            "message":{}
        }
        
        if os.path.exists(file_path):


            if len(top_images_valid_path_list) > 0 and Valid_Image:
                norm_path = file_path.replace('\\', '/')
                if (
                    '/raw/top_image_' in norm_path
                    and '_valid_' not in norm_path
                    and 'NumberPlate' not in file_path
                    and 'BigNumberPlate' not in file_path
                ):
                    continue

            if '_valid_' in file_path:
                request_data_Test['flag']=1
                request_data_Live['flag']=1
            

            # print('Found file_path : ',file_path)
            # print("file_path : ",file_path)
            files1 = {'Files': open(file_path, 'rb')}
                
            image_count=len(glob(save_json_path+f'/{imageCategory}**'))
            if image_count==0:
                request_json_name_Live=f'request_{imageCategory}_Live.json'
                response_json_name_Live=f'response_{imageCategory}_Live.json'
                request_json_name_Test=f'request_{imageCategory}_Test.json'
                response_json_name_Test=f'response_{imageCategory}_Test.json'
                
            else:
                request_json_name_Live=f'request_{imageCategory}_{str(image_count+1)}_Live.json'
                response_json_name_Live=f'response_{imageCategory}_{str(image_count+1)}_Live.json'
                
                request_json_name_Test=f'request_{imageCategory}_{str(image_count+1)}_Test.json'
                response_json_name_Test=f'response_{imageCategory}_{str(image_count+1)}_Test.json'


            
            
            logging.info(f'request save: {imageCategory}')

            if Live_Data_Upload and logid_Live!=-1:
                with open(save_json_path+request_json_name_Live, 'w') as f:
                    json.dump(request_data_Live, f)

                try:
                    logging.info(f'request sent: {imageCategory}')
                    # print("uplaoding file : ",file_path)
                    temp_all_data['request_data']=request_data_Live
                    response_Live,message=send_images(Image_path_upload_API_Live,base_data=request_data_Live,files1=files1)
                    # print("response_Live : ",response_Live)
                    # print("message : ",message)
                    temp_all_data['respose_data']=response_Live
                    temp_all_data['message']=message

                    all_image_upload_status[file_path]=temp_all_data
                    
                    with open(save_json_path+response_json_name_Live, 'w') as f:
                        json.dump(response_Live, f)
                        logging.info(f'response Live save: {imageCategory}')

                except Exception as e:
                    print('Live image upload error : ',e)
                    continue
            
                
            if Upload_Test_Images and Test_Data_Upload and logid_Test != -1:
                with open(save_json_path+request_json_name_Test, 'w') as f:
                    json.dump(request_data_Test, f)

                try:
                    logging.info(f'request sent: {imageCategory}')
                    response_Test,message=send_images(Image_path_upload_API_Test,base_data=request_data_Test,files1=files1)
                    response_Test=response_Test.json()
                    logging.info(f'Test response recived: {imageCategory}')

                    with open(save_json_path+response_json_name_Test, 'w') as f:
                        json.dump(response_Test, f)
                        logging.info(f'response Test save: {imageCategory}')

                except Exception as e:
                    print('e : ',e)
                    continue

        else:
            print("Image File not found : ",file_path) 
        
    logging.info(f'Server Image Uploding Done : {str(round(time.time()-start_time_s3_upload,2))}')
    with open(save_json_path+all_image_upload_json_path_name, 'w') as f:
        json.dump(all_image_upload_status, f)
class main():
    def main(self,logid,file_path,top_class_name,created_data):
        start_time=time.time()
        logging.info(f'----------------------------------Uploding Started : {file_path}----------------------------------')
        try:
            upload_image(
                logid=logid, path=file_path, top_class_name=top_class_name,
                created_data=created_data, Valid_Image=False,
            )
        except Exception as e:
            logging.exception(f'upload_image failed: {file_path} : {e}')
            raise
        logging.info(f'Uploding Done : {file_path} : {str(round(time.time()-start_time,2))}')
        logging.info(f'----------------------------------Uploding Done : {file_path}----------------------------------')
            
   
class main_live():
    def main(self,logid_Live,logid_Test,file_path,top_class_name,created_data):
        start_time=time.time()
        logging.info(f'----------------------------------Live Uploding Started : {file_path}----------------------------------')
        try:
            upload_image_live(
                logid_Live=logid_Live, logid_Test=logid_Test, path=file_path,
                created_data=created_data, Valid_Image=True,
            )
        except Exception as e:
            logging.exception(f'upload_image_live failed: {file_path} : {e}')
            raise
        logging.info(f'Uploding Done : {file_path} : {str(round(time.time()-start_time,2))}')
        logging.info(f'----------------------------------Live Uploding Done : {file_path}----------------------------------')
           
# if __name__=="__main__":
#     main_obj=main_live()
#     logid_Live=2
#     logid_Test=-1
#     top_class_name=''
#     created_data="26_06_2026_04_03_18"
#     path='/home/aikernel/output/IND0032260620260100099/'
#     main_obj.main(logid_Live,logid_Test,path,top_class_name,created_data)
