from datetime import datetime, timedelta
import pandas as pd
import pickle as p
import pymysql
import pyspark.sql.functions as psf
from pyspark.sql.functions import col
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss

from .base import BaseCrymeTask
from .mappings import ts_conv, t_occ_conv, actb_lat, actb_lon, space_dist


class SearchForCrimesMixin(BaseCrymeTask):
    def search_for_crimes(self, events_sample, write_to_db=True):
        crime_incidents = self.load_df_from_mongo("incidents")

        # clean data

        # convert timestamp strings to datetime
        crime_incidents = crime_incidents.withColumn('date_occ', ts_conv(crime_incidents.date_occ))
        # only days after jan 1 2018 / invalid ts strings
        crime_incidents = crime_incidents.filter(crime_incidents['date_occ'] > datetime.now() - timedelta(days=365))
        # convert time occurred to seconds
        crime_incidents = crime_incidents.withColumn('time_occ_seconds', t_occ_conv(crime_incidents.time_occ))
        crime_incidents = crime_incidents.filter(crime_incidents.time_occ_seconds >= 0)  # remove invalid choices
        # convert datetime to unix timestamp
        crime_incidents = crime_incidents.withColumn('date_occ_unix', psf.unix_timestamp(crime_incidents.date_occ))
        # assign coordinates to bounding box
        crime_incidents = crime_incidents.withColumn('lat_bb_c', actb_lat(crime_incidents.location_1.coordinates[0]))
        # assign coordinates to bounding box
        crime_incidents = crime_incidents.withColumn('lon_bb_c', actb_lon(crime_incidents.location_1.coordinates[1]))
        # engineer timestamp in unix feature
        crime_incidents = crime_incidents.withColumn(
            'ts_occ_unix',
            crime_incidents.date_occ_unix + crime_incidents.time_occ_seconds
        )

        # engineer features
        events_sample = events_sample.withColumn('lat_bb',
                                                 actb_lat(events_sample.latitude))  # assign coor to bounding box
        events_sample = events_sample.withColumn('lon_bb',
                                                 actb_lon(events_sample.longitude))  # assign coor to bounding box
        # convert datetime to unix timestamp
        events_sample = events_sample.withColumn(
            'timestamp_unix',
            psf.unix_timestamp(events_sample.timestamp)
        )

        #  begin grid search and merge
        results = None
        for i in range(-1, 2):
            for j in range(-1, 2):
                subsample = events_sample.withColumn('lat_bb', events_sample.lat_bb + i)
                subsample = subsample.withColumn('lon_bb', events_sample.lon_bb + j)

                results_subsample = subsample.join(
                    crime_incidents,
                    (subsample.lat_bb == crime_incidents.lat_bb_c) & (subsample.lon_bb == crime_incidents.lon_bb_c)
                )

                results_subsample = results_subsample.filter(
                    results_subsample.ts_occ_unix - results_subsample.timestamp_unix < 3600
                )
                results_subsample = results_subsample.filter(
                    results_subsample.ts_occ_unix - results_subsample.timestamp_unix > 0
                )

                results_subsample = results_subsample.withColumn('distance', space_dist(
                    results_subsample.longitude,
                    results_subsample.latitude,
                    results_subsample.location_1.coordinates[1],
                    results_subsample.location_1.coordinates[0],
                ))

                results_subsample = results_subsample.filter(results_subsample.distance < .5)
                results = results.union(results_subsample) if results else results_subsample

        # All local crime incidents found, count incidents per event and merge back with events sample
        results = results.groupBy(col('id')).count()
        dataset = events_sample.join(results, "id", "left_outer")

        if write_to_db:
            self.write_to_mysql(dataset, 'dataset')
        else:
            return dataset


class BuildDataset(SearchForCrimesMixin):
    def run(self):
        #  import req. data. should require no cleaning as all the data should be pre-vetted by the generation script
        events_sample = self.load_df_from_mysql('safety_syntheticanalysisrequest')
        self.search_for_crimes(events_sample, write_to_db=True)


class UpdateDataset(SearchForCrimesMixin):
    def run(self):
        ds = self.load_df_from_mysql('dataset')
        start_ts = ds.agg({"timestamp": "max"}).collect()[0][0]
        del ds

        events_sample = self.load_df_from_mysql('safety_syntheticanalysisrequest')
        events_sample = events_sample.filter(events_sample.timestamp > start_ts)

        self.search_for_crimes(events_sample, write_to_db=True)


class TrainCrymeClassifier(BaseCrymeTask):
    def run(self, model_save_path):
        features = ['longitude', 'latitude', 'time_minutes', 'day_of_week']
        conn = pymysql.connect(host='localhost',
                               user='root',
                               password='',
                               db='crymepipelines',
                               charset='utf8mb4',
                               cursorclass=pymysql.cursors.DictCursor)

        ts_end = (datetime.now() - timedelta(days=30)).date()
        ts_start = ts_end - timedelta(days=300)

        cds = pd.read_sql('SELECT * FROM dataset WHERE timestamp < "' + str(ts_end) +
                          '" AND timestamp > "' + str(ts_start) + '"', conn)
        cds_test = pd.read_sql('SELECT * FROM dataset WHERE timestamp >= "' + str(ts_end) + '"', conn)

        cds = self.clean_and_engineer_ds(cds)
        cds_test = self.clean_and_engineer_ds(cds_test)

        rfc = RandomForestClassifier(max_depth=10, n_estimators=500, n_jobs=-1)
        rfc.fit(cds[features], cds['crime_occ'])
        y_est = rfc.predict_proba(cds_test[features])
        ll = log_loss(cds_test['crime_occ'], y_est)

        cur = conn.cursor()
        cur.execute('INSERT INTO cryme_classifiers (log_loss, n_samples_train, n_samples_test, model_generated_on, ' +
                    f'saved_to) VALUES ({ll}, {cds.shape[0]}, {cds_test.shape[0]}, "{datetime.now()}", ' +
                    f'"{model_save_path}")')
        cur.close()

        p.dump(rfc, open(model_save_path + '/rfc_cryme_classifier' + str(datetime.now()) + '.p', 'wb'))

    @staticmethod
    def clean_and_engineer_ds(cds):
        cds.columns = cds.columns = ['id', 'latitude', 'longitude', 'timestamp', 'estimate', 'model_id',
               'lat_bb', 'lon_bb', 'timestamp_unix', 'n_crimes']
        cds.n_crimes = cds.n_crimes.fillna(0)

        cds['crime_occ'] = cds.n_crimes.apply(lambda x: min(x, 1))

        cds['time_minutes'] = cds.timestamp.apply(lambda x: datetime.time(x).hour * 60 + datetime.time(x).minute)
        cds['hour'] = cds.timestamp.apply(lambda x: datetime.time(x).hour)
        cds['day_of_week'] = cds.timestamp.apply(lambda x: x.weekday())
        return cds




