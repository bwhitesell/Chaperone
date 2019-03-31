#!/usr/bin/env python
import findspark
findspark.init()
import pyspark
import sys

from settings import MYSQL_URL, MONGO_URL
import tasks.tasks as tasks


APP_NAME = 'CRYME_PIPELINE'
sc = pyspark.SparkContext()
spark = pyspark.sql.SparkSession(sc).builder.appName(APP_NAME).getOrCreate()

if __name__ == "__main__":
    # check for arguments`
    if len(sys.argv) < 2:
        raise ValueError("No command provided.")
    try:
        if len(sys.argv) > 2:
            task = getattr(tasks, sys.argv[1])(spark, MYSQL_URL, MONGO_URL).run(sys.argv[2])
        else:
            task = getattr(tasks, sys.argv[1])(spark, MYSQL_URL, MONGO_URL).run()
    except AttributeError:
        raise ValueError(f"{sys.argv[1]} is not a valid task. Check for typos.")