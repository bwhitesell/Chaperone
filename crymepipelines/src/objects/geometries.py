import json
import numpy as np
from settings import cp_conn
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon


class GeometricRegion:

    id = int
    name = str
    geometry = str

    def __init__(self, id):
        self.id = id
        with cp_conn.cursor() as cursor:
            cursor.execute(f'SELECT * FROM geometries WHERE id={self.id};')
            raw_data = cursor.fetchone()

        self._parse_data(raw_data['geom_json'])
        self.name = raw_data['name']

    def __str__(self):
        return f'Geometric Region: {self.name}'

    def _parse_data(self, geometry):
            polygon_coords = json.loads(geometry)['geometries'][0]['coordinates'][0][0]
            lats_vect = np.array([float(coord[0]) for coord in polygon_coords])
            lons_vect = np.array([float(coord[1]) for coord in polygon_coords])
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

    def in_domain(self, x, y):
        point = Point(x, y)
        return self.included_geometry['polygon'].contains(point)