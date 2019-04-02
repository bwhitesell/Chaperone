from django.db import models
import json
import numpy as np
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon


class GeometricRegionManager(models.Manager):
    def in_domain(self, x, y):
        for region in self.all():
            if region.in_domain(x, y):
                return True
        return False


class GeometricRegion(models.Model):
    """ A model to define regions for which there is total incident reporting coverage I.E. valid domains. """

    name = models.CharField(max_length=100, null=False, blank=False)
    polygon_coordinates = models.TextField(null=False, blank=False)

    objects = GeometricRegionManager()


    def __str__(self):
        return 'Region: ' + self.name

    def geom(func):  # an in-class decorator for lazy loading of geometric objects
        def _load_geom_and_eval(self, *args, **kwargs):
            if not hasattr(self, 'included_geometry'):
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
            return func(self, *args, **kwargs)

        return _load_geom_and_eval

    @geom
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

    @geom
    def in_domain(self, x, y):
        point = Point(x, y)
        return self.included_geometry['polygon'].contains(point)
