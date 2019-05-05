from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import pickle as p
import pymysql
import random
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss

from shared.objects.samples import SamplesManager
from shared,settings import CF_TRUST_DELAY, START_DATE, cf_conn, cp_conn, TMP_DIR
from .base import BaseCrymeTask
from .mixins import SearchForCrimesMixin


class GenerateLocationTimeSamples(BaseCrymeTask):
    task_type = 'single'

    def run(self):
        sm = SamplesManager()
        cf_freshness = cf_conn.get_recency_data()
        update_date = (cf_freshness - CF_TRUST_DELAY).date()
        print(update_date)
        # check the update date before running.
        if (update_date < datetime.now().date()) and (update_date > START_DATE):
            sm.update_samples(update_date)
        else:
            raise ValueError('Invalid Update Date Specified.')


class BuildDataset(SearchForCrimesMixin):
    def run(self):
        #  import req. data. should require no cleaning as all the data should be pre-vetted by the generation script
        events_sample = self.load_df_from_db('location_time_samples')
        features_ds = self.search_for_crimes(events_sample)
        features_ds.write.parquet(TMP_DIR + '/features.parquet')


class TrainCrymeClassifier(BaseCrymeTask):
    task_type = 'single'

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




