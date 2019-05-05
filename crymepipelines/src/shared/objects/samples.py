from datetime import date, datetime, timedelta
import random

from shared.settings import cp_conn, START_DATE
from .geometries import GeometricRegion


class SamplesManager:
    start_date = START_DATE

    def __init__(self):
        self.gd = GeometricRegion(id=1)

    def update_samples(self, date_arg):
        # we need some argument checking to ensure sample reliability.
        if type(date_arg) != date:
            raise ValueError('Invalid type for argument "date_arg"')
        if date_arg < START_DATE:
            raise ValueError('Invalid Start Date Provided. Too Early.')

        samples_recency = self.get_samples_recency()
        if date_arg <= samples_recency:
            raise ValueError(f'Samples already updated to {samples_recency}')

        # argument checking done, now perform operation
        n_days = (date_arg - samples_recency).days
        for day in range(1, n_days):
            add_date = samples_recency + timedelta(days=day)
            self._add_samples(add_date)
            print(f'Generated samples for {add_date}.')

    def get_samples_recency(self):
        with cp_conn.cursor() as cursor:
            cursor.execute('SELECT max(timestamp) as "updated" FROM location_time_samples;')
            resp = cursor.fetchone()['updated']
        if not resp:
            return self.start_date
        else:
            return resp.date()

    def _add_samples(self, date_arg, n_samples=500):
        min_lat, max_lat, min_long, max_long = self.gd.get_bounding_box()
        valid_samples = self._generate_location_times(min_lat, max_lat, min_long, max_long, date_arg, n_samples)
        self._save_samples(valid_samples)

    def _generate_location_times(self, min_lat, max_lat, min_long, max_long, date_arg, n_samples):
        samples = []
        length = 0
        dt_date_arg = datetime.combine(date_arg, datetime.min.time())
        while length < n_samples:
            lat = random.uniform(min_lat, max_lat)
            long = random.uniform(min_long, max_long)
            if self.gd.in_domain(long, lat):
                ts = dt_date_arg - timedelta(
                    hours=random.uniform(0, 24))
                samples.append({
                    'longitude': long,
                    'latitude': lat,
                    'timestamp': ts
                })
                length = len(samples)
        return samples

    @staticmethod
    def _save_samples(samples):
        with cp_conn.cursor() as cursor:
            for sample in samples:
                cursor.execute(f'''
                    INSERT INTO location_time_samples (latitude, longitude, timestamp)
                      VALUES ({sample['latitude']}, {sample['longitude']}, "{sample['timestamp']}");
                ''')
            cp_conn.conn.commit()
