import datetime
import pymongo
from settings import DB_URL, DB_NAME
from utils import cla_timestamp_to_datetime


class CrymeFeeder:
    data_source = None
    db = None
    record_threshold = 500

    def __init__(self, data_source):
        self.data_source = data_source
        # initiate db conn on instantiation of the object.
        self.db = pymongo.MongoClient(DB_URL)[DB_NAME]

    def _write_db_status(self):
        self.db.meta.update_one({
            '_id': 'db_state'
        }, {
            '$set': {
                'last_updated': datetime.datetime.utcnow(),
                'total_incidents_count': self.db.incidents.count_documents({}),
                'most_recently_created_at': self.db.incidents.find({}).sort(
                    [("created_at", pymongo.DESCENDING)]).limit(1)[0][':created_at']
            }
        }, upsert=True)

    def _batch_update(self, get_records_func, batch_size, **kwargs):
        results_chunk = True
        page = 0

        while results_chunk:
            kwargs['limit'] = batch_size
            kwargs['offset'] = batch_size * page
            results_chunk = get_records_func(**kwargs, )

    @property
    def db_most_recently_created_record(self):
        return  cla_timestamp_to_datetime(
            self.db.meta.find({'_id': 'db_state'})[0]['most_recently_created_at']
        )

    def is_data_stale(self):
        most_recently_created = self.db_most_recently_created_record
        if len(self.data_source.get_incidents_created_after(most_recently_created)) > self.record_threshold:
            return True
        return False

    def insert_new_incidents(self, incidents):
        insert_time = datetime.datetime.utcnow()
        for incident in incidents:
            incident['record_inserted_at'] = insert_time
        self.db.incidents.insert_many(incidents)

    def update_incident_records(self):
        most_recently_created = self.db_most_recently_created_record
        results_chunk = True
        page = 0

        while results_chunk:
            results_chunk = self.data_source.get_incidents_created_after(most_recently_created)
            self.insert_new_incidents(results_chunk)
            page += 1

        self._write_db_status()

    def get_all_historical_incidents(self, batch_size):
        results_chunk = True
        page = 0

        while results_chunk:
            results_chunk = self.data_source.get_incidents(limit=batch_size, offset=batch_size * page)
            self.insert_new_incidents(results_chunk)
            page += 1

        self._write_db_status()
