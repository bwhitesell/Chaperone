import datetime
import mpu
from pyspark.sql.functions import udf
from pyspark.sql.types import IntegerType, StringType, FloatType, TimestampType
import random

from .constants import crime_group_mapping


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


def add_noise_to_lon(longitude):
    return longitude + random.uniform(-1, 1) * 0.007254180000003885/2


def add_noise_to_lat(latitude):
    return latitude + random.uniform(-1, 1) * 0.004363475000000037/2


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
crime_group_assignment_udf = udf(lambda x: crime_group_mapping.get(int(x), 'Other'), StringType())
add_noise_to_lat_udf = udf(add_noise_to_lat, FloatType())
add_noise_to_lon_udf = udf(add_noise_to_lon, FloatType())


# Misc. Utils
def row_to_list(row):
    return [
        row.id,
        row.latitude,
        row.longitude,
        row.timestamp,
        row.lat_bb,
        row.lon_bb,
        row.timestamp_unix,
        row.n_ab,
        row.n_b,
        row.n_t,
        row.n_btv,
        row.n_vbbs,
        row.n_pdt,
        row.n_ltvc,
        row.n_sp,
        row.n_mio,
        row.n_r,
        row.time_minutes,
        row.day_of_week,
    ]
