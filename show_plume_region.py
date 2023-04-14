from osgeo import osr, gdal
import re
import numpy as np
import math
from PIL import Image as im
import os
import csv

def normalize(band):
    band_min, band_max = (band.min(), band.max())
    return ((band-band_min)/((band_max - band_min)))


def brighten(band):
    alpha=0.13
    beta=0
    return np.clip(alpha*band+beta, 0,255)

def convert_dtype(band):
    band = band.astype(np.float64) / np.max(band) # normalize the data to 0 - 1
    band = 255 * band # Now scale by 255
    band = band.astype(np.uint8)
    return band

# assign directory
directory = "/mnt/c/Users/bgorr/PycharmProjects/untitled/untitled/sentinel_images_texas/"

points = []
with open("./tx_plume_locations.txt") as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        points.append([float(row[0]), float(row[1])])
# iterate over files in
# that directory
file_count = 0
for filename in os.listdir(directory):
    f = os.path.join(directory, filename)
    # checking if it is a file
    if os.path.isfile(f):
        # get the existing coordinate system
        ds = gdal.Open(f)
        footprint_string = ds.GetMetadata()["FOOTPRINT"]
        print(file_count)
        #print(footprint_string)
        subdatasets = ds.GetSubDatasets()
        mysubdataset_name = subdatasets[0][0] # corresponds to 10m band
        mydata = gdal.Open(mysubdataset_name, gdal.GA_ReadOnly)
        mydata = mydata.ReadAsArray()
        print(mydata.shape)
        print(subdatasets)
        true_color_data_name = subdatasets[3][0]
        true_color_data = gdal.Open(true_color_data_name, gdal.GA_ReadOnly)
        true_color_data = true_color_data.ReadAsArray()
        print(true_color_data.shape)
        res = re.findall("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", footprint_string)
        ul = (float(res[0]),float(res[1]))
        lr = (float(res[4]),float(res[5]))
        # print(ul)
        # print(lr)
        array = np.asarray(mydata)        
        blue = array[0,:,:]
        blue_bn = convert_dtype(normalize(blue))
        green = array[1,:,:]
        green_bn = convert_dtype(normalize(green))
        red = array[2,:,:]
        red_bn = convert_dtype(normalize(red))
        rgb_array = np.dstack((red_bn,green_bn,blue_bn))
        full_data = im.fromarray(rgb_array)  
        full_data.save('full_'+str(file_count)+'.png')
        for point in points:
            lat = point[0]
            lon = point[1]
            if(ul[0] < lon < lr[0]):
                left_right_frac = (ul[0]-lon)/(ul[0]-lr[0])
            else:
                continue
            if(lr[1] < lat < ul[1]):
                up_down_frac = (ul[1]-lat)/(ul[1]-lr[1])
            else:
                continue
            # print(left_right_frac)
            # print(up_down_frac)
            y_pos = math.floor(up_down_frac*array.shape[1])
            x_pos = math.floor(left_right_frac*array.shape[2])

            image_size = 400
            top = 0
            bottom = array.shape[1]
            left = 0
            right = array.shape[2]
            if y_pos > image_size/2:
                top = math.floor(y_pos - image_size/2)
            if y_pos < array.shape[1]-image_size/2:
                bottom = math.floor(y_pos + image_size/2)
            if x_pos > image_size/2:
                left = math.floor(x_pos - image_size/2)
            if x_pos < array.shape[2]-image_size/2:
                right = math.floor(x_pos + image_size/2)
            # print(top)
            # print(bottom)
            # print(left)
            # print(right)
            red_slice = red[top:bottom,left:right]
            green_slice = green[top:bottom,left:right]
            blue_slice = blue[top:bottom,left:right]
            red_slice_n = convert_dtype(normalize(red_slice))
            green_slice_n = convert_dtype(normalize(green_slice))
            blue_slice_n = convert_dtype(normalize(blue_slice))
            # print(img_array)
            rgb_slice = np.dstack((red_slice_n,green_slice_n,blue_slice_n))
            data = im.fromarray(rgb_slice)
            # saving the final output 
            # as a PNG file
            data.save('slice_'+str(lat)+'_'+str(lon)+'_'+str(file_count)+'.png')
            array_tc = np.asarray(true_color_data)
            blue_tc = array_tc[2,:,:]
            green_tc = array_tc[1,:,:]
            red_tc = array_tc[0,:,:]
            red_tc_slice = red_tc[top:bottom,left:right]
            green_tc_slice = green_tc[top:bottom,left:right]
            blue_tc_slice = blue_tc[top:bottom,left:right]
            rgb_tc_slice = np.dstack((red_slice_n,green_slice_n,blue_slice_n))
            tc_img = im.fromarray(rgb_tc_slice)
            tc_img.save('slice_tc_'+'_'+str(lat)+'_'+str(lon)+'_'+str(file_count)+'.png')
    file_count += 1