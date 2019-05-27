# utils for the classifiers app


lat_delta = 0.004363475000000037/2
lon_delta = 0.007254180000003885/2


def datetime_to_minutes_into_day(ts):
    hours = ts.hour
    minutes = ts.minute
    return hours * 60 + minutes


def build_view_box(lon, lat):
    return {
        'point_lat': lat,
        'point_lon': lon,
        'bl_lat': lat + lat_delta,
        'bl_lon': lon - lon_delta,
        'tr_lat': lat - lat_delta,
        'tr_lon': lon + lon_delta,
    }

