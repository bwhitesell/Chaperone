import datetime
from pyspark.sql.types import ArrayType, StructType, IntegerType, StructField, StringType, FloatType, TimestampType, \
    DecimalType
from pyspark.sql.functions import udf
import mpu
import numpy as np
import os
import pandas as pd
import folium
import branca


# Define native python mappings here
def assign_coordinate_to_lat_box(latitude):
    try:
        lat_box = abs(int(latitude / (1 * 0.004363475000000037)))
        return lat_box
    except ValueError:
        return 0


def assign_coordinate_to_lon_box(longitude):
    try:
        lon_box = abs(int(longitude / (1 * 0.007254180000003885)))
        return lon_box
    except ValueError:
        return 0


def time_occ_to_seconds(time_occ):
    try:
        return int(time_occ[:2]) * 60 ** 2 + int(time_occ[2:]) * 60
    except ValueError:
        return -99


def cla_timestamp_to_datetime(cla_ts):
    try:
        return datetime.datetime.strptime(cla_ts, '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        return datetime.datetime(year=1, month=1, day=1)


def crime_occ(n_crimes):
    return 1 if n_crimes > 0 else 0


def ts_to_minutes_in_day(x):
    return x.hour * 60 + x.minute


def ts_to_hour_of_day(x):
    return x.hour


def ts_to_day_of_week(x):
    return x.weekday()


# Define UDFs here
actb_lat = udf(assign_coordinate_to_lat_box, IntegerType())
actb_lon = udf(assign_coordinate_to_lon_box, IntegerType())
ts_conv = udf(cla_timestamp_to_datetime, TimestampType())
t_occ_conv = udf(time_occ_to_seconds, IntegerType())
space_dist = udf(lambda w, x, y, z: mpu.haversine_distance((w, x), (y, z)) * 0.621371, FloatType())
crime_occ_udf = udf(crime_occ, IntegerType())
ts_to_minutes_in_day_udf = udf(ts_to_minutes_in_day, IntegerType())
ts_to_hour_of_day_udf = udf(ts_to_hour_of_day, IntegerType())
ts_to_day_of_week_udf = udf(ts_to_day_of_week, IntegerType())


safety_rel_crimes = {
    624: 'BATTERY - SIMPLE ASSAULT',
    740: 'VANDALISM - FELONY ($400 & OVER, ALL CHURCH VANDALISMS)',
    626: 'INTIMATE PARTNER - SIMPLE ASSAULT',
    330: 'BURGLARY FROM VEHICLE',
    510: 'VEHICLE - STOLEN',
    310: 'BURGLARY',
    440: 'THEFT PLAIN - PETTY ($950 & UNDER)',
    230: 'ASSAULT WITH DEADLY WEAPON, AGGRAVATED ASSAULT',
    210: 'ROBBERY',
    420: 'THEFT FROM MOTOR VEHICLE - PETTY ($950 & UNDER)',
    745: 'VANDALISM - MISDEAMEANOR ($399 OR UNDER)',
    930: 'CRIMINAL THREATS - NO WEAPON DISPLAYED',
    341: 'THEFT-GRAND ($950.01 & OVER)EXCPT,GUNS,FOWL,LIVESTK,PROD',
    888: 'TRESPASSING',
    236: 'INTIMATE PARTNER - AGGRAVATED ASSAULT',
    331: 'THEFT FROM MOTOR VEHICLE - GRAND ($400 AND OVER)',
    761: 'BRANDISH WEAPON',
    480: 'BIKE - STOLEN',
    350: 'THEFT, PERSON',
    320: 'BURGLARY, ATTEMPTED',
    220: 'ATTEMPTED ROBBERY',
    860: 'BATTERY WITH SEXUAL CONTACT',
    625: 'OTHER ASSAULT',
    623: 'BATTERY POLICE (SIMPLE)',
    121: 'RAPE, FORCIBLE',
    627: 'CHILD ABUSE (PHYSICAL) - SIMPLE ASSAULT',
    753: 'DISCHARGE FIREARMS/SHOTS FIRED',
    886: 'DISTURBING THE PEACE ',
    648: 'ARSON',
    437: 'RESISTING ARREST',
    940: 'EXTORTION',
    520: 'VEHICLE - ATTEMPT STOLEN',
    850: 'INDECENT EXPOSURE',
    812: 'CRM AGNST CHLD (13 OR UNDER) (14-15 & SUSP 10 YRS OLDER)',
    352: 'PICKPOCKET',
    251: 'SHOTS FIRED AT INHABITED DWELLING',
    110: 'CRIMINAL HOMICIDE',
    421: 'THEFT FROM MOTOR VEHICLE - ATTEMPT',
    815: 'SEXUAL PENETRATION W/FOREIGN OBJECT',
    910: 'KIDNAPPING',
    441: 'THEFT PLAIN - ATTEMPT',
    647: 'THROWING OBJECT AT MOVING VEHICLE',
    820: 'ORAL COPULATION',
    932: 'PEEPING TOM',
    763: 'STALKING',
    235: 'CHILD ABUSE (PHYSICAL) - AGGRAVATED ASSAULT',
    122: 'RAPE, ATTEMPTED',
    351: 'PURSE SNATCHING',
    231: 'ASSAULT WITH DEADLY WEAPON ON POLICE OFFICER',
    450: 'THEFT FROM PERSON - ATTEMPT',
    250: 'SHOTS FIRED AT MOVING VEHICLE, TRAIN OR AIRCRAFT',
    755: 'BOMB SCARE',
    920: 'KIDNAPPING - GRAND ATTEMPT',
    760: 'LEWD/LASCIVIOUS ACTS WITH CHILD',
    822: 'HUMAN TRAFFICKING - COMMERCIAL SEX ACTS',
    813: 'CHILD ANNOYING (17YRS & UNDER)',
    933: 'PROWLER',
    668: 'EMBEZZLEMENT, GRAND THEFT ($950.01 & OVER)',
    434: 'FALSE IMPRISONMENT',
    943: 'CRUELTY TO ANIMALS',
    438: 'RECKLESS DRIVING',
    806: 'PANDERING',
    487: 'BOAT - STOLEN',
    622: 'BATTERY ON A FIREFIGHTER',
    451: 'PURSE SNATCHING - ATTEMPT',
    922: 'CHILD STEALING',
    805: 'PIMPING',
    485: 'BIKE - ATTEMPTED STOLEN',
    470: 'TILL TAP - GRAND THEFT ($950.01 & OVER)',
}
    
    
    
def build_risk_map(rfc, time_of_day):
    n = 100
    start_lon = 34.300779
    end_lon = 33.749713
    start_lat = -118.155360
    end_lat = -118.666218
    delta_lon = (end_lon - start_lon) / n
    delta_lat = (end_lat - start_lat) / n

    # build geometry
    features_ = []
    for row in range(0, n):
        for col in range(0, n):
            top_lft_lon = start_lon + row * delta_lon
            top_lft_lat = start_lat + col * delta_lat
            feat_dict = {
                "type":"Feature",
                "id":str(top_lft_lon + delta_lon/2) + '_' + str(top_lft_lat + delta_lat/2),
                "properties": {"name": str(row) + '_' + str(col)}
            }

            coordinates = [[
                [top_lft_lat, top_lft_lon],
                [top_lft_lat + delta_lat, top_lft_lon],
                [top_lft_lat + delta_lat, top_lft_lon + delta_lon],
                [top_lft_lat, top_lft_lon + delta_lon],
            ]]

            feat_dict["geometry"] = {
                "type":"Polygon",
                "coordinates": coordinates
            }
            features_.append(feat_dict)


    la_grid_geo = {
        "type":"FeatureCollection",
        "features": features_,
    }
    
    # assign geometry values
    point_ids = [z['id'] for z in la_grid_geo['features']]
    points = [[float(i) for i in j.split('_')] for j in point_ids]
    points = [i + [time_of_day] for i in points]
    points = np.array(points)
    c = rfc.predict_proba(points)[:,1]
    crime_risk = pd.DataFrame({'id': point_ids, 'risk': rfc.predict_proba(points)[:,1]})
    cd = crime_risk.set_index('id').to_dict('index')
    
    # Initialize the map:
    m = folium.Map(location=[34.074904, -118.376525], zoom_start=16)
    colorscale = branca.colormap.linear.RdPu_09.scale(0, np.sqrt(rfc.predict_proba(points)[:,1].max()))

    # Add the color for the chloropleth:

    folium.GeoJson(
        la_grid_geo,
        name='crime_risk',
        style_function=lambda feature: {
            'stroke': False,
            'fillOpacity' : 0.4,
            'smoothFactor':0,
            'color': colorscale(np.sqrt(cd[feature['id']]['risk'])),
            'dashArray': '1000, 100',
            'legend_name': 'Theft Risk (%)'
        }
    ).add_to(m)
    folium.LayerControl().add_to(m)
    return m


    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
   
