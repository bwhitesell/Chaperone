import datetime
import pymongo
from settings import DB_URL, DB_NAME


class CrymeFeeder:
    data_source = None
    db = None

    def __init__(self, data_source):
        self.data_source = data_source
        # initiate db conn on instantiation of the object.
        self.db = pymongo.MongoClient(DB_URL)[DB_NAME]

    def is_data_stale(self):
        last_updated_date = self.db.meta.findOne({'_id': 'db_state'})[0]['most_recently_created_at']
        self.data_source.get_incidents_created_after(last_update_date)
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

    def insert_new_incidents(self, incidents):
        insert_time = datetime.datetime.utcnow()
        for incident in incidents:
            incident['record_inserted_at'] = insert_time
        self.db.incidents.insert_many(incidents)

    def get_all_historical_data(self, batch_size):
        results_chunk = True
        page = 0

        while results_chunk:
            results_chunk = self.data_source.get_incidents(limit=batch_size, offset=batch_size * page)
            self.insert_new_incidents(results_chunk)
            page += 1

        self._write_db_status()

