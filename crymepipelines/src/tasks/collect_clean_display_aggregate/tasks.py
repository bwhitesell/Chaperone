from datetime import datetime, timedelta
from pyspark.sql.functions import monotonically_increasing_id, unix_timestamp

from shared.objects.samples import SamplesManager
from shared.settings import CF_TRUST_DELAY, START_DATE, cf_conn, cp_conn, TMP_DIR, BIN_DIR
from ..base import SparkCrymeTask, NativeCrymeTask
from ..constants import safety_rel_crimes
from ..mappings import ts_conv, crime_group_assignment_udf, t_occ_conv, actb_lat, actb_lon


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


class CleanCrimeIncidents(SparkCrymeTask):
    output_file = TMP_DIR + '/clean_crime_incidents.parquet'

    def run(self):
        raw_crime_incidents = self.load_df_from_crymefeeder("incidents")
        crime_incidents = raw_crime_incidents.withColumn('date_occ', ts_conv(raw_crime_incidents.date_occ))
        crime_incidents = crime_incidents.filter(crime_incidents.date_occ > datetime.now().date() - timedelta(days=365))
        crime_incidents = crime_incidents.filter(crime_incidents.crm_cd.isin(list(safety_rel_crimes.keys())))
        crime_incidents = crime_incidents.withColumn('lon', crime_incidents.location_1.coordinates[1])
        crime_incidents = crime_incidents.withColumn('lat', crime_incidents.location_1.coordinates[0])
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


class AggregateCrimesByPremises(SparkCrymeTask):
    input_file = TMP_DIR + '/clean_crime_incidents.parquet'

    def run(self):
        crime_incidents = self.spark.read.parquet(self.input_file)
        crime_incidents = crime_incidents.filter(crime_incidents.date_occ > datetime.now().date() - timedelta(days=30))

        by_type = crime_incidents.groupBy('premis_desc').agg({'_id': 'count'}).orderBy("count(_id)", ascending=False)
        by_type = by_type.withColumn("id", monotonically_increasing_id())
        by_type = by_type.withColumnRenamed("count(_id)", "volume")

        self.write_to_cw(by_type.limit(10), 'crime_crimespremisesvolume')


