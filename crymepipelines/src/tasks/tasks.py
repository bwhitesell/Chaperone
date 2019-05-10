import csv
from datetime import datetime, timedelta
import os
import pickle as p
import shutil

from shared.objects.samples import SamplesManager
from shared.settings import CF_TRUST_DELAY, START_DATE, cf_conn, cp_conn, TMP_DIR, BIN_DIR
from .base import SparkCrymeTask, NativeCrymeTask
from .mappings import crime_occ_udf, ts_to_minutes_in_day_udf, ts_to_hour_of_day_udf, ts_to_day_of_week_udf
from .mixins import SearchForCrimesMixin


class GenerateLocationTimeSamples(NativeCrymeTask):

    def run(self):
        sm = SamplesManager()
        cf_freshness = cf_conn.get_recency_data()
        update_date = (cf_freshness - CF_TRUST_DELAY).date()
        # check the update date before running.
        if (update_date < datetime.now().date()) and (update_date > START_DATE):
            sm.update_samples(update_date)
        else:
            raise ValueError('Invalid Update Date Specified.')


class BuildFullDataset(SearchForCrimesMixin):
    output_file = TMP_DIR + '/features.parquet'

    def run(self):
        events_sample = self.load_df_from_db('location_time_samples')
        features_ds = self.search_for_crimes(events_sample)
        features_ds.write.parquet(TMP_DIR + '/features.parquet')


class BuildRecentDataset(SearchForCrimesMixin):
    output_file = TMP_DIR + '/features.parquet'

    def run(self):
        cf_freshness = cf_conn.get_recency_data()
        update_date = (cf_freshness - CF_TRUST_DELAY).date()
        if (update_date >= datetime.now().date()) or (update_date < START_DATE):
            raise ValueError('Invalid Update Date Specified.')

        events_sample = self.load_df_from_db('location_time_samples')
        events_sample = events_sample.filter(events_sample.timestamp < update_date + timedelta(days=1))
        events_sample = events_sample.filter(events_sample.timestamp > update_date)
        features_ds = self.search_for_crimes(events_sample)
        features_ds.write.parquet(TMP_DIR + '/features.parquet')


class CleanDataset(SparkCrymeTask):
    input_file = TMP_DIR + '/features.parquet'
    output_file = TMP_DIR + '/features_clean.parquet'

    def run(self):
        df = self.spark.read.parquet(self.input_file)
        df = df.fillna(0, subset=['count'])  # fill none values with 0.
        df.write.parquet(self.output_file)
        shutil.rmtree(self.input_file)


class EngineerFeatures(SparkCrymeTask):
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


class TrainCrymeClassifier(NativeCrymeTask):
    input_file = TMP_DIR + '/final_dataset.csv'
    output_file = BIN_DIR + '/cryme_classifier_' + str(datetime.now().date()) + '.p'

    def run(self):

        features = ['longitude', 'latitude', 'time_minutes', 'day_of_week']
        target = 'crime_occ'

        data = self._local_mod_access['pandas'].read_csv(self.input_file)
        ts_end = cf_conn.get_recency_data() - CF_TRUST_DELAY - timedelta(days=15)
        ts_start = str(ts_end - timedelta(days=300))
        ts_end = str(ts_end)

        train_ds = data[(data.timestamp > ts_start) & (data.timestamp < ts_end)]
        test_ds = data[(data.timestamp > ts_end)]
        rfc = self._local_mod_access['RandomForestClassifier'](max_depth=10, n_estimators=500, n_jobs=-1)
        rfc.fit(train_ds[features], train_ds[target])
        y_est = rfc.predict_proba(test_ds[features])
        ll = self._local_mod_access['log_loss'](test_ds[target], y_est)

        p.dump(rfc, open(self.output_file, 'wb'))
        os.remove(self.input_file)

        cursor = cp_conn.cursor()
        cursor.execute(
            f'CALL AddNewModel({round(ll, 2)}, {train_ds.shape[0]}, {test_ds.shape[0]}, "{self.output_file}")'
        )
        cp_conn.conn.commit()


class EvalCrymeClassifier(NativeCrymeTask):
    input_file = TMP_DIR + '/final_dataset.csv'

    def run(self):
        features = ['longitude', 'latitude', 'time_minutes', 'day_of_week']
        target = 'crime_occ'

        df = self._local_mod_access['pandas'].read_csv(self.input_file)
        cursor = cp_conn.cursor()
        cursor.execute('SELECT * FROM cryme_classifiers;')
        models = cursor.fetchall()
        for model in models:
            model_obj = p.load(open(model['saved_to'], 'rb'))
            y_est = model_obj.predict_proba(df[features])
            ll = self._local_mod_access['log_loss'](df[target], y_est)

            cursor.execute(
                f'CALL eval_model({model["id"]}, {round(ll, 2)}, {df.shape[0]}, "{(cf_conn.get_recency_data() - CF_TRUST_DELAY).date()}")'
            )
            cp_conn.conn.commit()







