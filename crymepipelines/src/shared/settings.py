from datetime import datetime, timedelta
import os

from shared.db.mysql.connection import CrymePipelinesMySqlConn
from shared.db.mongo.connection import CrymePipelinesMongoConn


raw_pth = os.path.dirname((os.path.abspath(__file__)))
if "shared.zip" in raw_pth:
    BASE_DIR = os.path.abspath(raw_pth + '/..')
else:
    BASE_DIR = raw_pth

TMP_DIR = os.path.abspath(BASE_DIR + '/..') + '/tmp'
BIN_DIR = os.path.abspath(BASE_DIR + '/../..') + '/bin'


# DATABASE CONNECTIONS CONFIG
DB_URL = 'mysql://root@localhost/crymepipelines?serverTimezone=UTC'
FEEDER_DB_URL = 'mongodb://localhost:27017/crymeclarity'
CRYMEWEB_DB_URL = 'mysql://root@localhost/crymeweb?serverTimezone=UTC'

cp_conn = CrymePipelinesMySqlConn(DB_URL)
cw_conn = CrymePipelinesMySqlConn(CRYMEWEB_DB_URL)
cf_conn = CrymePipelinesMongoConn(FEEDER_DB_URL)


# CrymeFeeder Trust Delay
# often crimes are reported and uploaded to the api well after the fact, this parameter gives the feeder a buffer
# to help mitigate inaccurate feature generation and subsequent model training on samples within the delay interval.
# This parameter only applies to pipelines for model generation.
CF_TRUST_DELAY = timedelta(days=14)

# Sampling Start Date
# Data from over a year ago is not beneficial to the user experience or model performance, dont use any data
# prior to this date
START_DATE = datetime(year=2018, month=4, day=1).date()



