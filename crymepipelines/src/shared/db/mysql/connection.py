import pymysql
import time
from urllib.parse import urlparse


class CrymePipelinesMySqlConn:
    """
      A Wrapping class around the pymysql connection object to improve resilience of the pipelines
      and manage the config around connection setup.
    """
    def __init__(self, uri):
        self.conn = None
        self.uri = uri
        self.connect()

    def connect(self):
        conn_params = urlparse(self.uri)
        self.conn = pymysql.connect(
            host=conn_params.hostname,
            port=conn_params.port,
            database=conn_params.path.replace('/', ''),
            user=conn_params.username,
            password=conn_params.password,
            cursorclass=pymysql.cursors.DictCursor,
        )

    def cursor(self, *args, **kwargs):

        try:
            return self.conn.cursor()
        except Exception:
            try:
                self._reconnect()
                return self.conn.cursor()
            except Exception as e:
                raise e

    def _reconnect(self, attempts=10, timeout=30):
        attempt = 0
        start_time = time.time()

        while attempt < attempts or time.time() - start_time > timeout:
            try:
                self.connect()
                break
            except Exception:
                attempt += 1

        if attempt == attempts:
            raise Exception("Unable to connect to db.")


