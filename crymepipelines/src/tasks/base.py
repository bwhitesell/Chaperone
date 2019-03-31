

class BaseCrymeTask:
    mysql_url = None
    mongo_url = None
    spark = None

    def __init__(self, spark, mysql_url, mongo_url):
        self.spark = spark
        self.mysql_url = mysql_url
        self.mongo_url = mongo_url

    def load_df_from_mysql(self, table):
        return self.spark.read.format("jdbc").options(
            url="jdbc:" + self.mysql_url,
            driver="com.mysql.jdbc.Driver",
            dbtable=table,
        ).load()

    def load_df_from_mongo(self, collection):
        return self.spark.read.format("com.mongodb.spark.sql.DefaultSource").option(
            "uri",
            self.mongo_url + '.' + collection
        ).load()

    def write_to_mysql(self, df, table):
        df.write.format('jdbc').options(
            url="jdbc:" + 'mysql://root@localhost/crymepipelines?serverTimezone=UTC',
            driver='com.mysql.jdbc.Driver',
            dbtable=table,
        ).mode('overwrite').save()
