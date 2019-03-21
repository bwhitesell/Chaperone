import pymongo

from feeder import crymefeeder
from sources.cla import CLAAPI
from settings import SOCRATA_APP_TOKEN, DB_NAME, DB_URL


def _init_cf():
    api = CLAAPI(token=SOCRATA_APP_TOKEN)
    db = pymongo.MongoClient(DB_URL)[DB_NAME]
    cf = crymefeeder.CrymeFeeder(api, db)
    return cf


def populate_data():
    cf = _init_cf()
    cf.populate_incidents(batch_size=10000)


def update_data():
    cf = _init_cf()
    if cf.is_data_stale():
        cf.update_incident_records(batch_size=10000)


def check():
    cf = _init_cf()
    print(cf.is_data_stale())