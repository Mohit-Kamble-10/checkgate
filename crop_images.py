import numpy as np
import cv2
from glob import glob
from matplotlib import pyplot as plt
pixel_difference_two_line=5 #pixel
boundingRect_height_threshold=5#pixel
class rearrange_crop_images():
    def __init__(self) -> None:
        pass
    
    def crop_old(self,image,points_list):
        crop_image_list=[]
        for bbox in points_list:


            # img = cv2.imread("test.png")
            pts = bbox#np.array([bbox])
            # print('pts : ',pts)

            ## (1) Crop the bounding rect
            rect = cv2.boundingRect(pts)
            x,y,w,h = rect
            # print('x,y,w,h : ',x,y,w,h)
            croped = image[y:y+h, x:x+w].copy()

            ## (2) make mask
            pts = pts - pts.min(axis=0)

            mask = np.zeros(croped.shape[:2], np.uint8)
            # cv2.drawContours(mask, [pts], -1, (255, 255, 255), -1, cv2.LINE_AA)

            ## (3) do bit-op
            dst = cv2.bitwise_and(croped, croped, mask=mask)

            ## (4) add the white background
            bg = np.ones_like(croped, np.uint8)*255
            cv2.bitwise_not(bg,bg, mask=mask)
            dst2 = bg+ dst

            # x1,y1=bbox[0]
            # x2,y2=bbox[2]
            # crop_image=image[int(y1):int(y2),int(x1):int(x2)]
            crop_image_list.append(croped)
        return crop_image_list    
    
    def rotate_crop(self,img,pts):
        rect = cv2.minAreaRect(pts)
        angle = rect[2]-180
        
        # if angle < -45:
        #     angle = (90 + angle)

        if angle < -45 and angle>-100:
            angle = (90 + angle)
        elif angle>=-180:
            angle = (180 + angle)

        # otherwise, just take the inverse of the angle to make
        # it positive
        else:
            angle = -angle  
        # print('final angle : ',angle)
        # rotate the image to deskew it
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated_img = cv2.warpAffine(img, M, (w, h),
            flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE) 
        # print('rotate_crop : Done')
        return rotated_img

    def preprocess(self,polys,image_area):
        processed_poly=[]
        for poly in polys:
            poly=np.array(poly,dtype=np.int32)
            try:
                conture_area=cv2.contourArea(poly)
            except:
                conture_area = cv2.contourArea(poly)[0]
            # print('conture_area : ',conture_area)
            if (conture_area*100/image_area)<1:
                continue
            else:
                # poly=np.array(poly,dtype=np.int32)
                r,c=poly.shape
                poly=poly.reshape(r,1,c)
            # print('poly.shape : ',poly.shape)
            processed_poly.append(poly)
        # print('preprocess : Done')
        return processed_poly

    def horizontal_sort(self,x_list,y_list,new_polys):
        sorted_line={}
        for i in range(len(x_list)):
            index=x_list.index(min(x_list))
            x_list.pop(index)
            y_list.pop(index)
            temp_poly=new_polys[index]
            new_polys.pop(index)
            sorted_line[i]=temp_poly
        # print('horizontal_sort : Done')
        return sorted_line
    

    def rearrange(self,org_new_polys):

        x_list=[]
        y_list=[]
        new_polys=org_new_polys.copy()
        for poly in new_polys:
            
            try:
                x=[pp2[0] for pp1 in  poly for pp2 in pp1 ]
                y=[pp2[1] for pp1 in  poly for pp2 in pp1 ]
            except:    
                x = [p[0] for p in poly[0]]
                y = [p[1] for p in poly[0]]
            centroid = (sum(x) / len(poly), sum(y) / len(poly))
            x_list.append(centroid[0])
            y_list.append(centroid[1])
            # print(centroid)

        # print('x_list : ',x_list)
        # print('y_list : ',y_list)



        #'One-liner Number Plate'
        if max(y_list)-min(y_list)<=pixel_difference_two_line:# pixel_difference_two_line
            # print('One-liner Number Plate')
            sorted_line={}
            for i in range(len(x_list)):
                index=x_list.index(min(x_list))
                x_list.pop(index)
                y_list.pop(index)
                temp_poly=new_polys[index]
                new_polys.pop(index)
                sorted_line[i]=[temp_poly]
            return sorted_line
        else:
            # print('Two-liner or more liner Number Plate')
            sorted_line={}
            # Sorted Line 1 and Line 2
            sorted_polys_by_height=sorted(y_list)
            # print('sorted_polys_by_height : ',sorted_polys_by_height)
            y_line_sorted={}
            line=1
            start_index=0
            for index in range(len(y_list)-1):
                # print('index : ',index,y_line_sorted)
                if sorted_polys_by_height[index+1]-sorted_polys_by_height[index]>pixel_difference_two_line:# Check same line if pix diff >5
                    # print('start_index:index+1 : ',start_index,' : ',index+1)
                    # print('start_index:index+1 : ',start_index,' : ',index+1)
                    y_line_sorted['line_'+str(line)]=[{'y_list':sorted_polys_by_height[start_index:index+1]}]
                    start_index=index+1
                    line+=1
            # print('start_index : ',start_index)
            if sorted_polys_by_height[start_index]-sorted_polys_by_height[start_index-1]>pixel_difference_two_line:
                y_line_sorted['line_'+str(len(y_line_sorted)+1)]=[{'y_list':sorted_polys_by_height[start_index:]}]


            # print('y_line_sorted : ',y_line_sorted)
            
            for line,y_line_data in y_line_sorted.items():
                # print('line,y_line_data : ',line,y_line_data)
                x_list_temp=[]
                new_polys_temp=[]
                for y_value in y_line_data[0]['y_list']:
                    index=y_list.index(y_value)
                    x_list_temp.append(x_list[index])
                    new_polys_temp.append(new_polys[index])
                y_line_sorted[line].append({'x_list':x_list_temp})
                y_line_sorted[line].append({'new_polys':{0:new_polys_temp}})

            # print('updated y_line_sorted : ',y_line_sorted)
                


            for line,line_data in y_line_sorted.items():
                if len(line_data[0]['y_list'])>1:
                    y_line_sorted[line][2]['new_polys']=self.horizontal_sort(line_data[1]['x_list'],line_data[0]['y_list'],line_data[2]['new_polys'][0])


        final_sorted={}
        count=0
        for _ , data_dict in y_line_sorted.items():
            # print('data_dict[2] : ',data_dict[2])
            for _,poly_array in data_dict[2]['new_polys'].items():
                final_sorted[count]=poly_array
                count+=1


                    

        # print('--------------------------------')
        # print('final_sorted : ',final_sorted)
        # print('--------------------------------')
        return final_sorted




    def crop_poly(self,img, rearranged_polys):
        image_list=[] 
        roated_image_list=[]
        # print('rearranged_polys : ',rearranged_polys)
        for line_num,poly in rearranged_polys.items():

            pts=poly[0]
            # pts=np.array(pts,dtype=np.int16)
            # print('poly :',poly.shape)
            # print('pts : ',type(pts),pts.shape)
            rect = cv2.boundingRect(pts)
            x,y,w,h = rect
            if h<=boundingRect_height_threshold:
                continue
            croped = img[y:y+h, x:x+w].copy()

            ## (2) make mask
            pts = pts - pts.min(axis=0)

            mask = np.zeros(croped.shape[:2], np.uint8)
            cv2.drawContours(mask, [pts], -1, (255, 255, 255), -1, cv2.LINE_AA)

            ## (3) do bit-op
            dst = cv2.bitwise_and(croped, croped, mask=mask)

            ## (4) add the white background
            bg = np.ones_like(croped, np.uint8)*255
            cv2.bitwise_not(bg,bg, mask=mask)
            dst2 = bg+ dst
            image_list.append(dst)
            roated_image_list.append(self.rotate_crop(dst,pts))
            
            # break
        # print('crop_poly : Done')
        return image_list,roated_image_list


    
def check_crop_distribution():
    images=glob('/home/linux/DeepLearning/Uday/Toll/ANPR_Yolo_Model/OCR_Opencv/data/**/crops/Number_Plate/**')
    print('len(images) :',len(images))
    h_list=[]
    w_list=[]
    for image_path in images:
        image = cv2.imread(image_path)
        h,w=image.shape[:2]
        h_list.append(h)
        w_list.append(w)
    # Creating histogram
    fig, ax = plt.subplots(figsize =(10, 7))
    # ax.hist(h_list, bins = [  0.,  30.,  60.,  90., 120., 150., 180., 210., 240., 270., 300.,330., 360., 390., 420., 450., 480., 510., 540., 570., 600.])
    ax.hist(w_list, bins = [  0.,  30.,  60.,  90., 120., 150., 180., 210., 240., 270., 300.,330., 360., 390., 420., 450., 480., 510., 540., 570., 600.])
    

    plt.title('Mean')
    plt.xlabel("value")
    plt.ylabel("Frequency")
    plt.savefig("width.png")

    # Show plot
    # plt.show()

# check_crop_distribution()
    

# polys = [[
#         [ 22.1054868 ,  27.51019071],
#         [ 40.68942108 , 25.91728161],
#         [ 71.17721176 , 23.31586977],
#         [ 99.97618839 , 20.84071587],
#         [132.83613305 , 19.10434865],
#         [161.24906425 , 17.79652576],
#         [194.89949397 , 17.25498805],
#         [200.70700951 , 54.36430624],
#         [167.05658013 , 54.90584365],
#         [135.47478514 , 56.57376043],
#         [104.06783557 , 58.17931885],
#         [ 73.05644759 , 60.83076875],
#         [ 43.7338746  , 63.35596064],
#         [ 25.14994053 , 64.94886953]]]

# img=np.zeros((80, 208, 3))
# print('img.shape :',img.shape)
# obj=rearrange_crop_images()
# process_polys_list=obj.preprocess(polys)
# print('--------process_polys_list Done -------------')
# rearrange_dict=obj.rearrange(process_polys_list)
# print('--------rearrange Done -------------')
# sorted_image_list=obj.crop_poly(img,rearrange_dict)
# print('--------sorted_image_list Done -------------')
