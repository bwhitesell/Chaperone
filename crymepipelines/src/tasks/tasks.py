import csv
from datetime import datetime, timedelta
import os
import pickle as p
import shutil

from shared.objects.samples import SamplesManager
from shared.settings import CF_TRUST_DELAY, START_DATE, cf_conn, cp_conn, TMP_DIR, BIN_DIR
from .base import BaseCrymeTask
from .mixins import SearchForCrimesMixin
from .mappings import crime_occ_udf, ts_to_minutes_in_day_udf, ts_to_hour_of_day_udf, ts_to_day_of_week_udf


class GenerateLocationTimeSamples(BaseCrymeTask):
    def run(self):
        sm = SamplesManager()
        cf_freshness = cf_conn.get_recency_data()
        update_date = (cf_freshness - CF_TRUST_DELAY).date()
        # check the update date before running.
        if (update_date < datetime.now().date()) and (update_date > START_DATE):
            sm.update_samples(update_date)
        else:
            raise ValueError('Invalid Update Date Specified.')


class BuildDataset(SearchForCrimesMixin):
    output_file = TMP_DIR + '/features.parquet'

    def run(self):
        events_sample = self.load_df_from_db('location_time_samples')
        features_ds = self.search_for_crimes(events_sample)
        features_ds.write.parquet(TMP_DIR + '/features.parquet')


class CleanDataset(BaseCrymeTask):
    input_file = TMP_DIR + '/features.parquet'
    output_file = TMP_DIR + '/features_clean.parquet'

    def run(self):
        df = self.spark.read.parquet(self.input_file)
        df = df.fillna(0, subset=['count'])  # fill none values with 0.
        df.write.parquet(self.output_file)
        shutil.rmtree(self.input_file)


class EngineerFeatures(BaseCrymeTask):
    input_file = TMP_DIR + '/features_clean.parquet'
    output_file = TMP_DIR + '/final_dataset.csv'

    def run(self):
        df = self.spark.read.parquet(self.input_file)
        df = df.withColumn('crime_occ', crime_occ_udf(df['count']))
        df = df.withColumn('time_minutes', ts_to_minutes_in_day_udf(df.timestamp))
        df = df.withColumn('hour', ts_to_hour_of_day_udf(df.timestamp))
        df = df.withColumn('day_of_week', ts_to_day_of_week_udf(df.timestamp))
        df = df.collect()
        with open(self.output_file, 'w') as output:
            writer = csv.writer(output, delimiter=',',)
            writer.writerow(
                ['id', 'latitude', 'longitude', 'timestamp', 'lat_bb', 'lon_bb',
                 'timestamp_unix', 'count', 'crime_occ', 'time_minutes', 'day_of_week']
            )  # headers
            for row in df:
                writer.writerow(self.row_to_list(row))

        shutil.rmtree(self.input_file)

    @staticmethod
    def row_to_list(row):
        return [
            row.id,
            row.latitude,
            row.longitude,
            row.timestamp,
            row.lat_bb,
            row.lon_bb,
            row.timestamp_unix,
            row.count,
            row.crime_occ,
            row.time_minutes,
            row.day_of_week,
        ]


class TrainCrymeClassifier(BaseCrymeTask):
    task_type = 'single'
    input_file = TMP_DIR + '/final_dataset.csv'
    output_file = BIN_DIR + '/cryme_classifier_' + str(datetime.now().date()) + '.p'

    def run(self):
        import pandas as pd
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import log_loss
        features = ['longitude', 'latitude', 'time_minutes', 'day_of_week']
        target = 'crime_occ'

        data = pd.read_csv(self.input_file)
        ts_end = cf_conn.get_recency_data() - CF_TRUST_DELAY - timedelta(days=15)
        ts_start = str(ts_end - timedelta(days=300))
        ts_end = str(ts_end)

        train_ds = data[(data.timestamp > ts_start) & (data.timestamp < ts_end)]
        test_ds = data[(data.timestamp > ts_end)]
        rfc = RandomForestClassifier(max_depth=10, n_estimators=500, n_jobs=-1)
        rfc.fit(train_ds[features], train_ds[target])
        y_est = rfc.predict_proba(test_ds[features])
        ll = log_loss(test_ds[target], y_est)
        print(ll)
        p.dump(rfc, open(self.output_file, 'wb'))
        os.remove(self.input_file)
