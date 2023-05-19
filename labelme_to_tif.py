import json
import numpy as np
import rasterio
import rasterio.features
from tifffile import imsave
import os


def json_annotation_to_array(json_path, masked=True):
    """Transforms the json annotations in the JSON file at 
       'json_path' of a Geotiff at 'image_path') annotated with
       LabelMe to a numpy array (optionally masked)."""  # Open the original Geotiff and save the dimensions and optional
    # mask data
    height = 512
    width = 512

    # Open the JSON file
    with open(json_path, 'rb') as json_file:
        labelme_json = json.load(json_file)

    # Create a list of "geometry-value" pairs for use with the
    # rasterize function from rasterio
    shapes = []
    for shape in labelme_json['shapes']:
        coord_list = []
        for point in shape['points']:
            coord_list.append((point[0], point[1]))
        shapes.append(({'coordinates': [coord_list],
                        'type': 'Polygon'}, 255))

    # Create the array
    labelme_array = rasterio.features.rasterize([(g, 255) for g, v
                                                 in shapes], out_shape=(height, width),
                                                all_touched=True)


    return labelme_array

path = "/home/ben/repos/sentinel_data/new_plumes/clouds/"
for folder in os.listdir(path):
    json_path = path+folder+'/label.json'

    xd = json_annotation_to_array(json_path, False)
    imsave(path+folder+'/label.tif', xd)
    print("xd")
