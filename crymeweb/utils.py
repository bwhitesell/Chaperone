import pymongo
from pymongo.errors import CursorNotFound, AutoReconnect, ConnectionFailure


class SafeMongoConnectionFailure(Exception):
    def __str__(self):
        return 'Failed to connect to mongodb'


class SafeMongoClientWrapper:
    """ A Wrapping class to make the mongo-client object more robust to connection issues for the web app. """
    def __init__(self, db_url, db_name, max_retries=10):
        self.db_url = db_url
        self.db_name = db_name
        self.max_retries = max_retries
        self._establish_connection()

    def _establish_connection(self):
        self.mc_client = pymongo.MongoClient(self.db_url)[self.db_name]

    def execute(self, collection, function, *args, **kwargs):
            try_n = 0
            while try_n < self.max_retries:
                try:
                    return getattr(getattr(self.mc_client, collection), function)(*args, **kwargs)
                except (CursorNotFound, ConnectionFailure, AutoReconnect):
                    self._establish_connection()
                    try_n += 1
            raise SafeMongoConnectionFailure
