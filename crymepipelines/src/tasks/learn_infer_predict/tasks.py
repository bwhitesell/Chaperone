import csv
from datetime import datetime, timedelta
import pickle as p
from pyspark.sql.functions import unix_timestamp

from shared.settings import CF_TRUST_DELAY, START_DATE, cf_conn, cp_conn, TMP_DIR, BIN_DIR
from ..base import SparkCrymeTask, NativeCrymeTask
from ..constants import safety_rel_crimes, cc_hyperparams
from ..mappings import (ts_to_minutes_in_day_udf, ts_to_hour_of_day_udf, ts_to_day_of_week_udf, ts_conv,
                       crime_group_assignment_udf, t_occ_conv, actb_lat, actb_lon, row_to_list)
from ..mixins import SearchForCrimesMixin


class EngineerFeaturesLocationTimeSamples(SparkCrymeTask, SearchForCrimesMixin):
    input_file = TMP_DIR + '/features_crime_incidents.parquet'
    output_file = TMP_DIR + '/complete_dataset.csv'

    def run(self):
        crime_incidents = self.spark.read.parquet(self.input_file)
        loc_time_samples = self.load_df_from_cp('location_time_samples')
        loc_time_samples = loc_time_samples.withColumn('lat_bb', actb_lat(loc_time_samples.latitude))
        loc_time_samples = loc_time_samples.withColumn('lon_bb', actb_lon(loc_time_samples.longitude))
        loc_time_samples = loc_time_samples.withColumn('timestamp_unix', unix_timestamp(loc_time_samples.timestamp))

        dataset = self.find_surrounding_crimes(loc_time_samples, crime_incidents)

        dataset = dataset.withColumn('time_minutes', ts_to_minutes_in_day_udf(dataset.timestamp))
        dataset = dataset.withColumn('hour', ts_to_hour_of_day_udf(dataset.timestamp))
        dataset = dataset.withColumn('day_of_week', ts_to_day_of_week_udf(dataset.timestamp))
        dataset = dataset.collect()

        with open(self.output_file, 'w') as output:
            writer = csv.writer(output, delimiter=',',)
            writer.writerow(
                ['id', 'latitude', 'longitude', 'timestamp', 'lat_bb', 'lon_bb', 'timestamp_unix', 'n_ab',
                 'n_b', 'n_t', 'n_btv', 'n_vbbs', 'n_pdt', 'n_ltvc', 'n_sp', 'n_mio', 'n_r', 'time_minutes',
                 'day_of_week']
            )  # headers
            for row in dataset:
                writer.writerow(row_to_list(row))


class EngineerFeaturesDailyLocationTimeSamples(SparkCrymeTask, SearchForCrimesMixin):
    input_file = TMP_DIR + '/features_crime_incidents.parquet'
    output_file = TMP_DIR + '/daily_dataset.csv'

    def run(self):
        cf_freshness = cf_conn.get_recency_data()
        update_date = (cf_freshness - CF_TRUST_DELAY).date()
        if (update_date >= datetime.now().date()) or (update_date < START_DATE):
            raise ValueError('Invalid Update Date Specified.')

        crime_incidents = self.spark.read.parquet(self.input_file)

        loc_time_samples = self.load_df_from_cp('location_time_samples')
        loc_time_samples = loc_time_samples.filter(loc_time_samples.timestamp < update_date + timedelta(days=1))
        loc_time_samples = loc_time_samples.filter(loc_time_samples.timestamp > update_date)
        loc_time_samples = loc_time_samples.withColumn('lat_bb', actb_lat(loc_time_samples.latitude))
        loc_time_samples = loc_time_samples.withColumn('lon_bb', actb_lon(loc_time_samples.longitude))
        loc_time_samples = loc_time_samples.withColumn('timestamp_unix', unix_timestamp(loc_time_samples.timestamp))

        dataset = self.find_surrounding_crimes(loc_time_samples, crime_incidents)
        dataset = dataset.withColumn('time_minutes', ts_to_minutes_in_day_udf(dataset.timestamp))
        dataset = dataset.withColumn('hour', ts_to_hour_of_day_udf(dataset.timestamp))
        dataset = dataset.withColumn('day_of_week', ts_to_day_of_week_udf(dataset.timestamp))
        print(dataset.count())
        dataset = dataset.collect()

        with open(self.output_file, 'w') as output:
            writer = csv.writer(output, delimiter=',', )
            writer.writerow(
                ['id', 'latitude', 'longitude', 'timestamp', 'lat_bb', 'lon_bb', 'timestamp_unix', 'n_ab',
                 'n_b', 'n_t', 'n_btv', 'n_vbbs', 'n_pdt', 'n_ltvc', 'n_sp', 'n_mio', 'n_r', 'time_minutes',
                 'day_of_week']
            )  # headers
            for row in dataset:
                writer.writerow(row_to_list(row))


class TrainCrymeClassifiers(NativeCrymeTask):
    input_file = TMP_DIR + '/complete_dataset.csv'
    output_file = BIN_DIR + '/cryme_classifier_' + str(datetime.now().date())

    def run(self):
        data = self._local_mod_access['pandas'].read_csv(self.input_file)
        ts_end = cf_conn.get_recency_data() - CF_TRUST_DELAY - timedelta(days=15)
        ts_start = str(ts_end - timedelta(days=300))
        ts_end = str(ts_end)

        train_ds = data[(data.timestamp > ts_start) & (data.timestamp < ts_end)]
        test_ds = data[(data.timestamp > ts_end)]

        features = ['longitude', 'latitude', 'time_minutes']
        for target in ['n_ab', 'n_b', 'n_t', 'n_btv', 'n_vbbs', 'n_pdt', 'n_ltvc', 'n_sp', 'n_mio', 'n_r']:

            rfc = self._local_mod_access['LGBMClassifier'](**cc_hyperparams[target])
            rfc.fit(train_ds[features], train_ds[target])
            y_est = rfc.predict_proba(test_ds[features])
            ll = self._local_mod_access['log_loss'](test_ds[target], y_est)

            bin_file_name = self.output_file + '_' + target+'.p'
            p.dump(rfc, open(bin_file_name, 'wb'))

            cursor = cp_conn.cursor()
            cursor.execute(
                f'CALL AddNewModel("{target}", {round(ll, 4)}, {train_ds.shape[0]}, {test_ds.shape[0]}, "{bin_file_name}")'
            )
            cp_conn.conn.commit()
            print(f'Classifier for {target} trained and exported.')


class EvalCrymeClassifiers(NativeCrymeTask):
    input_file = TMP_DIR + '/daily_dataset.csv'

    def run(self):
        features = ['longitude', 'latitude', 'time_minutes']
        target = 'crime_occ'

        df = self._local_mod_access['pandas'].read_csv(self.input_file)
        cursor = cp_conn.cursor()
        cursor.execute('SELECT * FROM cryme_classifiers;')
        models = cursor.fetchall()

        for model in models:
            target = model['target']
            model_obj = p.load(open(model['saved_to'], 'rb'))
            y_est = model_obj.predict_proba(df[features])
            ll = self._local_mod_access['log_loss'](df[target], y_est)

            cursor.execute(
                f'CALL eval_model({model["id"]}, {round(ll, 6)}, {df.shape[0]}, "{(cf_conn.get_recency_data() - CF_TRUST_DELAY).date()}")'
            )
            cp_conn.conn.commit()
