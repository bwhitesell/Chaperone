from datetime import datetime
import pymongo

from settings import FEEDER_DB_URL


class CrymePipelinesMongoConn:
    """
      A Wrapping class around the mongoclient object to improve resilience of the pipelines
      and manage the config around connection setup.
    """
    def __init__(self):
        self._establish_connection()

    def _establish_connection(self):
        self.mc_client = pymongo.MongoClient(FEEDER_DB_URL)['crymeclarity']

    def get_recency_data(self):
        return self.cla_timestamp_to_datetime(
            self.mc_client.meta.find_one({'_id': 'db_state'})['most_recently_created_at']
        )

    @staticmethod
    def cla_timestamp_to_datetime(cla_ts):
        return datetime.strptime(cla_ts, '%Y-%m-%dT%H:%M:%S.%fZ')
