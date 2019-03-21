import datetime
import pymongo

from settings import DB_URL, DB_NAME
from sources.cla import CLAAPI
from .utils import cla_timestamp_to_datetime


class CrymeFeeder:
    data_source = None
    db = None
    record_threshold = 500

    def __init__(self, data_source, db):
        self.data_source = data_source
        self.db = db
        self._write_db_status()

    def _write_db_status(self):
        self.db.meta.update_one({
            '_id': 'db_state'
        }, {
            '$set': {
                'last_updated': datetime.datetime.utcnow(),
                'total_incidents_count': self.db.incidents.count_documents({}),
                'most_recently_created_at': self.db.incidents.find({}).sort(
                    [(":created_at", pymongo.DESCENDING)]).limit(1)[0][':created_at']
            }
        }, upsert=True)

    def _db_operation(func):
        def _update_meta_and_exec(self, *args, **kwargs):
            func(self, *args, **kwargs)
            self._write_db_status()

        return _update_meta_and_exec

    @_db_operation
    def _insert_new_incidents(self, incidents):
        insert_time = datetime.datetime.utcnow()

        for incident in incidents:
            incident['record_inserted_at'] = insert_time
            incident['_id'] = incident[':id']

        try:
            self.db.incidents.insert_many(incidents)
        except pymongo.errors.BulkWriteError:
            for incident in incidents:
                try:
                    self.db.incidents.insert_one(incident)
                except pymongo.errors.DuplicateKeyError:
                    continue

    def _batch_get_and_insert_incidents(self, batch_size, get_records_func, **kwargs):
        page = 0
        kwargs['limit'] = batch_size
        kwargs['offset'] = 0
        results_chunk = get_records_func(**kwargs)

        while results_chunk:
            self._insert_new_incidents(results_chunk)
            kwargs['offset'] = batch_size * page
            results_chunk = get_records_func(**kwargs)
            page += 1

    @property
    def db_most_recently_created_record(self):
        try:
            ts = self.db.meta.find({'_id': 'db_state'}).limit(1)[0]['most_recently_created_at']
        except IndexError:
            ts = '2010-01-01T00:00:00.00Z'

        return cla_timestamp_to_datetime(ts)

    def is_data_stale(self):
        most_recently_created = self.db_most_recently_created_record
        if len(self.data_source.get_incidents_created_after(most_recently_created)) > self.record_threshold:
            return True
        return False

    def update_incident_records(self, batch_size):
        most_recently_created = self.db_most_recently_created_record
        self._batch_get_and_insert_incidents(batch_size, self.data_source.get_incidents_created_after,
                                             **{'dt': most_recently_created})

    def populate_incidents(self, batch_size):
        self._batch_get_and_insert_incidents(batch_size, self.data_source.get_incidents)
