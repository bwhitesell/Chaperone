from pyspark.sql.functions import monotonically_increasing_id

from shared.settings import DB_URL, FEEDER_DB_URL, CRYMEWEB_DB_URL


class BaseCrymeTask:

    def __init__(self):
        self.db_url = DB_URL
        self.feeder_db_url = FEEDER_DB_URL
        self.web_db_url = CRYMEWEB_DB_URL


class SparkCrymeTask(BaseCrymeTask):

    def __init__(self, spark_session):
        self.spark = spark_session
        super().__init__()

    def load_df_from_cp(self, table):
        return self.spark.read.format("jdbc").options(
            url="jdbc:" + self.db_url,
            driver="com.mysql.jdbc.Driver",
            dbtable=table,
        ).load()

    def write_to_cw(self, df, table):
        df.write.format('jdbc').options(
            url="jdbc:" + self.web_db_url,
            driver='com.mysql.jdbc.Driver',
            dbtable=table,
        ).mode('overwrite').save()

    def load_df_from_crymefeeder(self, collection):
        return self.spark.read.format("com.mongodb.spark.sql.DefaultSource").option(
            "uri",
            self.feeder_db_url + '.' + collection
        ).load()

    @staticmethod
    def sanitize_df_for_cw_ingestion(df):
        df = df.withColumn("id", monotonically_increasing_id())
        df = df.withColumn("date_occ", df.date_occ.cast("string"))
        df = df.withColumnRenamed("_id", "row_id")
        return df


class NativeCrymeTask(BaseCrymeTask):

    def __init__(self, spark):
        import pandas
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import log_loss

        self._local_mod_access = {}
        for _module in [pandas, RandomForestClassifier, log_loss]:
            self._local_mod_access[_module.__name__] = _module

        super().__init__()
