from datetime import datetime, timedelta
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


def build_dev_ds():
    cf = _init_cf()
    use_dt = datetime.now() - timedelta(days=7)
    cf.update_incident_records(batch_size=1000, override_ts=use_dt)


def check():
    cf = _init_cf()
    print(cf.is_data_stale())