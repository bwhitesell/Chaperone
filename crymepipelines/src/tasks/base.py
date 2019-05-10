from shared.settings import DB_URL, FEEDER_DB_URL, CRYMEWEB_DB_URL


class BaseCrymeTask:

    def __init__(self, spark_session):
        self.spark = spark_session  # not all tasks use spark but the session is there regardless.
        self.db_url = DB_URL
        self.feeder_db_url = FEEDER_DB_URL
        self.web_db_url = CRYMEWEB_DB_URL

    def load_df_from_db(self, table):
        return self.spark.read.format("jdbc").options(
            url="jdbc:" + self.db_url,
            driver="com.mysql.jdbc.Driver",
            dbtable=table,
        ).load()

    def write_to_db(self, df, table):
        df.write.format('jdbc').options(
            url="jdbc:" + self.db_url,
            driver='com.mysql.jdbc.Driver',
            dbtable=table,
        ).mode('overwrite').save()

    def load_df_from_crymefeeder(self, collection):
        return self.spark.read.format("com.mongodb.spark.sql.DefaultSource").option(
            "uri",
            self.feeder_db_url + '.' + collection
        ).load()


class NativeCrymeTask:

    def __init__(self, spark):
        import pandas as pd
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import log_loss
        self.db_url = DB_URL
        self.feeder_db_url = FEEDER_DB_URL
        self.web_db_url = CRYMEWEB_DB_URL
