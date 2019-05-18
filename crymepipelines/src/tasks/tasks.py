import csv
from datetime import datetime, timedelta
import os
import pickle as p
from pyspark.sql.functions import monotonically_increasing_id, unix_timestamp
import shutil

from shared.objects.samples import SamplesManager
from shared.settings import CF_TRUST_DELAY, START_DATE, cf_conn, cp_conn, TMP_DIR, BIN_DIR
from .base import SparkCrymeTask, NativeCrymeTask
from .constants import safety_rel_crimes
from .mappings import (crime_occ_udf, ts_to_minutes_in_day_udf, ts_to_hour_of_day_udf, ts_to_day_of_week_udf, ts_conv,
                       crime_group_assignment_udf, t_occ_conv, actb_lat, actb_lon)
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


class EngineerFeaturesLocationTimeSamples(SparkCrymeTask, SearchForCrimesMixin):
    input_file = TMP_DIR + 'features_crime_incidents.parquet'
    output_file = TMP_DIR + 'complete_dataset.parquet'

    def run(self):
        crime_incidents = self.spark.read.parquet(self.input_file)
        loc_time_samples = self.load_df_from_cp('location_time_samples')
        # assign bounding boxes
        loc_time_samples = loc_time_samples.withColumn('lat_bb', actb_lat(loc_time_samples.latitude))
        loc_time_samples = loc_time_samples.withColumn('lon_bb', actb_lon(loc_time_samples.longitude))
        # convert datetime to unix timestamp
        loc_time_samples = loc_time_samples.withColumn('timestamp_unix', unix_timestamp(loc_time_samples.timestamp))

        loc_time_samples_full = self.find_surrounding_crimes(loc_time_samples, crime_incidents)


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


class CleanCrimeIncidents(SparkCrymeTask):
    output_file = TMP_DIR + '/clean_crime_incidents.parquet'

    def run(self):
        raw_crime_incidents = self.load_df_from_crymefeeder("incidents")
        crime_incidents = raw_crime_incidents.withColumn('date_occ', ts_conv(raw_crime_incidents.date_occ))
        crime_incidents = crime_incidents.filter(crime_incidents.date_occ > datetime.now().date() - timedelta(days=365))
        crime_incidents = crime_incidents.filter(crime_incidents.crm_cd.isin(list(safety_rel_crimes.keys())))
        crime_incidents = crime_incidents.withColumn('lon', crime_incidents.location_1.coordinates[0])
        crime_incidents = crime_incidents.withColumn('lat', crime_incidents.location_1.coordinates[1])
        crime_incidents = crime_incidents.select(
            ['_id', 'crm_cd', 'crm_cd_desc', 'date_occ', 'time_occ', 'premis_desc', 'lon', 'lat']
        )
        crime_incidents.write.parquet(self.output_file)


class AddFeaturesToCrimeIncidents(SparkCrymeTask):
    input_file = TMP_DIR + '/clean_crime_incidents.parquet'
    output_file = TMP_DIR + '/features_crime_incidents.parquet'

    def run(self):
        crime_incidents = self.spark.read.parquet(self.input_file)
        crime_incidents = crime_incidents.withColumn('crm_grp', crime_group_assignment_udf(crime_incidents.crm_cd))
        crime_incidents = crime_incidents.withColumn('time_occ_seconds', t_occ_conv(crime_incidents.time_occ))
        crime_incidents = crime_incidents.withColumn('date_occ_unix', unix_timestamp(crime_incidents.date_occ))
        crime_incidents = crime_incidents.withColumn('lat_bb_c', actb_lat(crime_incidents.lat))
        crime_incidents = crime_incidents.withColumn('lon_bb_c', actb_lon(crime_incidents.lon))
        crime_incidents = crime_incidents.withColumn(
            'ts_occ_unix', crime_incidents.date_occ_unix + crime_incidents.time_occ_seconds
        )
        crime_incidents.write.parquet(self.output_file)


class PipeRecentCrimeIncidents(SparkCrymeTask):
    input_file = TMP_DIR + '/clean_crime_incidents.parquet'

    def run(self):
        crime_incidents = self.spark.read.parquet(self.input_file)
        crime_incidents = crime_incidents.filter(crime_incidents.date_occ > datetime.now().date() - timedelta(days=30))

        crime_incidents = crime_incidents.withColumn("id", monotonically_increasing_id())
        crime_incidents = crime_incidents.withColumn("date_occ_str", crime_incidents.date_occ.cast("string"))
        crime_incidents = crime_incidents.withColumnRenamed("_id", "row_id")

        self.write_to_cw(crime_incidents, 'crime_crimeincident')


class AggregateCrimeVolumes(SparkCrymeTask):
    input_file = TMP_DIR + '/clean_crime_incidents.parquet'

    def run(self):
        crime_incidents = self.spark.read.parquet(self.input_file)
        crime_incidents = crime_incidents.filter(crime_incidents.date_occ > datetime.now().date() - timedelta(days=30))

        by_date = crime_incidents.groupBy('date_occ').agg({'_id': 'count'}).orderBy("date_occ", ascending=True)

        by_date = by_date.withColumn("id", monotonically_increasing_id())
        by_date = by_date.withColumn("date_occ_str", by_date.date_occ.cast("string"))
        by_date = by_date.withColumnRenamed("count(_id)", "volume")
        by_date = by_date.select(
            ['date_occ_str', 'volume', 'id']
        )

        self.write_to_cw(by_date, 'crime_dailycrimevolume')


class CrimesByPremises(SparkCrymeTask):
    input_file = TMP_DIR + '/clean_crime_incidents.parquet'

    def run(self):
        crime_incidents = self.spark.read.parquet(self.input_file)
        crime_incidents = crime_incidents.filter(crime_incidents.date_occ > datetime.now().date() - timedelta(days=30))

        by_type = crime_incidents.groupBy('premis_desc').agg({'_id': 'count'}).orderBy("count(_id)", ascending=False)
        by_type = by_type.withColumn("id", monotonically_increasing_id())
        by_type = by_type.withColumnRenamed("count(_id)", "volume")

        self.write_to_cw(by_type.limit(10), 'crime_crimespremisesvolume')








