from pyspark.sql.functions import udf

from .mappings import space_dist


class SearchForCrimesMixin:

    def find_surrounding_crimes(self, loc_time_samples, crime_incidents):
        #  begin grid search and merge
        results = None
        for i in range(-1, 2):
            for j in range(-1, 2):
                subsample = loc_time_samples.withColumn('lat_bb', loc_time_samples.lat_bb + i)
                subsample = subsample.withColumn('lon_bb', loc_time_samples.lon_bb + j)

                results_subsample = subsample.join(
                    crime_incidents,
                    (subsample.lat_bb == crime_incidents.lat_bb_c) & (subsample.lon_bb == crime_incidents.lon_bb_c)
                )

                results_subsample = results_subsample.filter(
                    results_subsample.ts_occ_unix - results_subsample.timestamp_unix < 3600 * 4
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

                results_subsample = results_subsample.filter(results_subsample.distance < .175)
                results = results.union(results_subsample) if results else results_subsample

        # All local crime incidents found, count incidents per event and merge back with events sample
        results = results.groupBy("id", "crm_grp").count()

        results = results.withColumn('n_ab', udf(lambda x: 1 if x == 'AB' else 0)(results.crm_grp))
        results = results.withColumn('n_b', udf(lambda x: 1 if x == 'B' else 0)(results.crm_grp))
        results = results.withColumn('n_t', udf(lambda x: 1 if x == 'T' else 0)(results.crm_grp))
        results = results.withColumn('n_btv', udf(lambda x: 1 if x == 'BTV' else 0)(results.crm_grp))
        results = results.withColumn('n_vbbs', udf(lambda x: 1 if x == 'VBBS' else 0)(results.crm_grp))
        results = results.withColumn('n_pdt', udf(lambda x: 1 if x == 'PDT' else 0)(results.crm_grp))
        results = results.withColumn('n_ltvc', udf(lambda x: 1 if x == 'LTVC' else 0)(results.crm_grp))
        results = results.withColumn('n_sp', udf(lambda x: 1 if x == 'SP' else 0)(results.crm_grp))
        results = results.withColumn('n_mio', udf(lambda x: 1 if x == 'MIO' else 0)(results.crm_grp))
        results = results.withColumn('n_r', udf(lambda x: 1 if x == 'R' else 0)(results.crm_grp))

        results = results.groupBy("id").agg({
            'n_ab': 'sum',
            'n_b': 'sum',
            'n_t': 'sum',
            'n_btv': 'sum',
            'n_vbbs': 'sum',
            'n_pdt': 'sum',
            'n_ltvc': 'sum',
            'n_sp': 'sum',
            'n_mio': 'sum',
            'n_r': 'sum'
        })

        results = results\
            .withColumnRenamed("SUM(n_ab)", "n_ab")\
            .withColumnRenamed("SUM(n_b)", "n_b")\
            .withColumnRenamed("SUM(n_t)", "n_t")\
            .withColumnRenamed("SUM(n_btv)", "n_btv")\
            .withColumnRenamed("SUM(n_vbbs)", "n_vbbs")\
            .withColumnRenamed("SUM(n_pdt)", "n_pdt")\
            .withColumnRenamed("SUM(n_ltvc)", "n_ltvc")\
            .withColumnRenamed("SUM(n_sp)", "n_sp")\
            .withColumnRenamed("SUM(n_mio)", "n_mio")\
            .withColumnRenamed("SUM(n_r)", "n_r")

        dataset = loc_time_samples.join(results, "id", "left_outer")
        dataset = dataset.fillna(0, subset=['n_mio', 'n_btv', 'n_vbbs', 'n_pdt', 'n_b', 'n_t',
                                            'n_ltvc', 'n_r', 'n_sp', 'n_ab'])

        return dataset
