import datetime


def cla_timestamp_to_datetime(cla_ts):
    return datetime.datetime.strptime(cla_ts, '%Y-%m-%dT%H:%M:%S.%fZ')
