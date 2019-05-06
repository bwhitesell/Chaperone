from datetime import datetime, timedelta
import os


BASE_DIR = os.path.dirname((os.path.abspath(__file__)))
TMP_DIR = os.path.abspath(BASE_DIR + '/..') + '/tmp'
BIN_DIR = os.path.abspath(BASE_DIR + '/..') + '/bin'

DB_URL = os.environ.get('CRYMEPIPELINES_DB_URL')
FEEDER_DB_URL = os.environ.get('CRYMEFEEDER_DB_URL')
CRYMEWEB_DB_URL = os.environ.get('CRYMEWEB_DB_URL')

# CrymeFeeder Trust Delay
# often crimes are reported and uploaded to the api well after the fact, this parameter gives the feeder a buffer
# to help mitigate inaccurate feature generation and subsequent model training on samples within the delay interval.
# This parameter only applies to pipelines for model generation.
CF_TRUST_DELAY = timedelta(days=14)

# Sampling Start Date
# Data from over a year ago is not beneficial to the user experience or model performance, dont use any data
# prior to this date
START_DATE = datetime(year=2018, month=4, day=1).date()


from shared.db.mysql.connection import CrymePipelinesMySqlConn
from shared.db.mongo.connection import CrymePipelinesMongoConn

cp_conn = CrymePipelinesMySqlConn()
cf_conn = CrymePipelinesMongoConn()


