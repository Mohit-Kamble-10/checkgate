
# -*- coding: utf-8 -*-
import sys
import os
import time
import argparse
os.environ["CUDA_VISIBLE_DEVICES"]="0"
import torch
import torch.nn as nn
import torch.backends.cudnn as cudnn
from torch.autograd import Variable
import pandas as pd
from PIL import Image
import cv2
from skimage import io
import numpy as np
import craft_utils
import imgproc
import file_utils
import json
import zipfile

from craft import CRAFT
from crop_images import rearrange_crop_images
from collections import OrderedDict
from configs.config import root_path

# full_path=root_path+'/src/'
full_path=root_path+'/metadata/'

cuda=torch.cuda.is_available()

print('cuda : ',cuda)
def copyStateDict(state_dict):
    if list(state_dict.keys())[0].startswith("module"):
        start_idx = 1
    else:
        start_idx = 0
    new_state_dict = OrderedDict()
    for k, v in state_dict.items():
        name = ".".join(k.split(".")[start_idx:])
        new_state_dict[name] = v
    return new_state_dict

def str2bool(v):
    return v.lower() in ("yes", "y", "true", "t", "1")






# parser = argparse.ArgumentParser(description='CRAFT Text Detection')
# parser.add_argument('--trained_model', default=full_path+'weights/craft_mlt_25k.pth', type=str, help='pretrained model')#craft_mlt_25k
# # parser.add_argument('--text_threshold', default=0.2, type=float, help='text confidence threshold')
# # parser.add_argument('--low_text', default=0.2, type=float, help='text low-bound score')
# parser.add_argument('--text_threshold', default=0.4, type=float, help='text confidence threshold')
# parser.add_argument('--low_text', default=0.4, type=float, help='text low-bound score')
# parser.add_argument('--link_threshold', default=0.4, type=float, help='link confidence threshold')
# parser.add_argument('--cuda', default='1', type=str2bool, help='Use cuda for inference')
# parser.add_argument('--canvas_size', default=192, type=int, help='image size for inference')
# parser.add_argument('--mag_ratio', default=1.5, type=float, help='image magnification ratio')
# parser.add_argument('--poly', default=True, action='store_true', help='enable polygon type')
# parser.add_argument('--show_time', default=True, action='store_true', help='show processing time')
# parser.add_argument('--test_folder', default='../data_17200/test_craft/', type=str, help='folder path to input images')
# parser.add_argument('--refine', default=True, action='store_true', help='enable link refiner')
# parser.add_argument('--refiner_model', default=full_path+'weights/craft_refiner_CTW1500.pth', type=str, help='pretrained refiner model')
# args = parser.parse_args()

class test:
    def __init__(self) -> None:

        self.trained_model=full_path+'weights/craft_mlt_25k.pth'
        self.text_threshold=0.4
        self.low_text=0.4
        self.link_threshold=0.4
        self.cuda='0'
        self.canvas_size=192
        # self.mag_ratio=1.5
        self.mag_ratio=2.5
        self.poly=True
        self.show_time=True
        self.test_folder='../data_17200/test_craft/'
        self.refine=True
        self.refiner_model=full_path+'weights/craft_refiner_CTW1500.pth'
        
        


args=test()

# {
#     'trained_model':full_path+'weights/craft_mlt_25k.pth',
#     'text_threshold':0.4,
#     'low_text':0.4,
#     'cuda':'0',
#     'canvas_size':192,
#     'mag_ratio':1.5,
#     'poly':True,
#     'show_time':True,
#     'test_folder':'../data_17200/test_craft/',
#     'refine':True,
#     'refiner_model':full_path+'weights/craft_refiner_CTW1500.pth',
    
# }





def test_net(net, image, text_threshold, link_threshold, low_text, cuda, poly, refine_net=None):
    t0 = time.time()

    # resize
    img_resized, target_ratio, size_heatmap = imgproc.resize_aspect_ratio(image, args.canvas_size, interpolation=cv2.INTER_LINEAR, mag_ratio=args.mag_ratio)
    ratio_h = ratio_w = 1 / target_ratio

    # preprocessing
    x = imgproc.normalizeMeanVariance(img_resized)
    x = torch.from_numpy(x).permute(2, 0, 1)    # [h, w, c] to [c, h, w]
    x = Variable(x.unsqueeze(0))                # [c, h, w] to [b, c, h, w]
    if cuda:
        x = x.cuda()
        # x=x.half()

    # forward pass
    with torch.no_grad():
        # net=net.half()
        y, feature = net(x)
        # print('Prediction Done')

    # make score and link map
    score_text = y[0,:,:,0].cpu().data.numpy()
    score_link = y[0,:,:,1].cpu().data.numpy()

    # refine link
    if refine_net is not None:
        with torch.no_grad():
            y_refiner = refine_net(y, feature)
        score_link = y_refiner[0,:,:,0].cpu().data.numpy()

    t0 = time.time() - t0
    t1 = time.time()
    # polys=[]
    # Post-processing
    boxes, polys = craft_utils.getDetBoxes(score_text, score_link, text_threshold, link_threshold, low_text, poly)
    # print('boxes :\n',boxes)
    # print('polys :\n',polys,type(polys),len(polys))
    
    try:
        polys=np.array(polys)
    except:
        polys=boxes


    

    # coordinate adjustment
    boxes = craft_utils.adjustResultCoordinates(boxes, ratio_w, ratio_h)
    polys = craft_utils.adjustResultCoordinates(polys, ratio_w, ratio_h)
    for k in range(len(polys)):
        if polys[k] is None: polys[k] = boxes[k]

    t1 = time.time() - t1

    # render results (optional)
    render_img = score_text.copy()
    render_img = np.hstack((render_img, score_link))
    ret_score_text = imgproc.cvt2HeatmapImg(render_img)

    # if args.show_time : print("\ninfer/postproc time : {:.3f}/{:.3f}".format(t0, t1))
    # print('test_net : Done')
    return boxes, polys, ret_score_text



# if __name__ == '__main__':
def main_craft_from_folder():
    """ For test images in a folder """
    image_list, _, _ = file_utils.get_files(args.test_folder)

    result_folder ='../data/craft_result/'
    crops_folder='../data/crops_folder/'
    # if not os.path.isdir(result_folder):
    os.makedirs(result_folder,exist_ok=True)
    os.makedirs(crops_folder,exist_ok=True)


    # load net
    net = CRAFT()     # initialize
    reg_crop_images_obj=rearrange_crop_images()
    # print('Loading weights from checkpoint (' + args.trained_model + ')')
    if args.cuda:
        net.load_state_dict(copyStateDict(torch.load(args.trained_model)))
        # net.load_state_dict(torch.load(args.trained_model))
        print('Weights Loaded On GPU')
        
    else:
        net.load_state_dict(copyStateDict(torch.load(args.trained_model, map_location='cpu')))
        print('Weights Loaded On CPU')

    if args.cuda:
        net = net.cuda()
        net = torch.nn.DataParallel(net)
        cudnn.benchmark = False

    net.eval()

    # # LinkRefiner
    refine_net = None
    if args.refine:
        from refinenet import RefineNet
        refine_net = RefineNet()
        # print('Loading weights of refiner from checkpoint (' + args.refiner_model + ')')
        # print('args.cuda : ',args.cuda)
        if args.cuda:
            refine_net.load_state_dict(copyStateDict(torch.load(args.refiner_model)))
            refine_net = refine_net.cuda()
            refine_net = torch.nn.DataParallel(refine_net)
            print('refine_net Loaded On GPU....')
        else:
            refine_net.load_state_dict(copyStateDict(torch.load(args.refiner_model, map_location='cpu')))
            print('refine_net Loaded On CPU....')

        refine_net.eval()
        args.poly = True

    t = time.time()

    # load data
    for k, image_path in enumerate(image_list[:]):
        try:
            
            # image_nam0000e=image_path.split('/')[-1]
            # print('image_path : ',k,image_path,image_name)
            # if image_name not in rotation_issue:
            #     continue
            # print("Test image {:d}/{:d}: {:s}".format(k+1, len(image_list), image_path), end='\r')
            image = imgproc.loadImage(image_path)
            # print('image.shape : ',image.shape)
            w,h,_=image.shape
            inf_t = time.time()
            bboxes, polys, score_text = test_net(net, image, args.text_threshold, args.link_threshold, args.low_text, args.cuda, args.poly, refine_net)
            #print('bboxes : ',bboxes)
            # print('polys : ',polys)
            processed_polys=reg_crop_images_obj.preprocess(polys,w*h)
            renew_polys_dict=reg_crop_images_obj.rearrange(processed_polys)
            # renew_polys_dict {1:[crops]} line : crop
            sorted_image_crop_list,sorted_rotated_image_crop_list=reg_crop_images_obj.crop_poly(image,renew_polys_dict)
            
            print('sorted_image_crop_list : Done')
            print('Inferance Time : ',time.time()-inf_t)
            
            
            # save score text
            filename, file_ext = os.path.splitext(os.path.basename(image_path))
            # mask_file = result_folder + "/res_" + filename + '_mask.jpg'
            # cv2.imwrite(mask_file, score_text)
            
            os.makedirs(crops_folder+filename,exist_ok=True)
            # if len(crop_images_list)==1:
            cv2.imwrite(crops_folder+filename+'/'+filename+'_org.jpg',image)
                
            for index,image_crop in enumerate(sorted_image_crop_list):
                image_crop=cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB)
                cv2.imwrite(crops_folder+filename+'/'+filename+str(index)+'.jpg',image_crop)
                # cv2.imwrite(crops_folder+filename+str(index)+'.jpg',image_crop)
                # cv2.imwrite(crops_folder+filename+'.jpg',image_crop)

            for index,image_crop in enumerate(sorted_rotated_image_crop_list):
                image_crop=cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB)
                cv2.imwrite(crops_folder+filename+'/'+filename+'_'+str(index)+'_rotated.jpg',image_crop)
            
            
            
            

            file_utils.saveResult(image_path, image[:,:,::-1], polys, dirname=result_folder)
            # break
            
        except Exception as e:
            print('Error Found : ',image_path)
            print(e)
    print("elapsed time : {}s".format(time.time() - t))

def main_craft_from_xlsx():
    """ For test images in a folder """
    #image_list, _, _ = file_utils.get_files(args.test_folder)

    result_folder = '../data/craft_result/'
    crops_folder='../data/crops_folder/'
    # if not os.path.isdir(result_folder):
    os.makedirs(result_folder,exist_ok=True)
    os.makedirs(crops_folder,exist_ok=True)


    # load net
    net = CRAFT()     # initialize
    reg_crop_images_obj=rearrange_crop_images()
    # print('Loading weights from checkpoint (' + args.trained_model + ')')
    if args.cuda:
        net.load_state_dict(copyStateDict(torch.load(args.trained_model)))
        # net.load_state_dict(torch.load(args.trained_model))
        print('Weights Loaded On GPU')
        
    else:
        net.load_state_dict(copyStateDict(torch.load(args.trained_model, map_location='cpu')))
        print('Weights Loaded On CPU')

    if args.cuda:
        net = net.cuda()
        net = torch.nn.DataParallel(net)
        cudnn.benchmark = False

    net.eval()

    # # LinkRefiner
    refine_net = None
    if args.refine:
        from refinenet import RefineNet
        refine_net = RefineNet()
        # print('Loading weights of refiner from checkpoint (' + args.refiner_model + ')')
        # print('args.cuda : ',args.cuda)
        if args.cuda:
            refine_net.load_state_dict(copyStateDict(torch.load(args.refiner_model)))
            refine_net = refine_net.cuda()
            refine_net = torch.nn.DataParallel(refine_net)
            print('refine_net Loaded On GPU....')
        else:
            refine_net.load_state_dict(copyStateDict(torch.load(args.refiner_model, map_location='cpu')))
            print('refine_net Loaded On CPU....')

        refine_net.eval()
        args.poly = True

    t = time.time()

    # load data
    dataframe=pd.read_excel('../data/csvs/ANPR_Analysis.xlsx')
    
    # dataframe_300=pd.read_csv('../data/csvs/Analysis_300.csv')
    # to_analyise=dataframe_300['Image_Name'].to_list()
    final_list=[]
    for k, row_data in dataframe.iterrows():
        # if not row_data['Image_Name'] in to_analyise:
            # continue
        # print('row_data : \n',k,row_data)
        final_list.append(row_data)

        try:
                #print("Test image {:d}/{:d}: {:s}".format(k+1, len(image_list), image_path), end='\r')
            image_path_list=row_data['NP_crop_paths'].split(',')
            crop_image_path_str=''
            for image_path in image_path_list:
                print('image_path : ',image_path)
                # save score text
                filename, file_ext = os.path.splitext(os.path.basename(image_path))
                os.makedirs(crops_folder+filename,exist_ok=True)

                crop_image_path_str_temp=''
                image = imgproc.loadImage(image_path)
                # print('image.shape : ',image.shape)
                w,h,_=image.shape
                inf_t = time.time()
                bboxes, polys, score_text = test_net(net, image, args.text_threshold, args.link_threshold, args.low_text, args.cuda, args.poly, refine_net)
                #print('bboxes : ',bboxes)
                # print('polys : ',polys)
                if len(polys)==0:
                    continue
                processed_polys=reg_crop_images_obj.preprocess(polys,w*h)
                renew_polys_dict=reg_crop_images_obj.rearrange(processed_polys)
                # renew_polys_dict {1:[crops]} line : crop
                sorted_image_crop_list,sorted_rotated_image_crop_list=reg_crop_images_obj.crop_poly(image,renew_polys_dict)

                
                with open(crops_folder+filename+'/sorted_crop_list.txt', "w") as output:
                    output.write(str(renew_polys_dict))
                
                # with open(crops_folder+filename+'/sorted_crop_list.txt', 'w', encoding='utf-8') as f:
                #     json.dump(renew_polys_dict, f, ensure_ascii=False, indent=4)
                                
                print('sorted_image_crop_list : Done')
                # print('Inferance Time : ',time.time()-inf_t)
                
                
                

                # mask_file = result_folder + "/res_" + filename + '_mask.jpg'
                # cv2.imwrite(mask_file, score_text)
                
                
                # if len(crop_images_list)==1:
                
                # cv2.imwrite(crops_folder+filename+'/'+filename+'_org.jpg',image)
                    
                # for index,image_crop in enumerate(sorted_image_crop_list):
                #     image_crop=cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB)
                #     cv2.imwrite(crops_folder+filename+'/'+filename+str(index)+'.jpg',image_crop)

                    # cv2.imwrite(crops_folder+filename+str(index)+'.jpg',image_crop)
                    # cv2.imwrite(crops_folder+filename+'.jpg',image_crop)

                for index,image_crop in enumerate(sorted_rotated_image_crop_list):
                    image_crop=cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB)
                    crop_rotate_image_path=crops_folder+filename+'/'+filename+'_'+str(index)+'_rotated.jpg'
                    crop_image_path_str_temp+=(crop_rotate_image_path)+','
                    cv2.imwrite(crop_rotate_image_path,image_crop)
                    
                if len(crop_image_path_str_temp)>0:
                    crop_image_path_str+=str(crop_image_path_str_temp)+'&&'
                file_utils.saveResult(image_path, image[:,:,::-1], polys, dirname=result_folder)
            
            row_data['craft_crop_paths']=crop_image_path_str[:-2]
            row_data['craft']='Done'
            # break


            
        except Exception as e:
            row_data['craft']='Failed'
            final_list.append(row_data)
            
            print('Error Found : ',row_data['Image_Path'])
            print(e)
    pd.DataFrame(final_list).to_excel('../data/csvs/'+'ANPR_Analysis_1.xlsx',index=False)
        
    print("elapsed time : {}s".format(time.time() - t))


class craft():
    def __init__(self) -> None:

        self.net = CRAFT()     # initialize
        self.reg_crop_images_obj=rearrange_crop_images()
        # print('Loading weights from checkpoint (' + args.trained_model + ')')
        if args.cuda:
            self.net.load_state_dict(copyStateDict(torch.load(args.trained_model)))
            # net.load_state_dict(torch.load(args.trained_model))
            print('Craft Weights Loaded On GPU')
            
        else:
            self.net.load_state_dict(copyStateDict(torch.load(args.trained_model, map_location='cpu')))
            print('Craft Weights Loaded On CPU')

        if args.cuda:
            self.net = self.net.cuda()
            self.net = torch.nn.DataParallel(self.net)
            cudnn.benchmark = False

        self.net.eval()

        # # LinkRefiner
        refine_net = None
        if args.refine:
            from refinenet import RefineNet
            self.refine_net = RefineNet()
            # print('Loading weights of refiner from checkpoint (' + args.refiner_model + ')')
            # print('args.cuda : ',args.cuda)
            if args.cuda:
                self.refine_net.load_state_dict(copyStateDict(torch.load(args.refiner_model)))
                self.refine_net = self.refine_net.cuda()
                self.refine_net = torch.nn.DataParallel(self.refine_net)
                print('refine_net Loaded On GPU....')
            else:
                self.refine_net.load_state_dict(copyStateDict(torch.load(args.refiner_model, map_location='cpu')))
                print('refine_net Loaded On CPU....')

            self.refine_net.eval()
            args.poly = True



    def craft_main(self,number_plate_crop_lst=[]):
        data={
            'Status':1,# Error 1 Done 0
            'Error':'init craft_main error',# Error 1 Done 0
            'Sorted_Rotated_Image_Crop_List':[],# 
            'Image_Crop_List_Found':False,# Return True,False
        }


        try:
            if len(number_plate_crop_lst)==0:
                data['Status']=0
                data['Error']='No Number plates Found'
                return data
            for image in number_plate_crop_lst:
                try:
                    w,h,_=image.shape
                    bboxes, polys, score_text = test_net(self.net, image, args.text_threshold, args.link_threshold, args.low_text, args.cuda, args.poly, self.refine_net)
                    #print('bboxes : ',bboxes)
                    # print('polys : ',polys)
                    if len(polys)==0:
                        polys=bboxes
                        # continue
                    processed_polys=self.reg_crop_images_obj.preprocess(polys,w*h)
                    renew_polys_dict=self.reg_crop_images_obj.rearrange(processed_polys)
                    sorted_image_crop_list,sorted_rotated_image_crop_list=self.reg_crop_images_obj.crop_poly(image,renew_polys_dict)
                    
                    data['Status']=0
                    data['Error']=0
                    if len(sorted_rotated_image_crop_list)>0:
                        data['Sorted_Rotated_Image_Crop_List'].append(sorted_rotated_image_crop_list)
                except Exception as e:
                    data['Status']=1
                    data['Error']=e
                    continue
    
            if len(data['Sorted_Rotated_Image_Crop_List'])>0:
                data['Image_Crop_List_Found']=True
            return data 
        except Exception as e:
            data['Status']=1
            data['Error']=e
            return data 
       

# crop_numberplate_path='/home/aikernel/output/IND0003241020240100084/processed/NumberPlate_Crop_0.png'''
# dest_folder='/home/aikernel/output/IND0003241020240100084/processed/'


# img.shape :  (49, 89, 3)

# img=cv2.imread(crop_numberplate_path)
# print("img.shape : ",img.shape)
# output=craft().craft_main([img])
# print('Status : ',output['Status'])
# print('Error : ',output['Error'])
# print('Sorted_Rotated_Image_Crop_List : ',len(output['Sorted_Rotated_Image_Crop_List']))
# print('Status : ',output['Image_Crop_List_Found'])
# for index,crop_list in enumerate(output['Sorted_Rotated_Image_Crop_List']):
#     # print("type(crop) : ",type(crop))
#     for j,crop in enumerate(crop_list):
#         dest_img_path=dest_folder+str(index)+'_'+str(j)+'.png'
#         print("dest_img_path : ",dest_img_path)
#         cv2.imwrite(dest_img_path,crop)


# data={
#             'Status':1,# Error 1 Done 0
#             'Error':'init craft_main error',# Error 1 Done 0
#             'Sorted_Rotated_Image_Crop_List':[],# 
#             'Image_Crop_List_Found':False,# Return True,False
#         }


# obj=craft().craft_main()
