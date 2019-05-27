# utils for the classifiers app


def datetime_to_minutes_into_day(ts):
    hours = ts.hour
    minutes = ts.minute
    return hours * 60 + minutes


def build_view_box(lon, lat):
    return {
        'point_lat': lat,
        'point_lon': lon,
        'bl_lat': lat + 0.004363475000000037,
        'bl_lon': lon - 0.007254180000003885,
        'tr_lat': lat - 0.004363475000000037,
        'tr_lon': lon + 0.007254180000003885,
    }
