import cv2
import numpy as np
import torch
import os
os.environ["CUDA_VISIBLE_DEVICES"]="0"
import random
import time
import torchvision
from PIL import Image
from pathlib import Path
import time
from shapely.geometry import Point, Polygon
from configs.config import anpr_image_size,mining_vehicle_list,root_path,top_image_size,\
    Filter_Plate_To_Selected_Vehicle,Plate_Vehicle_Assoc_Pad_Frac
import logging
from glob import glob
from custom_utils.save_json import save_json
logger = logging.getLogger(__name__)


source_path=root_path+'metadata/'
# Set printoptions
torch.set_printoptions(linewidth=320, precision=5, profile='long')
np.set_printoptions(linewidth=320, formatter={'float_kind': '{:11.5g}'.format})  # format short g, %precision=5


# Prevent OpenCV from multithreading (to use PyTorch DataLoader)
cv2.setNumThreads(0)

NP_class_names=['number_plate','truck','mini_truck','hywa','tractor','bus','car','other','unclassified','covered','mining_empty','mining_full','miss_triggered','non_mining','two_wheeler']
Top_class_names=['number_plate','truck','mini_truck','hywa','tractor','bus','car','other','unclassified','covered','mining_empty','mining_full','miss_triggered','non_mining','two_wheeler','bonnet','covered_mining_full']


cuda_available=torch.cuda.is_available()#False#

def xyxy2xywh(x):
    # Convert nx4 boxes from [x1, y1, x2, y2] to [x, y, w, h] where xy1=top-left, xy2=bottom-right
    y = torch.zeros_like(x) if isinstance(x, torch.Tensor) else np.zeros_like(x)
    y[:, 0] = (x[:, 0] + x[:, 2]) / 2  # x center
    y[:, 1] = (x[:, 1] + x[:, 3]) / 2  # y center
    y[:, 2] = x[:, 2] - x[:, 0]  # width
    y[:, 3] = x[:, 3] - x[:, 1]  # height
    return y


def xywh2xyxy(x):
    # Convert nx4 boxes from [x, y, w, h] to [x1, y1, x2, y2] where xy1=top-left, xy2=bottom-right
    y = torch.zeros_like(x) if isinstance(x, torch.Tensor) else np.zeros_like(x)
    y[:, 0] = x[:, 0] - x[:, 2] / 2  # top left x
    y[:, 1] = x[:, 1] - x[:, 3] / 2  # top left y
    y[:, 2] = x[:, 0] + x[:, 2] / 2  # bottom right x
    y[:, 3] = x[:, 1] + x[:, 3] / 2  # bottom right y
    return y
def clip_boxes(boxes, shape):
    # Clip boxes (xyxy) to image shape (height, width)
    if isinstance(boxes, torch.Tensor):  # faster individually
        boxes[..., 0].clamp_(0, shape[1])  # x1
        boxes[..., 1].clamp_(0, shape[0])  # y1
        boxes[..., 2].clamp_(0, shape[1])  # x2
        boxes[..., 3].clamp_(0, shape[0])  # y2
    else:  # np.array (faster grouped)
        boxes[..., [0, 2]] = boxes[..., [0, 2]].clip(0, shape[1])  # x1, x2
        boxes[..., [1, 3]] = boxes[..., [1, 3]].clip(0, shape[0])  # y1, y2

def crop_number_plate(xyxy,image,gain=1.02,BGR=False,pad=10):

    xyxy = torch.tensor(xyxy).view(-1, 4)
    b = xyxy2xywh(xyxy)  # boxes
    b[:, 2:] = b[:, 2:] * gain + pad  # box wh * gain + pad
    xyxy = xywh2xyxy(b).long()
    clip_boxes(xyxy, image.shape)
    crop = image[int(xyxy[0, 1]):int(xyxy[0, 3]), int(xyxy[0, 0]):int(xyxy[0, 2]), ::(1 if BGR else -1)]
    return crop

# def crop_number_plate_context(xyxy, image, gain=2.4, pad=140, BGR=False):
#     """Same bbox as tight plate crop, but larger gain/pad for bumper/bonnet context (BigNumberPlate_* on disk)."""
#     xyxy = torch.tensor(xyxy).view(-1, 4)
#     b = xyxy2xywh(xyxy)
#     b[:, 2:] = b[:, 2:] * gain + pad
#     xyxy = xywh2xyxy(b).long()
#     clip_boxes(xyxy, image.shape)
#     crop = image[int(xyxy[0, 1]):int(xyxy[0, 3]), int(xyxy[0, 0]):int(xyxy[0, 2]), ::(1 if BGR else -1)]
#     return crop

def crop_number_plate_context(xyxy, image, BGR=False,
        pad_left_frac=2.5, pad_right_frac=2.5,
        pad_top_frac=5, pad_bottom_frac=0.4,
        min_pad_px=100):
    """Wide crop: extra top (bonnet) and sides; less below plate."""
    x1, y1, x2, y2 = [float(v) for v in xyxy]
    w, h = max(x2 - x1, 1), max(y2 - y1, 1)

    x1 = max(0, x1 - max(w * pad_left_frac, min_pad_px))
    x2 = min(image.shape[1], x2 + max(w * pad_right_frac, min_pad_px))
    y1 = max(0, y1 - max(h * pad_top_frac, min_pad_px))      # bonnet
    y2 = min(image.shape[0], y2 + max(h * pad_bottom_frac, min_pad_px * 0.5))

    crop = image[int(y1):int(y2), int(x1):int(x2), ::(1 if BGR else -1)]
    return crop


def plate_belongs_to_vehicle(plate_xyxy, vehicle_xyxy, pad_frac=0.20):
    """
    True if plate center lies inside an expanded vehicle box
    (extra pad below for low bumper plates).
    plate_xyxy / vehicle_xyxy: [x1,y1,x2,y2]
    """
    try:
        vx1, vy1, vx2, vy2 = [float(v) for v in vehicle_xyxy[:4]]
        px1, py1, px2, py2 = [float(v) for v in plate_xyxy[:4]]
    except Exception:
        return False
    vw = max(vx2 - vx1, 1.0)
    vh = max(vy2 - vy1, 1.0)
    # Expand: equal sides/top, more below (bumper / low plate)
    vx1_e = vx1 - vw * pad_frac
    vx2_e = vx2 + vw * pad_frac
    vy1_e = vy1 - vh * pad_frac * 0.5
    vy2_e = vy2 + vh * pad_frac * 1.5
    pcx = (px1 + px2) * 0.5
    pcy = (py1 + py2) * 0.5
    return vx1_e <= pcx <= vx2_e and vy1_e <= pcy <= vy2_e


def filter_plates_for_vehicle(plate_crops, plate_big_crops, plate_points, vehicle_xyxy,
                              pad_frac=0.20):
    """Keep only plate crops whose bbox belongs to the selected vehicle."""
    if vehicle_xyxy is None:
        return [], [], []
    kept_crops, kept_big, kept_pts = [], [], []
    for crop, big, pts in zip(plate_crops, plate_big_crops, plate_points):
        if plate_belongs_to_vehicle(pts, vehicle_xyxy, pad_frac=pad_frac):
            kept_crops.append(crop)
            kept_big.append(big)
            kept_pts.append(pts)
    return kept_crops, kept_big, kept_pts


def save_one_box(xyxy, im, file_path='im.jpg', gain=1.02, pad=10, BGR=False, save=True):
    # Save image crop as {file} with crop size multiple {gain} and {pad} pixels. Save and/or return crop
    xyxy = torch.tensor(xyxy).view(-1, 4)
    b = xyxy2xywh(xyxy)  # boxes
    b[:, 2:] = b[:, 2:] * gain + pad  # box wh * gain + pad
    xyxy = xywh2xyxy(b).long()
    clip_boxes(xyxy, im.shape)
    crop = im[int(xyxy[0, 1]):int(xyxy[0, 3]), int(xyxy[0, 0]):int(xyxy[0, 2]), ::(1 if BGR else -1)]
    count=0
    if save:
        while True:
            if os.path.exists(file_path):
                count+=1
                if count==1:
                    file_path=file_path.replace('.jpg','_'+str(count)+'.jpg')
                else:
                    file_path=file_path.replace('_'+str(count-1)+'.jpg','_'+str(count)+'.jpg')
                print('updated file_path : ',file_path)
            else:
                break

        Image.fromarray(crop[..., ::-1]).save(file_path, quality=95, subsampling=0)  # save RGB


    return crop,file_path


def scale_coords(img1_shape, coords, img0_shape, ratio_pad=None):
    # Rescale coords (xyxy) from img1_shape to img0_shape
    if ratio_pad is None:  # calculate from img0_shape
        gain = max(img1_shape) / max(img0_shape)  # gain  = old / new
        pad = (img1_shape[1] - img0_shape[1] * gain) / 2, (img1_shape[0] - img0_shape[0] * gain) / 2  # wh padding
    else:
        gain = ratio_pad[0][0]
        pad = ratio_pad[1]

    coords[:, [0, 2]] -= pad[0]  # x padding
    coords[:, [1, 3]] -= pad[1]  # y padding
    coords[:, :4] /= gain
    clip_coords(coords, img0_shape)
    return coords


def clip_coords(boxes, img_shape):
    # Clip bounding xyxy bounding boxes to image shape (height, width)
    boxes[:, 0].clamp_(0, img_shape[1])  # x1
    boxes[:, 1].clamp_(0, img_shape[0])  # y1
    boxes[:, 2].clamp_(0, img_shape[1])  # x2
    boxes[:, 3].clamp_(0, img_shape[0])  # y2


def plot_one_box(x, img, color=None, label=None, line_thickness=None):
    # Plots one bounding box on image img
    tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1  # line/font thickness
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1]+100 - t_size[1] - 3
        cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  # filled
        cv2.putText(img, label, (c1[0], c1[1]+50), 0, tl / 3, [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)

def plot_one_box_top_front(x, img, color=None, label=None, line_thickness=None):
    # Plots one bounding box on image img
    tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1  # line/font thickness
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1]+100 - t_size[1] - 3
        cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  # filled
        cv2.putText(img, label, (c1[0], c1[1]+50), 0, tl / 3, [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)
def point_in_polygon(point, polygon_points):
    # Create a Shapely Point object from the given point coordinates
    p = Point(point)
    
    # Create a Shapely Polygon object from the list of polygon points
    poly = Polygon(polygon_points)
    
    # Check if the point is inside the polygon
    if p.within(poly):
        return True#"Point is inside the polygon"
    else:
        return False#"Point is outside the polygon"
    

def non_max_suppression(prediction, conf_thres=0.1, iou_thres=0.6, fast=False, classes=None, agnostic=False):
    """
    Performs  Non-Maximum Suppression on inference results
    Returns detections with shape:
        nx6 (x1, y1, x2, y2, conf, cls)
    """
    nc = prediction[0].shape[1] - 5  # number of classes
    xc = prediction[..., 4] > conf_thres  # candidates

    # Settings
    min_wh, max_wh = 2, 4096  # (pixels) minimum and maximum box width and height
    max_det = 300  # maximum number of detections per image
    time_limit = 10.0  # seconds to quit after
    redundant = True  # require redundant detections
    fast |= conf_thres > 0.001  # fast mode
    if fast:
        merge = False
        multi_label = False
    else:
        merge = True  # merge for best mAP (adds 0.5ms/img)
        multi_label = nc > 1  # multiple labels per box (adds 0.5ms/img)

    t = time.time()
    output = [None] * prediction.shape[0]
    for xi, x in enumerate(prediction):  # image index, image inference
        # Apply constraints
        #x[((x[..., 2:4] < min_wh) | (x[..., 2:4] > max_wh)).any(1), 4] = 0  # width-height
        x = x[xc[xi]]  # confidence

        # If none remain process next image
        if not x.shape[0]:
            continue

        # Compute conf
        x[:, 5:] *= x[:, 4:5]  # conf = obj_conf * cls_conf

        # Box (center x, center y, width, height) to (x1, y1, x2, y2)
        box = xywh2xyxy(x[:, :4])

        # Detections matrix nx6 (xyxy, conf, cls)
        if multi_label:
            i, j = (x[:, 5:] > conf_thres).nonzero().t()
            x = torch.cat((box[i], x[i, j + 5, None], j[:, None].float()), 1)
        else:  # best class only
        
            conf, j = x[:, 5:].max(1, keepdim=True)
            x = torch.cat((box, conf, j.float()), 1)[conf.view(-1) > conf_thres]

        # Filter by class
        if classes:
            x = x[(x[:, 5:6] == torch.tensor(classes, device=x.device)).any(1)]
            
        # If none remain process next image
        n = x.shape[0]  # number of boxes
        if not n:
            continue

        # Batched NMS
        c = x[:, 5:6] * (0 if agnostic else max_wh)  # classes
        boxes, scores = x[:, :4] + c, x[:, 4]  # boxes (offset by class), scores
        i = torchvision.ops.boxes.nms(boxes, scores, iou_thres)
        if i.shape[0] > max_det:  # limit detections
            i = i[:max_det]
        if merge and (1 < n < 3E3):  # Merge NMS (boxes merged using weighted mean)
            try:  # update boxes as boxes(i,4) = weights(i,n) * boxes(n,4)
                iou = box_iou(boxes[i], boxes) > iou_thres  # iou matrix
                weights = iou * scores[None]  # box weights
                x[i, :4] = torch.mm(weights, x[:, :4]).float() / weights.sum(1, keepdim=True)  # merged boxes
                if redundant:
                    i = i[iou.sum(1) > 1]  # require redundancy
            except:  # possible CUDA error https://github.com/ultralytics/yolov3/issues/1139
                print(x, i, x.shape, i.shape)
                pass

        output[xi] = x[i]
        if (time.time() - t) > time_limit:
            break  # time limit exceeded

    return output


def letterbox(img, new_shape=(416, 416), color=(114, 114, 114), auto=True, scaleFill=False, scaleup=True):
    # Resize image to a 32-pixel-multiple rectangle https://github.com/ultralytics/yolov3/issues/232
    shape = img.shape[:2]  # current shape [height, width]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:  # only scale down, do not scale up (for better test mAP)
        r = min(r, 1.0)

    # Compute padding
    ratio = r, r  # width, height ratios
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding
    if auto:  # minimum rectangle
        dw, dh = np.mod(dw, 64), np.mod(dh, 64)  # wh padding
    elif scaleFill:  # stretch
        dw, dh = 0.0, 0.0
        new_unpad = new_shape
        ratio = new_shape[0] / shape[1], new_shape[1] / shape[0]  # width, height ratios

    dw /= 2  # divide padding into 2 sides
    dh /= 2

    if shape[::-1] != new_unpad:  # resize
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  # add border
    return img, ratio, (dw, dh)

count=0
data=[]
def count_obj(id):#box,w,h,
    global count,data
    if id not in data: 
        count+=1
        
        data.append(id)
        # print('count,data : ',count,data)



class yolo_pred():
    def __init__(self,height=None,width=None,draw_lines=True,lane_id=None,image_type='ANPR',roi_info=None):

        #self.top_cls_names=['Covered','Mining_Empty','Mining_Full','Miss_Triggered','Non_Mining','not_found']
        #self.NP_class_names=['number_plate','truck','mini_truck','hywa','tractor','bus','car','other','unclassified','covered','mining_empty','mining_full','miss_triggered','non_mining','two_wheeler']
        self.cross_lane_class_names=['mining_vehicle','unclassified','other','tyers']

        self.front_mining_cls_index_list=[1,2,3,4]#[1,2,3,4,5,6]#
        self.top_mining_cls_index_list=[9,10,11,12,13]
        
        
        # self.front_cls_colors=[[255,0,0],[0,255,0],[0,255,0],[255,0,0],[0,255,0],[0,255,0],[0,255,0],[0,255,0]]
        self.front_cls_colors=[[255,0,0],[255,0,0],[255,0,0],[255,0,0],[255,0,0],[255,0,0],[255,0,0],[255,0,0]]
        

        # weights_number_plate_detection='./weights/v1_number_plate_detection_yolov5small_best.pt'
        # weights_number_plate_detection='./weights/MP_Front_NP_small640_04112023.pt'
        # weights_number_plate_detection='./weights/MP_Feb15_YoloNano640_best.pt'
        # weights_number_plate_detection= './weights/MP_Feb20_YoloNano640_NumberPlate_FrontTop_best.pt'
        # weights_number_plate_detection = './weights/MP_Feb21_NumberPlate_FrontTop_best.pt'
        # weights_number_plate_detection = './weights/MP_March9_NumberPlate_FrontTop_best.pt'
        # weights_number_plate_detection = './weights/MP_March14_NumberPlate_FrontTop_best.pt'
        # weights_number_plate_detection = './weights/MP_March16_NumberPlate_FrontTop_best.pt'
        # weights_number_plate_detection = './weights/MP_March22_NumberPlate_FrontTop_best.pt'
        # weights_number_plate_detection = '/weights/MP_March31_NumberPlate_FrontTop_best.pt'
        # weights_number_plate_detection = '/weights/MP_May12_NumberPlate_FrontTop_best.pt'
        # weights_number_plate_detection = '/weights/MP_May27_NumberPlate_FrontTop_best.pt'
        # weights_number_plate_detection = '/weights/MP_July30_NumberPlate_FrontTop_best.pt'
        # weights_number_plate_detection = '/weights/MP_NumberPlate_FrontTop_25082024_mixed_data_best.pt'
        # weights_number_plate_detection = '/weights/MP_NumberPlate_FrontTop_17102024_mixed_data_best.pt'
        weights_number_plate_detection =glob(source_path+'/weights/MP_NumberPlate_FrontTop_**')[0]
        save_json(source_path+'/loaded_model/','ANPR_Vehicle_Number_Plate_Detection.json',{'model':weights_number_plate_detection})
        

        # weights_Top_detection = '/weights/Top_14062024best.pt'
        # weights_Top_detection = '/weights/Top_15062024best.pt'
        # weights_Top_detection = '/weights/Top_21062024best.pt'
        # weights_Top_detection = '/weights/Top_15092024_best.pt'
        # weights_Top_detection = '/weights/Top_23092024best.pt'
        # weights_Top_detection = '/weights/Top_25092024.pt'
        # weights_Top_detection = '/weights/Top_11102024.pt'
        # weights_Top_detection = '/weights/Top_19102024.pt'
        # weights_Top_detection = '/weights/Top_23112024.pt'
        # weights_Top_detection = '/weights/Covered_mining_full_11122024.pt'
        # weights_Top_detection = '/weights/Covered_mining_full_02012026.pt'
        # weights_Top_detection = '/weights/Covered_mining_full_21022026.pt'
        weights_Top_detection =glob(source_path+'/weights/Covered_mining_full_**')[0]
        save_json(source_path+'/loaded_model/','Top_Detection.json',{'model':weights_Top_detection})
        
        
        
        # weights_Cross_Lane_detection = './weights/crosslane_object_detection_top_22082024.pt'
        weights_Cross_Lane_detection =glob(source_path+'/weights/crosslane_object_detection_top_**')[0]
        save_json(source_path+'/loaded_model/','Cross_Lane_Top_Detection.json',{'model':weights_Cross_Lane_detection})
        
        if cuda_available and image_type=='ANPR':
            
            self.yolo_NB_detection_model = torch.load(weights_number_plate_detection,weights_only=False)['model'].cuda()
            self.yolo_NB_detection_model.eval()
            print('NB_detection Model Loaded On GPU....')
            logger.info('weights_number_plate_detection GPU: '+weights_number_plate_detection)
        elif cuda_available==False and image_type=='ANPR':
            self.yolo_NB_detection_model = torch.load(weights_number_plate_detection,map_location='cpu',weights_only=False)['model']
            self.yolo_NB_detection_model.float().eval()
            print('NB_detection Model Loaded On CPU....')
            logger.info('weights_number_plate_detection CPU: '+weights_number_plate_detection)
        if cuda_available and image_type=='TOP':
            self.yolo_top_detection_model = torch.load(weights_Top_detection,weights_only=False)['model'].cuda()
            self.yolo_top_detection_model.eval()
            print('yolo_top_detection_model Model Loaded On GPU....') 
            logger.info('weights_Top_detection GPU: '+weights_Top_detection)
        elif cuda_available==False and image_type=='TOP':
            self.yolo_top_detection_model = torch.load(weights_Top_detection,map_location='cpu',weights_only=False)['model']
            self.yolo_top_detection_model.float().eval()
            print('yolo_top_detection_model Model Loaded On CPU....')
            logger.info('weights_Top_detection GPU: '+weights_Top_detection)
        
        if cuda_available and image_type=='CROSS':
            self.yolo_top_cross_detection_model = torch.load(weights_Cross_Lane_detection,weights_only=False)['model'].cuda()
            self.yolo_top_cross_detection_model.eval()
            print('yolo_top_detection_model Model Loaded On GPU....') 
        elif cuda_available==False and image_type=='CROSS':
            self.yolo_top_cross_detection_model = torch.load(weights_Cross_Lane_detection,map_location='cpu',weights_only=False)['model']
            self.yolo_top_cross_detection_model.float().eval()
            print('yolo_top_detection_model Model Loaded On CPU....')
        




        


        self.conf_thresh_anpr = 0.4#0.8
        self.iou_thresh_anpr = 0.4#0.8
        self.top_model_confidance_thrshold=0.6
        self.top_model_iou_threshold = 0.6#0.8
        

        # self.conf_thresh_top = 0.2
        # self.iou_thresh_top = 0.2

        self.agnostic = 'store_true'
        self.classes = None
        self.agnostic_nms = 'store_true'
        self.img_size = 640

        # width,height= 2688,1520
        # width,height= anpr_image_size
        # print('width,height : ',width,height)
        
        self.draw_lines=draw_lines


        

        # Lane 1/ lane_3.py
        if image_type=='ANPR' and roi_info==None:
            width,height= anpr_image_size
            print('width,height : ',width,height)
            
            if lane_id==3 or lane_id==1:

                # New Camera Setup Obaidullaganj
                self.point_on_line_1 = (int(width*.25), int(height*.10)) #[537  , 0]
                self.point_on_line_2 = (int(width*.60), int(height*.10))
                self.point_on_line_3 = (int(width*.80), int(height*.85))#[2688 , 1520]
                self.point_on_line_4 = (int(width*.25), int(height*.9))#[ 940, 1520]
                self.top_point_on_line_1 = (int(width*.32), .20) #[537  , 0]
                self.top_point_on_line_2 = (int(width*.604166667), .20)
                
                self.new_transaction_threshold=int(height*.40)
                self.capture_numberplate_heavy_vehicles=int(height*.40)
                self.top_capture_yaxis_mining = ( int(height*.40)) # with center
                

            elif lane_id==2 or lane_id==4:
                # width,height= top_image_size
                # print('width,height : ',width,height)
                # self.point_on_line_1 = (int(width*.39), int(height*.1)) #[537  , 0]
                # self.point_on_line_2 = (int(width*.627604167), int(height*.1)) #[1344 ,   0] 0.604166667, 0.186111111
                # self.point_on_line_3 = (int(width*.6859375), int(height*.9))#[2688 , 1520]
                # self.point_on_line_4 = (int(width*.29), int(height*.9))#[ 940, 1520]

                # # Videos 
                # # self.point_on_line_1 = (int(width*.472916667), int(height*.1)) #[537  , 0]
                # self.point_on_line_1 = (int(width*.25), int(height*.05)) #[537  , 0]
                # self.point_on_line_2 = (int(width*.60), int(height*.05)) #[1344 ,   0] 0.604166667, 0.186111111
                # self.point_on_line_3 = (int(width*.67), int(height*.9))#[2688 , 1520]
                # self.point_on_line_4 = (int(width*.15), int(height*.9))#[ 940, 1520]

                # # Same as point one with max height
                # self.top_point_on_line_1 = (int(width*.25), 0) #[537  , 0] 
                # self.top_point_on_line_2 = (int(width*.60), 0)

                # self.top_capture_yaxis_mining = ( int(height*.85)) # with right bottom 
                
                self.point_on_line_1 = (int(width*.36), int(height*.10)) #[537  , 0]
                self.point_on_line_2 = (int(width*.65), int(height*.10)) #[1344 ,   0] 0.604166667, 0.186111111
                self.point_on_line_3 = (int(width*.75), int(height*.9))#[2688 , 1520]
                self.point_on_line_4 = (int(width*.26), int(height*.9))#[ 940, 1520]

                self.top_point_on_line_1 = (int(width*.472916667), 0) #[537  , 0]
                self.top_point_on_line_2 = (int(width*.647916667), 0)

                
                self.top_capture_yaxis_mining = ( int(height*.40)) # with center 

                self.capture_numberplate_heavy_vehicles=int(height*.40)

                # if vehicle is more then 25% in image (height or y) start transaction
                self.new_transaction_threshold=int(height*.25)
            
            self.poly_list=[self.point_on_line_1 ,self.point_on_line_2,self.point_on_line_3,self.point_on_line_4]
            self.top_poly_list=[self.top_point_on_line_1 ,self.top_point_on_line_2,self.point_on_line_3,self.point_on_line_4]

        elif image_type=='TOP' and roi_info==None:
            width,height= top_image_size#(w,h)

            print('width,height : ',width,height)
            

            # 2592 × 1944  Lane 1
            self.point_on_line_1_1 = (int(width*.42), int(height*0.25)) #height 26%->10%
            self.point_on_line_1_2 = (int(width*.61), int(height*.25)) #height 26%->10% width 63->53
            self.point_on_line_1_3 = (int(width*.81), int(height*0.89))#[2688 , 1520]
            self.point_on_line_1_4 = (int(width*.32), int(height*0.89))#[ 940, 1520

            self.top_point_on_line_1_1 = (int(width*.401), int(height*0.15))#[2688 , 1520]
            self.top_point_on_line_1_2 = (int(width*0.61), int(height*0.15))#[ 940, 1520]

            # Ideal for inferance using top camera 
            # Capture top for model training 56% to 30%
            # self.top_capture_yaxis_mining = ( int(height*.4)) # with center
            # self.capture_numberplate_heavy_vehicles=int(height*.4)

                

            # if lane_id==2 or lane_id==4:
                # 2592 × 1944  Lane 1
            self.point_on_line_2_1 = (int(width*.4), int(height*0.25)) ##height 26%->10% width 42->46
            self.point_on_line_2_2 = (int(width*.64), int(height*0.25)) #height 26%->10%
            self.point_on_line_2_3 = (int(width*.79), int(height*0.89))#[2688 , 1520]
            self.point_on_line_2_4 = (int(width*.29), int(height*0.89))#[ 940, 1520

            self.top_point_on_line_2_1 = (int(width*.40), int(height*0.15))#[2688 , 1520]
            self.top_point_on_line_2_2 = (int(width*0.64), int(height*0.15))#[ 940, 1520]
            # Ideal for inferance using top camera 
            # Capture top for model training 56% to 30%

        
        
            self.front_poly_list_1_3=[self.point_on_line_1_1 ,self.point_on_line_1_2,self.point_on_line_1_3,self.point_on_line_1_4]
            self.top_poly_list_1_3=[self.top_point_on_line_1_1 ,self.top_point_on_line_1_2,self.point_on_line_1_3,self.point_on_line_1_4]

            self.poly_list_2_4=[self.point_on_line_2_1 ,self.point_on_line_2_2,self.point_on_line_2_3,self.point_on_line_2_4]
            self.top_poly_list_2_4=[self.top_point_on_line_2_1 ,self.top_point_on_line_2_2,self.point_on_line_2_3,self.point_on_line_2_4]

        elif image_type=='TOP' and roi_info!=None:
            width,height= top_image_size#(w,h)

            print('width,height : ',width,height)

            # print('roi_info : ',roi_info)
            if 'Top_1' in roi_info:
                self.point_on_line_1_1 = (int(width*roi_info['Top_1']['roi_info']['1']['xRatio']), int(height*roi_info['Top_1']['roi_info']['1']['yRatio'])) #[537  , 0]
                self.point_on_line_1_2 = (int(width*roi_info['Top_1']['roi_info']['2']['xRatio']), int(height*roi_info['Top_1']['roi_info']['2']['yRatio']))
                self.point_on_line_1_3 = (int(width*roi_info['Top_1']['roi_info']['3']['xRatio']), int(height*roi_info['Top_1']['roi_info']['3']['yRatio']))#[2688 , 1520]
                self.point_on_line_1_4 = (int(width*roi_info['Top_1']['roi_info']['4']['xRatio']), int(height*roi_info['Top_1']['roi_info']['4']['yRatio']))#[ 940, 1520]
                
                self.top_point_on_line_1_1 = (int(width*roi_info['Top_1']['roi_info']['1']['xRatio']), int(height*0.10))#[2688 , 1520]
                self.top_point_on_line_1_2 = (int(width*roi_info['Top_1']['roi_info']['2']['xRatio']), int(height*0.10))#[ 940, 1520]

                self.front_poly_list_1=[self.point_on_line_1_1 ,self.point_on_line_1_2,self.point_on_line_1_3,self.point_on_line_1_4]
                self.top_poly_list_1=[self.top_point_on_line_1_1 ,self.top_point_on_line_1_2,self.point_on_line_1_3,self.point_on_line_1_4]

            if 'Top_2' in roi_info:
                self.point_on_line_2_1 = (int(width*roi_info['Top_2']['roi_info']['1']['xRatio']), int(height*roi_info['Top_2']['roi_info']['1']['yRatio'])) #[537  , 0]
                self.point_on_line_2_2 = (int(width*roi_info['Top_2']['roi_info']['2']['xRatio']), int(height*roi_info['Top_2']['roi_info']['2']['yRatio']))
                self.point_on_line_2_3 = (int(width*roi_info['Top_2']['roi_info']['3']['xRatio']), int(height*roi_info['Top_2']['roi_info']['3']['yRatio']))#[2688 , 1520]
                self.point_on_line_2_4 = (int(width*roi_info['Top_2']['roi_info']['4']['xRatio']), int(height*roi_info['Top_2']['roi_info']['4']['yRatio']))#[ 940, 1520]
                
                self.top_point_on_line_2_1 = (int(width*roi_info['Top_2']['roi_info']['1']['xRatio']), int(height*0.10))#[2688 , 1520]
                self.top_point_on_line_2_2 = (int(width*roi_info['Top_2']['roi_info']['2']['xRatio']), int(height*0.10))#[ 940, 1520]

                self.poly_list_2=[self.point_on_line_2_1 ,self.point_on_line_2_2,self.point_on_line_2_3,self.point_on_line_2_4]
                self.top_poly_list_2=[self.top_point_on_line_2_1 ,self.top_point_on_line_2_2,self.point_on_line_2_3,self.point_on_line_2_4]
            
            if 'Top_3' in roi_info:
                self.point_on_line_3_1 = (int(width*roi_info['Top_3']['roi_info']['1']['xRatio']), int(height*roi_info['Top_3']['roi_info']['1']['yRatio'])) #[537  , 0]
                self.point_on_line_3_2 = (int(width*roi_info['Top_3']['roi_info']['2']['xRatio']), int(height*roi_info['Top_3']['roi_info']['2']['yRatio']))
                self.point_on_line_3_3 = (int(width*roi_info['Top_3']['roi_info']['3']['xRatio']), int(height*roi_info['Top_3']['roi_info']['3']['yRatio']))#[2688 , 1520]
                self.point_on_line_3_4 = (int(width*roi_info['Top_3']['roi_info']['4']['xRatio']), int(height*roi_info['Top_3']['roi_info']['4']['yRatio']))#[ 940, 1520]
                
                self.top_point_on_line_3_1 = (int(width*roi_info['Top_3']['roi_info']['1']['xRatio']), int(height*0.10))#[2688 , 1520]
                self.top_point_on_line_3_2 = (int(width*roi_info['Top_3']['roi_info']['2']['xRatio']), int(height*0.10))#[ 940, 1520]

                self.poly_list_3=[self.point_on_line_3_1 ,self.point_on_line_3_2,self.point_on_line_3_3,self.point_on_line_3_4]
                self.top_poly_list_3=[self.top_point_on_line_3_1 ,self.top_point_on_line_3_2,self.point_on_line_3_3,self.point_on_line_3_4]

            if 'Top_4' in roi_info:
                self.point_on_line_4_1 = (int(width*roi_info['Top_4']['roi_info']['1']['xRatio']), int(height*roi_info['Top_4']['roi_info']['1']['yRatio'])) #[537  , 0]
                self.point_on_line_4_2 = (int(width*roi_info['Top_4']['roi_info']['2']['xRatio']), int(height*roi_info['Top_4']['roi_info']['2']['yRatio']))
                self.point_on_line_4_3 = (int(width*roi_info['Top_4']['roi_info']['3']['xRatio']), int(height*roi_info['Top_4']['roi_info']['3']['yRatio']))#[2688 , 1520]
                self.point_on_line_4_4 = (int(width*roi_info['Top_4']['roi_info']['4']['xRatio']), int(height*roi_info['Top_4']['roi_info']['4']['yRatio']))#[ 940, 1520]
                
                self.top_point_on_line_4_1 = (int(width*roi_info['Top_4']['roi_info']['1']['xRatio']), int(height*0.10))#[2688 , 1520]
                self.top_point_on_line_4_2 = (int(width*roi_info['Top_4']['roi_info']['2']['xRatio']), int(height*0.10))#[ 940, 1520]

                self.poly_list_4=[self.point_on_line_4_1 ,self.point_on_line_4_2,self.point_on_line_4_3,self.point_on_line_4_4]
                self.top_poly_list_4=[self.top_point_on_line_4_1 ,self.top_point_on_line_4_2,self.point_on_line_4_3,self.point_on_line_4_4]

        
        
            
            
        
        elif image_type=='ANPR' and roi_info!=None:
            print('=======================image_type==ANPR and roi_info!=None=========================')
            width,height= anpr_image_size
            print('width,height : ',width,height)
            self.point_on_line_1 = (int(width*roi_info['1']['xRatio']), int(height*roi_info['1']['yRatio'])) #[537  , 0]
            self.point_on_line_2 = (int(width*roi_info['2']['xRatio']), int(height*roi_info['2']['yRatio']))
            self.point_on_line_3 = (int(width*roi_info['3']['xRatio']), int(height*roi_info['3']['yRatio']))#[2688 , 1520]
            self.point_on_line_4 = (int(width*roi_info['4']['xRatio']), int(height*roi_info['4']['yRatio']))#[ 940, 1520]
            
            # self.top_point_on_line_1 = self.point_on_line_1#(int(width*.32), .20)
            # self.top_point_on_line_2 = self.point_on_line_2#(int(width*.604166667), .20)

            self.top_point_on_line_1 = (int(width*roi_info['1']['xRatio']),0)#(int(width*.32), .20)
            self.top_point_on_line_2 = (int(width*roi_info['2']['xRatio']),0)#(int(width*.604166667), .20)
            
            self.new_transaction_threshold=int(height*.40)
            self.capture_numberplate_heavy_vehicles=int(height*.40)
            self.top_capture_yaxis_mining = ( int(height*.40)) # with center
            self.poly_list=[self.point_on_line_1 ,self.point_on_line_2,self.point_on_line_3,self.point_on_line_4]
            self.top_poly_list=[self.top_point_on_line_1 ,self.top_point_on_line_2,self.point_on_line_3,self.point_on_line_4]

            print('self.poly_list : ',self.poly_list)
            print('self.top_poly_list : ',self.top_poly_list)
        elif image_type=='CROSS':
            print('=======================image_type==CROSS =========================')
            width,height= anpr_image_size
            self.top_capture_yaxis_mining = ( int(height*.50)) # with center
            
            






                
        print('YOLO Model Loaded Successfully......') 
        

        self.last_y_percent=0
        self.difference_y_percent=0
        self.vehicle_count=0
    
    def Top_main(self,image,lane_no,camera_side='left'):
        lane_no=int(lane_no)
        # print('Top Main lane_no: ',lane_no,type(lane_no))
        if lane_no==1:
            self.poly_list=self.front_poly_list_1
            self.top_poly_list=self.top_poly_list_1
        elif lane_no==2:
            self.poly_list=self.poly_list_2
            self.top_poly_list=self.top_poly_list_2
        elif lane_no==3:
            self.poly_list=self.poly_list_3
            self.top_poly_list=self.top_poly_list_3
        elif lane_no==4:
            self.poly_list=self.poly_list_4
            self.top_poly_list=self.top_poly_list_4
        
        
        data={  
            'Status':1,# Error 1 Done 0
            'Error':None,# Error 1 Done 0
            'Vehicle_Found':False,
            'Return_Disply_Frame':[],
            'Front_Class':'',
            'Front_IN_ROI':False,
            # 'Capture_Top':False,
            'Raw_Top_Category_List':[],
            'Top_IN_ROI':False,
            'Mining_Full_Crop_Found':False,
            'Raw_Mining_Full_Crop_List':[],
            'Bonnet_Crop_Found':False,
            'Bonnet_Crop_List':[],
            'Front_Valid_Image':False
        }
        # try:
        try:
            draw_img = image.copy()
        except Exception as e:
            data['Error']='Image not found Yolo: ',str(e)
            return data

        with torch.no_grad():
            
            
            
            # width=image.shape[1]
            # height=image.shape[0]
            height,width,_=image.shape
            img0 = image.copy()
            
            img = letterbox(img0, new_shape = self.img_size )[0]
            img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
            img = np.ascontiguousarray(img)
            img = torch.from_numpy(img)
            if cuda_available:
                img=img.cuda()
                img = img.half()
                self.yolo_top_detection_model.half()
            else:
                img = img.float()

            img /= 255.0  # 0 - 255 to 0.0 - 1.0
            if img.ndimension() == 3:
                img = img.unsqueeze(0)
            # Inference
            pred = self.yolo_top_detection_model(img)[0]
            pred = pred.float()
            # Apply NMS
            #pred = non_max_suppression(pred, self.conf_thresh_anpr, self.iou_thresh_anpr, fast=True, classes = self.classes, agnostic= self.agnostic_nms)
            pred = non_max_suppression(pred, self.top_model_confidance_thrshold, self.top_model_iou_threshold, fast=True, classes = self.classes, agnostic= self.agnostic_nms)
        

        object_conf=-1
        object_class=-1
        # print('pred : ',len(pred))
        center_point_y_front=-1
        center_point_y_top=-1
        
        for i, det in enumerate(pred):  # detections per image
            

            # print('------------------------------------------------------------------>',i)
            if det is not None and len(det):
                # print('det : ',det)

                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], img0.shape).round()
                
                ##########
                # Deep sort
                

                xywhs = xyxy2xywh(det[:, 0:4])
                #print('Deepsort 0')
                confs = det[:, 4]
                #print('Deepsort 1',confs)
                clss = det[:, 5]
                bottom_left_points=[]
                bounding_box_xywhs_list=[]
                object_conf_list=[]
                object_class_list=[]
                for index,clss_value in enumerate(clss.tolist()):
                    
                    xywhs_1=xywhs[index].cpu().unsqueeze(0)
                    confs_1=confs[index].cpu().unsqueeze(0)
                    clss_1=clss[index].cpu().unsqueeze(0)
                    x_min, y_min, x_max, y_max =det[index, :4]
                    bottom_left_points.append((x_min.item(), y_max.item()))
                    center_point_x,center_point_y=int(xywhs_1[0][0]),int(xywhs_1[0][1])

                    # out of ROI and not Number plate and exclude non mining categories
                    # Check Take all mining Vehicles and there tops are present in ROI

                    # print('Top_class_names[int(clss_value)] : ',Top_class_names[int(clss_value)],clss_value)
                    if (int(clss_value)>0 and (int(clss_value)<=8)):
                        # Ignore Non Mining Vehicles
                        if int(clss_value) not in self.front_mining_cls_index_list:
                                # print('Front not in self.front_mining_cls_index_list : =========>',Top_class_names[int(clss_value)],clss_value)
                                continue
                        # For Mining Vehicles Check ROI 
                        else:
                            # Ignore Mining Vehicle if its not in ROI 
                            if point_in_polygon((center_point_x,center_point_y),self.poly_list)==False:
                                # print('Front OUT ROI continue : =========>',Top_class_names[int(clss_value)],clss_value)
                                continue
                            else:
                                if center_point_y>=1000:
                                    data['Front_Valid_Image']=True
                                    center_point_y_front=center_point_y
                                    
                                else:
                                    center_point_y_front=center_point_y

                                bounding_box_xywhs = xywhs_1
                                object_conf=confs_1
                                object_class=clss_1

                                bounding_box_xywhs_list.append(xywhs_1[0])
                                object_conf_list.append(object_conf[0])
                                object_class_list.append(object_class[0])

                                # pass
                                # print('Front IN ROI continue : =========>',Top_class_names[int(clss_value)],clss_value)

                            # print('Front IN')

            


                    if ((int(clss_value)>0 and int(clss_value)<=8)) :
                        draw_img= cv2.circle(draw_img,(center_point_x,center_point_y), radius=0, color=[0,255,0], thickness=10)

                        data['Front_IN_ROI']=True
                        selected_label = '%s %.2f' % (Top_class_names[int(clss_value)],object_conf)
                        plot_one_box(det[index, :4], draw_img, color=[0,255,0],label=selected_label, line_thickness=4)
                        # print('Box Draw....')
                    
                        data['Vehicle_Found']=True
                        data['Front_Class']=Top_class_names[int(clss_value)]
                        
                        # # for ANPR Camera
                        # if int(clss_value) in self.front_mining_cls_index_list  and int(center_point_y)>= self.top_capture_yaxis_mining:# for front
                        #     data['Capture_Top']=True


                    
                    elif (int(clss_value)>8 and int(clss_value)<14) or int(clss_value)==16:
                        object_conf=confs_1
                        # center_point_x,center_point_y=int(xywhs_1[0][0]),int(xywhs_1[0][1])
                        
                        if point_in_polygon((center_point_x,center_point_y),self.top_poly_list):
                        #point_position_wrt_line((center_point_x,center_point_y),self.point_on_line_1,self.point_on_line_2,self.point_on_line_3,self.point_on_line_4):
                            # cv2.putText(draw_img, "Vehicle is in ROI", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            data['Top_IN_ROI']=True
                            data['Raw_Top_Category_List'].append(Top_class_names[int(clss_value)])
                            center_point_y_top=center_point_y

                                    

                            label ='%.1f %s' % (object_conf,Top_class_names[int(det[index, 5])])
                            plot_one_box(det[index, :4], draw_img, color=[0,127,255],label=label, line_thickness=4)
                            draw_img= cv2.circle(draw_img,(center_point_x,center_point_y), radius=0, color=[0,255,0], thickness=10)
                            
                            # Mining Full or Covered Mining Full 
                            if int(clss_value)==11:# or int(clss_value)==16
                                # print('clss_value : ',int(clss_value))
                                xyxy=det[index, 0:4]
                                xyxy=xyxy.cpu().numpy()
                                mining_full_crop=crop_number_plate(xyxy,image)
                                # print('mining_full_crop.shape : ',mining_full_crop.shape)
                                data['Mining_Full_Crop_Found']=True
                                data['Raw_Mining_Full_Crop_List'].append(mining_full_crop)
                                
                            

                    elif int(clss_value)>0:
                        label = '%.1f %s' % (confs_1,Top_class_names[int(det[index, 5])])
                        plot_one_box(det[index, :4], draw_img, color=[0,255,255],label=label, line_thickness=4)

                    if int(clss_value)==15: # Bonnet
                        # if lane_no==1 or lane_no==3:
                        #     poly_list=self.front_poly_list_1_3
                        # elif lane_no==2 or lane_no==4:
                        #     poly_list=self.poly_list_2_4
                        if point_in_polygon((center_point_x,center_point_y),self.poly_list):
                            # print('clss_value : ',int(clss_value))
                            xyxy=det[index, 0:4]
                            xyxy=xyxy.cpu().numpy()
                            mining_full_crop=crop_number_plate(xyxy,image)
                            # print('mining_full_crop.shape : ',mining_full_crop.shape)
                            data['Bonnet_Crop_Found']=True
                            data['Bonnet_Crop_List'].append(mining_full_crop)
                        else:
                            pass
                            # print('Bonnet Out of ROI : ',(center_point_x,center_point_y))
            
            


        if self.draw_lines:

            line_thickness = 2
            # print("Top Line :",self.top_poly_list[0], self.top_poly_list[1])
            cv2.line(draw_img, self.top_poly_list[0], self.top_poly_list[1], (0, 255, 255), thickness=line_thickness)

            
            pts = np.array(self.poly_list, np.int32)
            # Reshape the array into the required shape for fillPoly function
            pts = pts.reshape((-1, 1, 2))

            mask = np.zeros_like(draw_img)

            # Fill the area defined by the coordinates with a semi-transparent color (e.g., blue with 50% opacity)
            cv2.fillPoly(mask, [pts], (255, 0, 0, 128))  # 128 for 50% opacity in the fourth channel
            # cv2.fillPoly(mask, [pts_1], (255, 255, 255, 128)) 

            # Combine the mask with the original image
            draw_img = cv2.addWeighted(draw_img, 1, mask, 0.5, 0)
                
        
        if not data['Front_Class'] in Top_class_names[:5]:   
            data['Mining_Full_Crop_Found']=False
            data['Raw_Mining_Full_Crop_List']=[]
        if center_point_y_front<center_point_y_top:
            data['Raw_Top_Category_List']=[]
            # print('front : ',center_point_y_front ,'>',' top',center_point_y_top)
            
                            

        draw_img=cv2.resize(draw_img,(0,0),fx=0.5,fy=0.5)
        data['Status']=0           
        data['Return_Disply_Frame'].append(draw_img)




        return data
                    
                            


        # except Exception as e:
        #     print(e)
        #     data['Status']='Error in yolo main....'
        #     data['Error']=e
            
        # return data
    
    def Top_cross_lane(self,image):

        data={  
            'Status':1,# Error 1 Done 0
            'Error':None,# Error 1 Done 0
            'Return_Disply_Frame':[],
            'Vehicle_IN_ROI':None,
            'Vehicle_Crop_Found':False,
            'Vehicle_Crop':[],
            'Axel_count':0,
            'distance_in_pixels':0
        }
        # try:
        try:
            draw_img = image.copy()
        except Exception as e:
            data['Error']='Image not found Yolo: ',str(e)
            return data

        with torch.no_grad():
            
            
            
            # width=image.shape[1]
            # height=image.shape[0]
            height,width,_=image.shape
            img0 = image.copy()
            
            img = letterbox(img0, new_shape = self.img_size )[0]
            img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
            img = np.ascontiguousarray(img)
            img = torch.from_numpy(img)
            if cuda_available:
                img=img.cuda()
                img = img.half()
                self.yolo_top_cross_detection_model.half()
            else:
                img = img.float()

            img /= 255.0  # 0 - 255 to 0.0 - 1.0
            if img.ndimension() == 3:
                img = img.unsqueeze(0)
            # Inference
            pred = self.yolo_top_cross_detection_model(img)[0]
            pred = pred.float()
            # Apply NMS
            #pred = non_max_suppression(pred, self.conf_thresh_anpr, self.iou_thresh_anpr, fast=True, classes = self.classes, agnostic= self.agnostic_nms)
            pred = non_max_suppression(pred, self.top_model_confidance_thrshold, self.top_model_iou_threshold, fast=True, classes = self.classes, agnostic= self.agnostic_nms)
        

        object_conf=-1
        object_class=-1
        axles_count=0
        # print('pred : ',len(pred))
        for i, det in enumerate(pred):  # detections per image
            

            # print('------------------------------------------------------------------>',i)
            if det is not None and len(det):
                # print('det : ',det)

                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], img0.shape).round()
                
                ##########
                # Deep sort
                

                xywhs = xyxy2xywh(det[:, 0:4])
                #print('Deepsort 0')
                confs = det[:, 4]
                #print('Deepsort 1',confs)
                clss = det[:, 5]
                bottom_left_points=[]
                for index,clss_value in enumerate(clss.tolist()):
                    
                    xywhs_1=xywhs[index].cpu().unsqueeze(0)
                    confs_1=confs[index].cpu().unsqueeze(0)
                    clss_1=clss[index].cpu().unsqueeze(0)
                    x_min, y_min, x_max, y_max =det[index, :4]
                    bottom_left_points.append((x_min.item(), y_max.item()))
                    center_point_x,center_point_y=int(xywhs_1[0][0]),int(xywhs_1[0][1])

                    
            

                    if clss_value == 0 and center_point_y>= self.top_capture_yaxis_mining:
                        cv2.putText(draw_img, f"y : {str(center_point_y)} ", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        draw_img= cv2.circle(draw_img,(center_point_x,center_point_y), radius=0, color=[0,255,0], thickness=10)
                        data['Vehicle_IN_ROI']=True
                        data['distance_in_pixels']=center_point_y
                        
                        selected_label = '%s %.2f' % (self.cross_lane_class_names[int(clss_value)],confs_1)
                        plot_one_box(det[index, :4], draw_img, color=[0,255,0],label=selected_label, line_thickness=4)
                        xyxy=det[index, 0:4]
                        xyxy=xyxy.cpu().numpy()
                        mining_full_crop=crop_number_plate(xyxy,image)
                        # print('mining_full_crop.shape : ',mining_full_crop.shape)
                        data['Vehicle_Crop_Found']=True
                        data['Vehicle_Crop'].append(mining_full_crop)
                    elif clss_value==3 and center_point_y>= self.top_capture_yaxis_mining:
                        axles_count+=1
                        label = '%.1f %s' % (confs_1,self.cross_lane_class_names[int(det[index, 5])])
                        plot_one_box(det[index, :4], draw_img, color=[255,0,255],label=label, line_thickness=4)

                    elif int(clss_value)>0 and int(clss_value)<3:
                        label = '%.1f %s' % (confs_1,self.cross_lane_class_names[int(det[index, 5])])
                        plot_one_box(det[index, :4], draw_img, color=[0,255,255],label=label, line_thickness=4)
                    elif clss_value == 0 and center_point_y< self.top_capture_yaxis_mining:
                        data['Vehicle_IN_ROI']=False


                            

        draw_img=cv2.resize(draw_img,(0,0),fx=0.5,fy=0.5)
        if data['Vehicle_Crop_Found']: 
            data['Axel_count']=axles_count
            
        else:
            data['Axel_count']=0
            data['distance_in_pixels']=0
        data['Status']=0           
        data['Return_Disply_Frame'].append(draw_img)




        return data
                    
                            


        # except Exception as e:
        #     print(e)
        #     data['Status']='Error in yolo main....'
        #     data['Error']=e
            
        # return data

    def yolo_ANPR_main(self,image,camera_side='left'):
        data={  
            'Status':1,# Error 1 Done 0
            'Error':'',# Error 1 Done 0
            'Count':-1,
            'Vehicle_Number_Crop_List':[],# numpy array dict {0:[],1:[]} more then one vehiles
            'Vehicle_Number_Crop_Big_List':[],# wide context crops aligned with Vehicle_Number_Crop_List
            'Vehicle_Number_Crop_Points':[],#x,y,w,h dict {0:[],1:[]} more then one vehiles
            'Number_Plate_Found':False,# Return True,False
            'Vehicle_Found':False,
            'Return_Disply_Frame':[],
            'Front_Class':'',
            'Front_IN_ROI':False,
            'Capture_Top':False,
            'Raw_Top_Category_List':[], #dict {0:[],1:[]} more then one vehiles
            'Top_IN_ROI':False,
            'Mining_Full_Crop_Found':False,
            'Raw_Mining_Full_Crop_List':[], #dict {0:[],1:[]} more then one vehiles
            # Distinct mining-front (truck/mini_truck/hywa/tractor) centers in front ROI poly
            'Mining_Front_In_ROI_Count':0,
        }
        # try:
        try:
            draw_img = image.copy()
        except Exception as e:
            data['Error']='Image not found Yolo: ',str(e)
            return data

        mining_front_in_roi_count = 0
        selected_vehicle_xyxy = None

        with torch.no_grad():
            
            
            
            # width=image.shape[1]
            # height=image.shape[0]
            height,width,_=image.shape
            img0 = image.copy()
            
            img = letterbox(img0, new_shape = self.img_size )[0]
            img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
            img = np.ascontiguousarray(img)
            img = torch.from_numpy(img)
            if cuda_available:
                img=img.cuda()
                img = img.half()
                self.yolo_NB_detection_model.half()
            else:
                img = img.float()

            img /= 255.0  # 0 - 255 to 0.0 - 1.0
            if img.ndimension() == 3:
                img = img.unsqueeze(0)
            # Inference
            pred = self.yolo_NB_detection_model(img)[0]
            pred = pred.float()
            # Apply NMS
            pred = non_max_suppression(pred, self.conf_thresh_anpr, self.iou_thresh_anpr, fast=True, classes = self.classes, agnostic= self.agnostic_nms)
        
        
        min_x_bottom_left_value = float('inf')
        min_y_bottom_left_value = float('inf')
        min_xy_bottom_left_lst=[]
        object_conf=-1
        object_class=-1
        obj_xyxy=[]
        
        for i, det in enumerate(pred):  # detections per image
            

            # print('------------------------------------------------------------------>',i)
            if det is not None and len(det):
                # print('det : ',det)

                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], img0.shape).round()
                
                ##########
                # Deep sort
                

                xywhs = xyxy2xywh(det[:, 0:4])
                #print('Deepsort 0')
                confs = det[:, 4]
                #print('Deepsort 1',confs)
                clss = det[:, 5]
                #print('Deepsort 2',clss)
                #print('xywhs.cpu(), confs.cpu(), clss.cpu(), img0 : ',type(xywhs.cpu()), type(confs.cpu()), type(clss.cpu()),type( img0))
                # print('xywhs.cpu(), confs.cpu(), clss.cpu(), img0 : ',(xywhs.cpu()), (confs.cpu()), (clss.cpu()),type( img0))
                
                for index,clss_value in enumerate(clss.tolist()):
                    # print('index,clss_value, : ',index,clss_value)

                    xywhs_1=xywhs[index].cpu().unsqueeze(0)
                    confs_1=confs[index].cpu().unsqueeze(0)
                    clss_1=clss[index].cpu().unsqueeze(0)

                    center_point_x,center_point_y=int(xywhs_1[0][0]),int(xywhs_1[0][1])
                    # out of ROI and not Number plate and exclude non mining categories
                    # print('clss_value : ',NP_class_names[int(clss_1)],' ROI ->',point_in_polygon((center_point_x,center_point_y),self.poly_list))
                    # print('1 : ',(int(clss_value)>0 and int(clss_value)<=8) )
                    if (int(clss_value)>0 and (int(clss_value)<=8 or int(clss_value)==14) ):
                        """
                            if class is in front category
                        """
                        if int(clss_value) not in self.front_mining_cls_index_list:
                                """
                                if class is not in front category and in front_mining_cls_index_list 
                                """
                                # print('Front continue : non mining class : ',(NP_class_names[int(clss_value)]))
                                # plot_one_box(det[index, :4], draw_img, color=[0,0,255],label=(NP_class_names[int(clss_value)]), line_thickness=4)

                                continue
                        else:
                            """
                                if class is in front category and in front_mining_cls_index_list 
                            """
                            if point_in_polygon((center_point_x,center_point_y),self.poly_list)==False:
                                """
                                    if class is in front category and in front_mining_cls_index_list and out of ROI
                                """
                                # print('Front continue : Out of ROI class : ',(NP_class_names[int(clss_value)]))
                                # plot_one_box(det[index, :4], draw_img, color=[255,0,255],label='Out of ROI : '+(NP_class_names[int(clss_value)]), line_thickness=4)

                                continue
                            else:
                                """
                                    if class is in front category and in front_mining_cls_index_list and in of ROI
                                     Required vehicle
                                """
                                # print('Front In ROI class : ',(NP_class_names[int(clss_value)]))
                                # plot_one_box(det[index, :4], draw_img, color=[255,0,255],label='In ROI : '+(NP_class_names[int(clss_value)]), line_thickness=4)

                                mining_front_in_roi_count += 1
                            # print('Front IN')
                        
                    else:
                        pass
                       

                    if (int(clss_value)>8 and int(clss_value)<14):
                        if int(clss_value) not in self.top_mining_cls_index_list:
                            # print('Top continue : non mining class : ',(NP_class_names[int(clss_value)]))
                            
                            continue
                        else:
                            if point_in_polygon((center_point_x,center_point_y),self.top_poly_list)==False:
                                # print('Top continue : Out of ROI class : ',(NP_class_names[int(clss_value)]))
                                continue
                    else:
                        pass
                        # print('Top else :  Front')
                        # print('Top')



                    if ((int(clss_value)>0 and int(clss_value)<=8)) : # or int(clss_value)==14
                        # center_point_x,center_point_y=int(xywhs_1[0][0]),int(xywhs_1[0][1])
                        # print('(center_point_x,center_point_y) : ',(center_point_x,center_point_y))
                        
                        draw_img= cv2.circle(draw_img,(center_point_x,center_point_y), radius=0, color=[0,255,0], thickness=10)
                        # print('Class Name,object_conf : ',(NP_class_names[int(clss_value)],confs_1))
                        # if int(center_point_y*100/1024)>40:
                        #     print('y : ',center_point_y, ': ' ,int(center_point_y*100/1024),'% : Differance abs: ',abs(int(center_point_y*100/1024)-self.last_y_percent))
                        #     self.last_y_percent=int(center_point_y*100/1024)
                        
                        #select region of interest
                        ## y>15% of region ie object should not too much far from camera.
                        ## x>20% of region ie object should not too much far from camera.

                        
                        # if point_in_polygon((center_point_x,center_point_y),self.poly_list):
                        #point_position_wrt_line((center_point_x,center_point_y),self.point_on_line_1,self.point_on_line_2,self.point_on_line_3,self.point_on_line_4):
                        # cv2.putText(draw_img, "Vehicle is in ROI", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        
                        # x_cor=det[index, :4]
                        # left_top_c1, right_bottom_c2 = (int(x_cor[0]), int(x_cor[1])), (int(x_cor[2]), int(x_cor[3]))
                        if int(clss_value) in self.front_mining_cls_index_list  and int(center_point_y)>= self.top_capture_yaxis_mining:# for front
                            data['Capture_Top']=True


                        
                        if index ==0:
                            min_y_bottom_left_value=center_point_y
                            min_x_bottom_left_value=center_point_x
                        # print('index,min_y_bottom_left_value,min_x_bottom_left_value : ',index,min_y_bottom_left_value,min_x_bottom_left_value)
                        # if  center_point_x<= min_x_bottom_left_value and center_point_y<= min_y_bottom_left_value:
                        if  (center_point_y<= min_y_bottom_left_value and  center_point_x<= min_x_bottom_left_value):

                            min_x_bottom_left_value=xywhs_1[0][0]
                            min_y_bottom_left_value=xywhs_1[0][1]
                            obj_xyxy=det[index, :4]
    
                            if int(center_point_y)>=self.new_transaction_threshold:
                                self.difference_y_percent=abs(int(center_point_y*100/1024)-self.last_y_percent)
                                # print('y : ',center_point_y, ': ' ,int(center_point_y*100/1024),'% : Differance abs: ',self.difference_y_percent)
                                self.last_y_percent=int(center_point_y*100/1024)
                                data['Front_IN_ROI']=True
                            


                            if self.difference_y_percent>20: 
                                # print('self.difference_y_percent>20 : ',self.difference_y_percent)
                                # print('self.last_y_percent : ',self.last_y_percent)
                                count_obj(self.vehicle_count)
                                self.vehicle_count+=1
                                selected_label = '%s %.2f' % (NP_class_names[int(clss_1)],confs_1)
                                plot_one_box(obj_xyxy, draw_img, color=[0,255,0],label=selected_label, line_thickness=4)
                                # cv2.line(image, (0, 0), (int(width*.75), height), (0, 255, 0), thickness=4)
                                if int(clss_value)!=0 :#and int(clss_value)!=10
                                    data['Vehicle_Found']=True
                                    data['Front_Class']=NP_class_names[int(clss_value)]
                                    try:
                                        selected_vehicle_xyxy = obj_xyxy.detach().cpu().numpy() if hasattr(obj_xyxy, 'detach') else np.array(obj_xyxy)
                                    except Exception:
                                        selected_vehicle_xyxy = np.array(obj_xyxy.tolist() if hasattr(obj_xyxy, 'tolist') else obj_xyxy)
                                data['Count']=count
                                # print('-------Count ------- : ',data['Count'])
                            elif self.difference_y_percent<=20:
                                if int(clss_value)!=0 :#and int(clss_value)!=10
                                    data['Vehicle_Found']=True
                                    data['Front_Class']=NP_class_names[int(clss_value)]
                                    try:
                                        selected_vehicle_xyxy = obj_xyxy.detach().cpu().numpy() if hasattr(obj_xyxy, 'detach') else np.array(obj_xyxy)
                                    except Exception:
                                        selected_vehicle_xyxy = np.array(obj_xyxy.tolist() if hasattr(obj_xyxy, 'tolist') else obj_xyxy)
                                data['Count']=count
                           


                        else:
                            # cv2.putText(draw_img, "Vehicle is out ROI", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            label = '%.2f %s' % (int(det[index, 4]),NP_class_names[int(det[index, 5])])
                            plot_one_box(det[index, :4], draw_img, color=[0,255,255],label=label, line_thickness=4)
                            
                    
                    elif int(clss_value)>8 and int(clss_value)<14:
                        # center_point_x,center_point_y=int(xywhs_1[0][0]),int(xywhs_1[0][1])
                        
                        if point_in_polygon((center_point_x,center_point_y),self.top_poly_list):
                        # point_position_wrt_line((center_point_x,center_point_y),self.point_on_line_1,self.point_on_line_2,self.point_on_line_3,self.point_on_line_4):
                            cv2.putText(draw_img, "Vehicle is in ROI", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            data['Top_IN_ROI']=True
                            data['Raw_Top_Category_List'].append(NP_class_names[int(clss_value)])
                            label ='%.1f %s' % (confs_1,NP_class_names[int(det[index, 5])])
                            plot_one_box(det[index, :4], draw_img, color=[0,127,255],label=label, line_thickness=4)
                            draw_img= cv2.circle(draw_img,(center_point_x,center_point_y), radius=0, color=[0,255,0], thickness=10)
                            
                            if int(clss_value)==11:
                                # print('clss_value : ',int(clss_value))
                                xyxy=det[index, 0:4]
                                # print('xyxy : ',xyxy)
                                xyxy=xyxy.cpu().numpy()
                                mining_full_crop=crop_number_plate(xyxy,image)
                                # print('mining_full_crop.shape : ',mining_full_crop.shape)
                                data['Mining_Full_Crop_Found']=True
                                data['Raw_Mining_Full_Crop_List'].append(mining_full_crop)
                            # cv2.imwrite('test.png',mining_full_crop)
                            # else:
                            #     print('Non-mining Vehicle')
                                
                        else:

                            label = '%.1f %s' % (confs_1,NP_class_names[int(det[index, 5])])
                            plot_one_box(det[index, :4], draw_img, color=[0,255,255],label=label, line_thickness=4)
                            draw_img= cv2.circle(draw_img,(center_point_x,center_point_y), radius=0, color=[0,0,255], thickness=10)
                        
                    elif int(clss_value)==0 and  int(center_point_y)>= self.capture_numberplate_heavy_vehicles:
                        
                        if point_in_polygon((center_point_x,center_point_y),self.top_poly_list):
                            xyxy=det[index, 0:4]
                            # print('xyxy : ',xyxy)
                            xyxy=xyxy.cpu().numpy()
                            # print('process xyxy : ',xyxy)
                            label=None#'Number Plate'
                            plot_one_box(xyxy, draw_img, color=[0,0,255],label=label, line_thickness=2)# NP_class_colors[int(cls)]
                            number_plate_crop=crop_number_plate(xyxy,image)
                            number_plate_big_crop=crop_number_plate_context(xyxy,image)
                            data['Number_Plate_Found']=True
                            data['Vehicle_Number_Crop_List'].append(number_plate_crop)
                            data['Vehicle_Number_Crop_Big_List'].append(number_plate_big_crop)
                            data['Vehicle_Number_Crop_Points'].append(xyxy)

                        # print("data['Number_Plate_Found'] : ",data['Number_Plate_Found'])
                    elif int(clss_value)>0:
                        label = '%.1f %s' % (int(confs_1),NP_class_names[int(det[index, 5])])
                        plot_one_box(det[index, :4], draw_img, color=[0,255,255],label=label, line_thickness=4)



        if self.draw_lines:

            # # distance parameter horizontal line
            # draw_img=cv2.line(draw_img, (0, int(height*.4)), (int(width), int(height*.4)), (0, 255, 0), thickness=3)
                
            # draw_img=cv2.line(draw_img, (int(width*.337), int(height*.9)), (int(width*.9), int(height*.8)), (0, 255, 0), thickness=2)

            
            # # lane boundaries vertical
            # draw_img=cv2.line(draw_img, (int(width*.2), 0), (int(width*.35), height), (0, 255, 0), thickness=2)
            # draw_img=cv2.line(draw_img, (int(width*.50), 0), (int(width), height), (0, 255, 0), thickness=2)
            
            pts = np.array(self.poly_list, np.int32)
            #np.array([(0,0),(0,500),(200,500),(200,0)], np.int32)

            # Reshape the array into the required shape for fillPoly function
            pts = pts.reshape((-1, 1, 2))

            mask = np.zeros_like(draw_img)

            # Fill the area defined by the coordinates with a semi-transparent color (e.g., blue with 50% opacity)
            cv2.fillPoly(mask, [pts], (255, 0, 0, 128))  # 128 for 50% opacity in the fourth channel

            # Combine the mask with the original image
            draw_img = cv2.addWeighted(draw_img, 1, mask, 0.5, 0)
                
        
        if not data['Front_Class'] in NP_class_names[:5]:   
            data['Mining_Full_Crop_Found']=False
            data['Raw_Mining_Full_Crop_List']=[]

        # Drop plates that do not belong to the selected mining-front vehicle
        # (avoids attaching car/bike/other plates to a hywa/truck txn).
        if Filter_Plate_To_Selected_Vehicle and data['Vehicle_Number_Crop_List']:
            before = len(data['Vehicle_Number_Crop_List'])
            if selected_vehicle_xyxy is not None:
                crops, bigs, pts = filter_plates_for_vehicle(
                    data['Vehicle_Number_Crop_List'],
                    data['Vehicle_Number_Crop_Big_List'],
                    data['Vehicle_Number_Crop_Points'],
                    selected_vehicle_xyxy,
                    pad_frac=Plate_Vehicle_Assoc_Pad_Frac,
                )
                data['Vehicle_Number_Crop_List'] = crops
                data['Vehicle_Number_Crop_Big_List'] = bigs
                data['Vehicle_Number_Crop_Points'] = pts
                data['Number_Plate_Found'] = len(crops) > 0
                if before != len(crops):
                    logger.info(
                        f'Plate-vehicle filter: kept {len(crops)}/{before} '
                        f'plates for Front_Class={data.get("Front_Class")}'
                    )
            else:
                # No selected mining vehicle — do not attach orphan plates
                data['Vehicle_Number_Crop_List'] = []
                data['Vehicle_Number_Crop_Big_List'] = []
                data['Vehicle_Number_Crop_Points'] = []
                data['Number_Plate_Found'] = False
                logger.info(f'Plate-vehicle filter: dropped {before} plates (no selected vehicle)')
                            

        draw_img=cv2.resize(draw_img,(0,0),fx=0.25,fy=0.25)
        data['Status']=0           
        data['Return_Disply_Frame'].append(draw_img)
        data['Count']=count
        data['Mining_Front_In_ROI_Count']=mining_front_in_roi_count

        if data['Front_IN_ROI']==False:
            self.difference_y_percent=0
            self.last_y_percent=0
            
        # print(data['Capture_Top'],data['Raw_Top_Category_List'])/
        # if data['Number_Plate_Found']:
        #     print('Number_Plate Found')

        
        return data
                    
                            

                            




  


        # except Exception as e:
        #     print(e)
        #     data['Status']='Error in yolo main....'
        #     data['Error']=e
            
        # return data
    

VEHICLE_TYPE_SKIP_CLASSES = {'axle'}


def _yolo_model_class_names(model, fallback_names):
    names = getattr(model, 'names', None)
    if names is None:
        return fallback_names
    if isinstance(names, dict):
        return [names[i] for i in sorted(names.keys(), key=lambda x: int(x) if str(x).isdigit() else x)]
    return list(names)


class vehicle_type_pred:
    """Axle / vehicle-type OD (19-06-2026.pt). Run only on raw/top_image_valid_* frames."""

    DEFAULT_CLASS_NAMES = [
        'axle',
        'tractor_trolley',
        '2_axles_6_wheeler',
        '2_axles_dumper_6_wheeler',
        '3_axles_10_wheeler',
        '4_to_6_axles_more_than_10_wheeler',
    ]

    def __init__(self):
        weight_candidates = glob(source_path + '/weights/19-06-2026.pt')
        if not weight_candidates:
            raise FileNotFoundError('Vehicle type weights not found: metadata/weights/19-06-2026.pt')
        weights_vehicle_type = weight_candidates[0]
        save_json(
            source_path + '/loaded_model/',
            'Vehicle_Type_Detection.json',
            {'model': weights_vehicle_type},
        )
        if cuda_available:
            self.model = torch.load(weights_vehicle_type, weights_only=False)['model'].cuda()
            self.model.eval()
            self.model.half()
            print('vehicle_type_pred Model Loaded On GPU....')
            logger.info('vehicle_type_pred GPU: ' + weights_vehicle_type)
        else:
            self.model = torch.load(weights_vehicle_type, map_location='cpu', weights_only=False)['model']
            self.model.float().eval()
            print('vehicle_type_pred Model Loaded On CPU....')
            logger.info('vehicle_type_pred CPU: ' + weights_vehicle_type)

        self.class_names = _yolo_model_class_names(self.model, self.DEFAULT_CLASS_NAMES)
        self.skip_classes = VEHICLE_TYPE_SKIP_CLASSES
        self.conf_thresh = 0.4
        self.iou_thresh = 0.45
        self.agnostic_nms = 'store_true'
        self.classes = None
        self.img_size = 640

    def vehicle_type_main(self, image):
        data = {
            'Status': 1,
            'Error': None,
            'Vehicle_Type_Class': 'Not_Found',
            'Confidence': 0.0,
        }
        try:
            img0 = image.copy()
        except Exception as e:
            data['Error'] = 'Image not found: ' + str(e)
            return data

        try:
            with torch.no_grad():
                img = letterbox(img0, new_shape=self.img_size)[0]
                img = img[:, :, ::-1].transpose(2, 0, 1)
                img = np.ascontiguousarray(img)
                img = torch.from_numpy(img)
                if cuda_available:
                    img = img.cuda().half()
                    self.model.half()
                else:
                    img = img.float()
                img /= 255.0
                if img.ndimension() == 3:
                    img = img.unsqueeze(0)
                pred = self.model(img)[0].float()
                pred = non_max_suppression(
                    pred,
                    self.conf_thresh,
                    self.iou_thresh,
                    fast=True,
                    classes=self.classes,
                    agnostic=self.agnostic_nms,
                )

            best_class = 'Not_Found'
            best_conf = 0.0
            for det in pred:
                if det is None or len(det) == 0:
                    continue
                for row in det:
                    conf = float(row[4])
                    cls_idx = int(row[5])
                    if cls_idx >= len(self.class_names):
                        continue
                    cls_name = self.class_names[cls_idx]
                    if cls_name in self.skip_classes:
                        continue
                    if conf > best_conf:
                        best_conf = conf
                        best_class = cls_name

            data['Status'] = 0
            data['Vehicle_Type_Class'] = best_class
            data['Confidence'] = best_conf
        except Exception as e:
            data['Error'] = str(e)
            logger.error('vehicle_type_main: ' + str(e))
        return data


class yolo_pred_surveillance():
    def __init__(self,draw_lines=True,junction_box_roi_info=None,Gantry_ROI_info=None):

        self.surveillance_classses=['gantry',
                                    'junction_box', # 1
                                    'junction_box_tampered', # Alert 2
                                    'person', # Near to ODC 3 
                                    'animal', # Near to ODC 4
                                    'vehicle', # Near to ODC 5 
                                    'camera', # Check Position 6
                                    'led', # # Check Position 7
                                    'ir', # Check Position / ON of 8 
                                    'rfid', # check Position 9
                                    'antenna', # Check Position 10 
                                    'light_on', # Check day night light on off 11
                                    'door_open', # Alert  12
                                    'other'] #13
        self.Junction_Box_Classes=[1,2,3,4,5,13,14]
        self.Gantry_box_classes=[0,3,6,7,8,9,10,11,12,14]

        weights_surveillance='./weights/Surveillance_25112024.pt'
        save_json(source_path+'/loaded_model/','Surveillance.json',{'model':weights_surveillance})
        
        if cuda_available:
            self.Surveillance_model = torch.load(source_path+weights_surveillance)['model'].cuda()
            self.Surveillance_model.eval()
            print('Surveillance Model Loaded On GPU....')
        elif cuda_available==False :
            self.Surveillance_model = torch.load(source_path+weights_surveillance,map_location='cpu')['model']
            self.Surveillance_model.float().eval()
            print('Surveillance Model Loaded On CPU....')
        

        

        width,height=1920,1080
        self.conf_thresh = 0.4#0.8
        self.iou_thresh= 0.4#0.8
        
        self.agnostic = 'store_true'
        self.classes = None
        self.agnostic_nms = 'store_true'
        self.img_size = 640

        self.draw_lines=draw_lines

        self.point_on_line_1_junction_box = (int(width*junction_box_roi_info['1']['xRatio']), int(height*junction_box_roi_info['1']['yRatio'])) #[537  , 0]
        self.point_on_line_2_junction_box = (int(width*junction_box_roi_info['2']['xRatio']), int(height*junction_box_roi_info['2']['yRatio']))
        self.point_on_line_3_junction_box = (int(width*junction_box_roi_info['3']['xRatio']), int(height*junction_box_roi_info['3']['yRatio']))#[2688 , 1520]
        self.point_on_line_4_junction_box = (int(width*junction_box_roi_info['4']['xRatio']), int(height*junction_box_roi_info['4']['yRatio']))#[ 940, 1520]
        
        self.point_on_line_1_Gantry = (int(width*Gantry_ROI_info['1']['xRatio']), int(height*Gantry_ROI_info['1']['yRatio'])) #[537  , 0]
        self.point_on_line_2_Gantry = (int(width*Gantry_ROI_info['2']['xRatio']), int(height*Gantry_ROI_info['2']['yRatio']))
        self.point_on_line_3_Gantry = (int(width*Gantry_ROI_info['3']['xRatio']), int(height*Gantry_ROI_info['3']['yRatio']))#[2688 , 1520]
        self.point_on_line_4_Gantry = (int(width*Gantry_ROI_info['4']['xRatio']), int(height*Gantry_ROI_info['4']['yRatio']))#[ 940, 1520]
        
        self.poly_list_junction_box=[self.point_on_line_1_junction_box ,self.point_on_line_2_junction_box,self.point_on_line_3_junction_box,self.point_on_line_4_junction_box]
        self.poly_list_Gantry=[self.point_on_line_1_Gantry ,self.point_on_line_2_Gantry,self.point_on_line_3_Gantry,self.point_on_line_4_Gantry]
            
        print('YOLO Model Loaded Successfully......') 
        

    def main(self,image,image_type='Junction_box'):


        data={  
            'Status':1,# Error 1 Done 0
            'Error':None,# Error 1 Done 0
            'Gantry':False,
            'Junction_box':False, #Junction_box
            'Junction_box_tampered':False, #Junction_box
            'Person_IN_ROI':False, #Junction_box
            'Animal_IN_ROI':False, #Junction_box
            'Vehicle_IN_ROI':False, #Junction_box 
            'Camera_Movement':False, 
            'Led_Movement':False,
            'IR_Movement':False,
            'Rfid_Movement':False,
            'Antenna_Movement':False,
            'Light_on':False, 
            'Door_open':False, # Junction_box
            'Other_IN_ROI':False, # Junction_box
            'Return_Disply_Frame':[]
        }

        if image_type=='Junction_box':
            self.poly_list=self.poly_list_junction_box
        else:
            self.poly_list=self.poly_list_Gantry
        
        try:
            draw_img = image.copy()
        except Exception as e:
            data['Error']='Image not found Yolo: ',str(e)
            return data

        with torch.no_grad():
            
            height,width,_=image.shape
            img0 = image.copy()
            
            img = letterbox(img0, new_shape = self.img_size )[0]
            img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
            img = np.ascontiguousarray(img)
            img = torch.from_numpy(img)
            if cuda_available:
                img=img.cuda()
                img = img.half()
                self.Surveillance_model.half()
            else:
                img = img.float()

            img /= 255.0  # 0 - 255 to 0.0 - 1.0
            if img.ndimension() == 3:
                img = img.unsqueeze(0)
            # Inference
            pred = self.Surveillance_model(img)[0]
            pred = pred.float()
            # Apply NMS
            pred = non_max_suppression(pred, self.conf_thresh, self.iou_thresh, fast=True, classes = self.classes, agnostic= self.agnostic_nms)
        

        # object_conf=-1
        # print('pred : ',len(pred))
        # print(pred)
        for i, det in enumerate(pred):  # detections per image
            

            # print('------------------------------------------------------------------>',i)
            if det is not None and len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], img0.shape).round()

                xywhs = xyxy2xywh(det[:, 0:4])
                #print('Deepsort 0')
                confs = det[:, 4]
                #print('Deepsort 1',confs)
                clss = det[:, 5]
                bottom_left_points=[]
                for index,clss_value in enumerate(clss.tolist()):
                    clss_value=int(clss_value)
                    print('clss_value : ',clss_value)
                    xywhs_1=xywhs[index].cpu().unsqueeze(0)
                    confs_1=confs[index].cpu().unsqueeze(0)
                    x_min, y_min, x_max, y_max =det[index, :4]
                    bottom_left_points.append((x_min.item(), y_max.item()))
                    center_point_x,center_point_y=int(xywhs_1[0][0]),int(xywhs_1[0][1])
                    
                    # Junction Box classes
                    if image_type=='Junction_box':
                        if clss_value ==1 or clss_value >=3 or clss_value<=5:
                            """
                            'junction_box', # 1
                            'person', # Near to ODC 3 
                            'animal', # Near to ODC 4
                            'vehicle', # Near to ODC 5 
                            """
                            if point_in_polygon((center_point_x,center_point_y),self.poly_list)==False:
                                pass
                            else:
                                if clss_value==3:
                                    data['Person_IN_ROI']=True
                                elif clss_value==4:
                                    data['Animal_IN_ROI']=True
                                elif clss_value==5:
                                    data['Vehicle_IN_ROI']=True
                                elif clss_value==1:
                                    data['Junction_box']=True
                        elif clss_value==2:
                            #junction_box_tampered', # Alert 2

                            data['Junction_box_tampered']=True
                        elif clss_value==12:
                            #'door_open', # Alert  12
                            data['Door_open']=True
                        elif clss_value==13:
                            #'other'
                            data['Other_IN_ROI']=True

                        label ='%.1f %s' % (confs_1,self.surveillance_classses[clss_value])
                        plot_one_box(det[index, :4], draw_img, color=[0,127,255],label=label, line_thickness=4)
                        draw_img= cv2.circle(draw_img,(center_point_x,center_point_y), radius=0, color=[0,255,0], thickness=10)
                    
                        
                    else:
                        """
                        'camera', # Check Position 6
                        'led', # # Check Position 7
                        'ir', # Check Position / ON of 8 
                        'rfid', # check Position 9
                        'antenna', # Check Position 10 
                        """
                        if clss_value ==11:
                            data['Light_on']==True
                        elif clss_value ==6 :
                            data['Camera_Movement']=True
                        elif clss_value ==7:
                            data['Led_Movement']=True
                        elif clss_value ==8:
                            data["IR_Movement"]=True
                        elif clss_value ==9:
                            data["Rfid_Movement"]=True
                        elif clss_value ==10:
                            data["Antenna_Movement"]=True
                        elif clss_value ==13:
                            data["Other_IN_ROI"]=True
                        
                        label ='%.1f %s' % (confs_1,self.surveillance_classses[clss_value])
                        plot_one_box(det[index, :4], draw_img, color=[0,127,255],label=label, line_thickness=4)
                        draw_img= cv2.circle(draw_img,(center_point_x,center_point_y), radius=0, color=[0,255,0], thickness=10)
                        
                        
                        
                        
                    

                    

                    


        if self.draw_lines:
            
            pts = np.array(self.poly_list, np.int32)
            # Reshape the array into the required shape for fillPoly function
            pts = pts.reshape((-1, 1, 2))

            mask = np.zeros_like(draw_img)

            # Fill the area defined by the coordinates with a semi-transparent color (e.g., blue with 50% opacity)
            cv2.fillPoly(mask, [pts], (255, 0, 0, 128))  # 128 for 50% opacity in the fourth channel
            # cv2.fillPoly(mask, [pts_1], (255, 255, 255, 128)) 

            # Combine the mask with the original image
            draw_img = cv2.addWeighted(draw_img, 1, mask, 0.5, 0)


        draw_img=cv2.resize(draw_img,(0,0),fx=0.5,fy=0.5)
        data['Status']=0           
        data['Return_Disply_Frame'].append(draw_img)




        return data
    

        
   

# obj=yolo_pred()
# img=cv2.imread('../output/transactions_lane3/10_10_2023/59/prediction/Front_Pred_10_10_2023_01_15_15.jpg')
# print('img.shape : ',img.shape)
# while True:
#     data=obj.yolo_Front_main(img)#yolo_Front_main_mp(img)
#     # print(data['Class_Name'])
#     # print(len(data['Return_Front_Frame']),data['Return_Front_Frame'][0].shape)

# obj=yolo_pred()
# img=cv2.imread('/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/output/transactions_lane4/17_10_2023/Top_Raw_16:10:2023_10:39:49_2.jpg')
# print('img.shape : ',img.shape)
# data=obj.yolo_Top_main(img)
# print(data['Class_Name'])


# obj=yolo_pred(lane_id=1)
# source_path='/home/linux/DeepLearning/Uday/MP_AVDR/model_training/NumberPlate_Front/Lane_Monitoring/27-05-2024/Lane1-20240527T133917Z-001/Lane1/frames_1/temp/'
# intial_image=cv2.imread(source_path+'frame_0140.png')
# img=cv2.imread(source_path+'frame_0145.png')
# img1=cv2.imread(source_path+'frame_0150.png')
# img2=cv2.imread(source_path+'frame_0155.png')

# source_path='/home/linux/DeepLearning/Uday/MP_AVDR/model_training/NumberPlate_Front/Lane_Monitoring/27-05-2024/Lane1-20240527T133917Z-001/Lane1/two_vehicle_images/'

# # img2=cv2.imread('/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/output_toll/input_images/790.png')
# # img3=cv2.imread('/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/output_toll/input_images/791.png')
# # img4=cv2.imread('/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/output_toll/input_images/803.png')
# # img5=cv2.imread('/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/output/transactions_lane2/05_01_2024/04/raw/Anpr_Raw.png')

# image_list=[intial_image,intial_image,img,img,img,img1,img2,img2,img2]*1#,img2,img3,img4
# print('img.shape : ',img.shape) #[intial_image]*5#
# # for i,raw_image in enumerate(image_list):
# for i,frame_count in enumerate(range(96,111)):
#     raw_image_name=f'frame_{frame_count:04d}.png'
#     raw_image=cv2.imread(source_path+raw_image_name)
#     print('========================================================================================>',i)
#     # raw_image=cv2.resize(raw_image,(0,0),fx=0.5,fy=0.5)
#     output_json=obj.yolo_ANPR_main(raw_image)#yolo_Front_main_mp(img)
#     # cv2.imwrite(f'../output/temp/test_{str(i)}.png',output_json['Return_Disply_Frame'][0])
#     cv2.imwrite(source_path+f'pred_{str(i)}.png',output_json['Return_Disply_Frame'][0])
#     # print('Count : ',output_json['Count'])
#     print('Vehicle_Found : ',output_json['Vehicle_Found'])
#     print('Front_Class : ',output_json['Front_Class'])
#     print('Capture_Top : ',output_json['Capture_Top'])
#     print('Top_IN_ROI : ',output_json['Top_IN_ROI'])
#     print('Count :',output_json['Count'])
#     # break
    
# from glob import glob
# obj=yolo_pred(lane_id=1,image_type='TOP')
# source_path='/home/aikernel/output/IND0004270720240100859/raw/'
# image_path_list=sorted(glob(source_path+'/top_image_**')[:])
# print('len image_path_list : ',len(image_path_list))
# for i,raw_image_path in enumerate(image_path_list):
# # for i,frame_count in enumerate(range(96,111)):
#     # raw_image_name=f'frame_{frame_count:04d}.png'
    
#     raw_image=cv2.imread(raw_image_path)
#     print('========================================================================================>',i)
#     print('raw_image_path : ',raw_image_path)
#     output_json=obj.Top_main(raw_image,lane_no=1)
#     print(source_path+f'/pred/pred_{str(i)}.png')
#     cv2.imwrite(source_path+f'/pred/pred_{str(i)}.png',output_json['Return_Disply_Frame'][0])
#     print('Vehicle_Found : ',output_json['Vehicle_Found'])
#     print('Front_Class : ',output_json['Front_Class'])
#     print('Capture_Top : ',output_json['Capture_Top'])
#     print('Top_IN_ROI : ',output_json['Top_IN_ROI'])
#     print('Raw_Mining_Full_Crop_List : ',len(output_json['Raw_Mining_Full_Crop_List']))
#     print('Bonnet_Crop_Found : ',output_json['Bonnet_Crop_Found'])
#     print('Bonnet_Crop_List : ',len(output_json['Bonnet_Crop_List']))
    
#     # break

    
# from glob import glob
# obj=yolo_pred(image_type='CROSS',lane_id=1)
# # source_path='/home/linux/DeepLearning/Uday/MP_AVDR/model_training/Cross_Lane_Object_Detection_top_camera/src/images/'
# source_path="/home/linux/DeepLearning/Uday/MP_AVDR/model_training/Cross_Lane_Object_Detection_top_camera/data/tranasctions/1/"
# for image_path in glob(source_path+'/**'):

#     #image_name='Cross_Lane_top_image_22_08_2024_13_41_39_1.jpg'
#     image_name=image_path.split('/')[-1]
#     raw_image=cv2.imread(source_path+image_name)
#     print('raw_image.shape : ',raw_image.shape)
#     output_json=obj.Top_cross_lane(raw_image)
#     cv2.imwrite(source_path+f'/pred_{image_name}.png',output_json['Return_Disply_Frame'][0])
#     print('Vehicle_IN_ROI : ',output_json['Vehicle_IN_ROI'])
#     print('Vehicle_Crop_Found : ',output_json['Vehicle_Crop_Found'])
#     print('Axel_count : ',output_json['Axel_count'])
#     print('Vehicle_Crop : ',len(output_json['Vehicle_Crop']))
#     print('distance_in_pixels : ',output_json['distance_in_pixels'])
