from geojson import Point
import csv
import json

points = []
with open("./cloud_image.txt") as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        points.append([float(row[0]), float(row[1])])
for i in range(len(points)):
    features = []
    feature = {
        "type": "Feature",
        "geometry": Point((points[i][1], points[i][0]))
    }
    features.append(feature)
    x = {
        "type": "FeatureCollection",
        "features": features
    }
    with open('./cloud_geojsons/cloud_'+str(i)+'.geojson', 'w') as fp:
        json.dump(x, fp)