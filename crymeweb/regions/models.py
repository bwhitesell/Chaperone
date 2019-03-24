from django.db import models
import json
import numpy as np
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon


class GeometricRegion(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    polygon_coordinates = models.TextField(null=False, blank=False)

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

        polygon_coords = json.loads(self.polygon_coordinates)
        lats_vect = np.array([coord[0] for coord in polygon_coords])
        lons_vect = np.array([coord[1] for coord in polygon_coords])
        polygon = Polygon(np.column_stack((lons_vect, lats_vect)))

        self.included_geometry = {
            'polygon_coords': polygon_coords,
            'lats_vect': lats_vect,
            'lons_vect': lons_vect,
            'polygon': polygon,
        }

    def get_bounding_box(self):
        max_lat = max([self.included_geometry['lats_vect'].max()
                       for geometry in self.included_geometry])
        min_lat = min([self.included_geometry['lats_vect'].min()
                       for geometry in self.included_geometry])
        max_long = max([self.included_geometry['lons_vect'].max()
                        for geometry in self.included_geometry])
        min_long = min([self.included_geometry['lons_vect'].min()
                        for geometry in self.included_geometry])

        return min_lat, max_lat, min_long, max_long

    def in_domain(self, y, x):
        point = Point(x, y)
        return self.included_geometry['polygon'].contains(point)
