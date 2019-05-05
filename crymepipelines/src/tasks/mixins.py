from datetime import datetime, timedelta
import pyspark.sql.functions as psf
from pyspark.sql.functions import col

from .base import BaseCrymeTask
from .mappings import ts_conv, t_occ_conv, actb_lat, actb_lon, space_dist


class SearchForCrimesMixin(BaseCrymeTask):
    def search_for_crimes(self, events_sample, write_to_db=False):
        crime_incidents = self.load_df_from_crymefeeder("incidents")

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