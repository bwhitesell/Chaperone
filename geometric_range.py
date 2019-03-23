import json
import numpy as np
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

from constants import geometries


class GeometricDomain:
    included_geometries = {}

    def __init__(self, geoms):
        for geom in geoms:

            with open(geometries[geom], 'r') as geom_file:
                polygon_coords = json.loads(geom_file.read())['geometries'][0]['coordinates'][0][0]

            lats_vect = np.array([coord[0] for coord in polygon_coords])
            lons_vect = np.array([coord[1] for coord in polygon_coords])
            polygon = Polygon(np.column_stack((lons_vect, lats_vect)))

            self.included_geometries[geom] = {
                'polygon_coords': polygon_coords,
                'lats_vect': lats_vect,
                'lons_vect': lons_vect,
                'polygon': polygon,
            }

    def get_bounding_box(self):
        max_lat = max([self.included_geometries[geometry]['lats_vect'].max()
                       for geometry in self.included_geometries])
        min_lat = min([self.included_geometries[geometry]['lats_vect'].min()
                       for geometry in self.included_geometries])
        max_long = max([self.included_geometries[geometry]['lons_vect'].max()
                        for geometry in self.included_geometries])
        min_long = min([self.included_geometries[geometry]['lons_vect'].min()
                        for geometry in self.included_geometries])

        return min_lat, max_lat, min_long, max_long

    def in_domain(self, y, x):
        point = Point(x, y)
        for geometry in self.included_geometries:
            if self.included_geometries[geometry]['polygon'].contains(point):
                return True
        return False
