from osgeo import osr, gdal
import re
import numpy as np
import math
import requests
from PIL import Image as im
import os
import csv
import urllib.request
import matplotlib.pyplot as plt

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

def get_tblr(array,image_size): # returns top bottom left right image dims
    y_pos = math.floor(up_down_frac*array.shape[1])
    x_pos = math.floor(left_right_frac*array.shape[2])
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
    return top, bottom, left, right

# assign directory
directory = "./cloud_images/"

points = []
with open("./cloud_image.txt") as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        points.append([float(row[0]), float(row[1])])
# iterate over files in
# that directory
file_count = 0
good_locations = []
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
        print(mysubdataset_name)
        mydata = gdal.Open(mysubdataset_name, gdal.GA_ReadOnly)
        mydata = mydata.ReadAsArray()
        print(mydata.shape)
        print(subdatasets)
        twenty_meter_data_name = subdatasets[1][0]
        print(twenty_meter_data_name)
        twenty_meter_data = gdal.Open(twenty_meter_data_name, gdal.GA_ReadOnly)
        twenty_meter_data = twenty_meter_data.ReadAsArray()
        print(twenty_meter_data.shape)
        sixty_meter_data_name = subdatasets[2][0]
        print(sixty_meter_data_name)
        sixty_meter_data = gdal.Open(sixty_meter_data_name, gdal.GA_ReadOnly)
        sixty_meter_data = sixty_meter_data.ReadAsArray()
        print(sixty_meter_data.shape)
        res = re.findall("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", footprint_string)
        print(footprint_string)
        print(res)
        image_points = []
        ul = (0.0,0.0)
        if len(res) > 10:
            continue
        for i in range(int(len(res)/2)):
            image_points.append((float(res[2*i]),float(res[2*i+1])))
        leftmost = 180
        uppermost = -90
        for img_pt in image_points:
            if img_pt[0] < leftmost and img_pt[1] > uppermost:
                ul = img_pt
                leftmost = img_pt[0]
                uppermost = img_pt[1]
        furthest_dist = 0
        for img_pt in image_points:
            dist = np.sqrt((ul[0]-img_pt[0])**2+(ul[1]-img_pt[1])**2)
            if dist > furthest_dist:
                lr = img_pt
                furthest_dist = dist
        ul = (float(res[0]),float(res[1]))
        lr = (float(res[4]),float(res[5]))
        # print(ul)
        # print(lr)
        array = np.asarray(mydata)
        twenty_meter_array = np.asarray(twenty_meter_data)
        sixty_meter_array = np.asarray(sixty_meter_data)  
        blue = array[0,:,:]
        blue_bn = convert_dtype(normalize(blue))
        green = array[1,:,:]
        green_bn = convert_dtype(normalize(green))
        red = array[2,:,:]
        red_bn = convert_dtype(normalize(red))
        nir = array[3,:,:]
        nir_bn = convert_dtype(normalize(nir))
        swir = twenty_meter_array[4,:,:]
        swir_bn = convert_dtype(normalize(swir))
        swir2 = twenty_meter_array[5,:,:]
        swir2_bn = convert_dtype(normalize(swir2))
        aot = twenty_meter_array[6,:,:]
        aot_bn = convert_dtype(normalize(aot))
        wvp = twenty_meter_array[10,:,:]
        wvp_bn = convert_dtype(normalize(wvp))
        rgb_array = np.dstack((red_bn,green_bn,blue_bn))
        full_data = im.fromarray(rgb_array)  
        #full_data.save('full_'+str(file_count)+'.png')
        
        for point in points:
            lat = point[0]
            lon = point[1]
            print(lat)
            print(lon)
            if(ul[0] < lon < lr[0]):
                left_right_frac = (ul[0]-lon)/(ul[0]-lr[0])
            else:
                continue
            if(lr[1] < lat < ul[1]):
                up_down_frac = (ul[1]-lat)/(ul[1]-lr[1])
            else:
                continue
            print(left_right_frac)
            print(up_down_frac)

            image_size = 512
            top,bottom,left,right = get_tblr(array,image_size)
            ts,bs,ls,rs = get_tblr(twenty_meter_array,256)
            #tw,bw,lw,rw = get_tblr(sixty_meter_array,256)

            # print(top)
            # print(bottom)
            # print(left)
            # print(right)
            red_slice = red[top:bottom,left:right]
            green_slice = green[top:bottom,left:right]
            blue_slice = blue[top:bottom,left:right]
            nir_slice = nir[top:bottom,left:right]
            swir_slice = swir[ts:bs,ls:rs]
            swir2_slice = swir2[ts:bs,ls:rs]
            aot_slice = aot[ts:bs,ls:rs]
            wvp_slice = wvp[ts:bs,ls:rs]
            red_slice_n = convert_dtype(normalize(red_slice))
            green_slice_n = convert_dtype(normalize(green_slice))
            blue_slice_n = convert_dtype(normalize(blue_slice))
            nir_slice_n = convert_dtype(normalize(nir_slice))
            swir_slice_n = convert_dtype(normalize(swir_slice))
            swir2_slice_n = convert_dtype(normalize(swir2_slice))
            aot_slice_n = convert_dtype(normalize(aot_slice))
            wvp_slice_n = convert_dtype(normalize(wvp_slice))

            # print(img_array)
            rgb_slice = np.dstack((red_slice_n,green_slice_n,blue_slice_n))
            #data = im.fromarray(rgb_slice)
            # saving the final output 
            # as a PNG file
            #data.save('slice_'+str(lat)+'_'+str(lon)+'_'+str(file_count)+'.png')
            gmap_url = "https://maps.googleapis.com/maps/api/staticmap?center="+str(lat)+","+str(lon)+"&zoom=15&maptype=satellite&size=512x512&key=AIzaSyBg-oR8oz0Ty4CLwrycLfLbh2qIq8FGUH4"
            urllib.request.urlretrieve(gmap_url, "./xd.jpg")
            gmap_image = im.open("./xd.jpg").convert("RGB")
            #gmap_image.show()
            #plt.figure()

            #subplot(r,c) provide the no. of rows and columns
            f, axarr = plt.subplots(2,4)
            f.set_size_inches(10,8)

            # use the created array to output your multiple images. In this case I have stacked 4 images vertically
            axarr[0,0].imshow(rgb_slice)
            axarr[0,1].imshow(nir_slice_n)
            axarr[0,2].imshow(swir_slice_n)
            axarr[0,3].imshow(swir2_slice_n)
            axarr[1,0].imshow(aot_slice)
            axarr[1,1].imshow(wvp_slice_n)
            axarr[1,2].imshow(np.asarray(gmap_image))
            
            plt.show()
            location_good = input("Is the location good?")
            if "y" in location_good:
                good_locations.append(point)
                plume_present = input("Is there a plume in the image?")
                if "y" in plume_present:
                    new_dir = "./new_plumes/plume"+str(lat)+'_'+str(lon)+'_'+str(file_count)+"/"
                    os.mkdir(new_dir)
                    rgb_slice_n = np.dstack([red_slice_n,green_slice_n,blue_slice_n])
                    im.fromarray(rgb_slice_n).save(new_dir+"rgb.png")
                    im.fromarray(red_slice_n).save(new_dir+'red.png')
                    im.fromarray(green_slice_n).save(new_dir+'green.png')
                    im.fromarray(blue_slice_n).save(new_dir+'blue.png')
                    im.fromarray(nir_slice_n).save(new_dir+'nir.png')
                    im.fromarray(swir_slice_n).save(new_dir+'swir.png')
            if "s" in location_good:
                break




    file_count += 1

with open("./good_smokestacks.csv","w") as csvfile:
    csvwriter = csv.writer(csvfile)
    for loc in good_locations:
        csvwriter.writerow(loc)