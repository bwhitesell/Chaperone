import csv
from datetime import datetime, timedelta
import pickle as p
from pyspark.sql.functions import unix_timestamp

from shared.settings import (CF_TRUST_DELAY, START_DATE, MODEL_TRAIN_DATE_START, MODEL_TRAIN_DATE_END, cf_conn, cp_conn,
                             cw_conn, TMP_DIR, BIN_DIR)
from ..base import SparkCrymeTask, NativeCrymeTask
from ..constants import cc_hyperparameters
from ..mappings import (ts_to_minutes_in_day_udf, ts_to_hour_of_day_udf, ts_to_day_of_week_udf, ts_conv,
                       crime_group_assignment_udf, t_occ_conv, actb_lat, actb_lon, row_to_list, add_noise_to_lon_udf,
                        add_noise_to_lat_udf)
from ..mixins import SearchForCrimesMixin


class EngineerFeaturesLocationTimeSamples(SparkCrymeTask, SearchForCrimesMixin):
    input_file = TMP_DIR + '/features_crime_incidents.parquet'
    output_file = TMP_DIR + '/complete_dataset.csv'

    def run(self):
        crime_incidents = self.spark.read.parquet(self.input_file)
        crime_incidents = crime_incidents.withColumn('lat', add_noise_to_lat_udf(crime_incidents.lat))
        crime_incidents = crime_incidents.withColumn('lon', add_noise_to_lon_udf(crime_incidents.lon))

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


class EngineerFeaturesEvalTimeSamples(SparkCrymeTask, SearchForCrimesMixin):
    input_file = TMP_DIR + '/features_crime_incidents.parquet'
    output_file = TMP_DIR + '/eval_dataset.csv'

    def run(self):
        cf_freshness = cf_conn.get_recency_data()
        update_date = (cf_freshness - CF_TRUST_DELAY).date()
        if (update_date >= datetime.now().date()) or (update_date < START_DATE):
            raise ValueError('Invalid Update Date Specified.')

        crime_incidents = self.spark.read.parquet(self.input_file)
        crime_incidents = crime_incidents.filter(crime_incidents.date_occ > MODEL_TRAIN_DATE_END - timedelta(days=1))

        loc_time_samples = self.load_df_from_cp('location_time_samples')
        loc_time_samples = loc_time_samples.filter(loc_time_samples.timestamp < update_date + timedelta(days=1))
        loc_time_samples = loc_time_samples.filter(loc_time_samples.timestamp > MODEL_TRAIN_DATE_END)
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
        ts_start = str(MODEL_TRAIN_DATE_START)
        ts_end = str(MODEL_TRAIN_DATE_END)

        train_ds = data[(data.timestamp > ts_start) & (data.timestamp < ts_end)]
        test_ds = data[(data.timestamp > ts_end)]

        features = ['longitude', 'latitude', 'time_minutes']
        for target in ['n_ab', 'n_b', 'n_t', 'n_btv', 'n_vbbs', 'n_pdt', 'n_ltvc', 'n_sp', 'n_mio', 'n_r']:

            rfc = self._local_mod_access['CalibratedClassifierCV'](**cc_hyperparameters[target])
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
    input_file = TMP_DIR + '/eval_dataset.csv'

    def run(self):
        features = ['longitude', 'latitude', 'time_minutes']
        target = 'crime_occ'

        df = self._local_mod_access['pandas'].read_csv(self.input_file)
        df['day'] = df.timestamp.apply(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S').date())
        numpy = self._local_mod_access['numpy']
        cursor = cp_conn.cursor()
        cursor.execute('SELECT * FROM cryme_classifiers;')
        models = cursor.fetchall()

        perf_df = None

        for model in models:
            target = model['target']
            model_obj = p.load(open(model['saved_to'], 'rb'))

            preds = model_obj.predict_proba(df[features])
            err = 'log_loss_' + target
            df['preds_neg'] = preds[:, 0]
            df['preds_pos'] = preds[:, 1]
            df[err] = -1 * ((1 - df[target]) * numpy.log(df.preds_neg) + (df[target]) * numpy.log(df.preds_pos))
            df.loc[:, err] = df[err].fillna(0)
            grp_df = df.groupby('day')[err].mean().reset_index()

            if perf_df is not None:
                perf_df = perf_df.merge(grp_df, how='left', on='day')
            else:
                perf_df = grp_df

        # write to webdb
        cur = cw_conn.cursor()
        for t, row in enumerate(perf_df.values):
            ins_str = f"REPLACE INTO classifiers_modelperformance (id, day, log_loss_n_ab, log_loss_n_b, log_loss_n_t," + \
            f"log_loss_n_btv, log_loss_n_vbbs, log_loss_n_pdt, log_loss_n_ltvc, log_loss_n_sp," + \
            f"""log_loss_n_mio, log_loss_n_r) VALUES ({t}, "{row[0]}", {row[1]}, {row[2]}, {row[3]}, {row[4]},""" + \
            f"{row[5]}, {row[6]}, {row[7]}, {row[8]}, {row[9]}, {row[10]} );"
            print(ins_str)
            cur.execute(ins_str)
        cw_conn.conn.commit()

