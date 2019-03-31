import datetime
from pyspark.sql.types import ArrayType, StructType, IntegerType, StructField, StringType, FloatType, TimestampType, \
    DecimalType
from pyspark.sql.functions import udf
import mpu


# Define native python mappings here
def assign_coordinate_to_lat_box(latitude):
    try:
        lat_box = abs(int(latitude / (1 * .008726950000000073)))
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


# Define UDFs here
actb_lat = udf(assign_coordinate_to_lat_box, IntegerType())
actb_lon = udf(assign_coordinate_to_lon_box, IntegerType())
ts_conv = udf(cla_timestamp_to_datetime, TimestampType())
t_occ_conv = udf(time_occ_to_seconds, IntegerType())
space_dist = udf(lambda w, x, y, z: mpu.haversine_distance((w, x), (y, z)) * 0.621371, FloatType())