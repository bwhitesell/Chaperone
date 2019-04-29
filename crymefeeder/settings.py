import os

SOCRATA_APP_TOKEN = os.environ.get('SOCRATA_APP_TOKEN')

DB_URL = os.environ.get('DB_URL')
DB_NAME = os.environ.get('DB_NAME')


REQUEST_TIMEOUT_LIMIT = 30

# The minimum number of new records available from a data source before crymefeeder should attempt to re-sync.
RECORD_THRESHOLD = 10