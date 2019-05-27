# utils for the classifiers app


def datetime_to_minutes_into_day(ts):
    hours = ts.hour
    minutes = ts.minute
    return hours * 60 + minutes