from datetime import datetime, timedelta
import pyspark.sql.functions as psf
from pyspark.sql.functions import col

from shared.settings import TMP_DIR
from .base import SparkCrymeTask
from .mappings import ts_conv, t_occ_conv, actb_lat, actb_lon, space_dist


class SearchForCrimesMixin:
    input_file = TMP_DIR + '/clean_crime_incidents.parquet'

    def find_surrounding_crimes(self, events_sample, crime_incidents):
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
                    results_subsample.lon,
                    results_subsample.lat,
                ))

                results_subsample = results_subsample.filter(results_subsample.distance < .25)
                results = results.union(results_subsample) if results else results_subsample

        # All local crime incidents found, count incidents per event and merge back with events sample
        results = results.groupBy(col('id')).count()
        dataset = events_sample.join(results, "id", "left_outer")

        return dataset
