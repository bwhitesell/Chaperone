#!/usr/bin/env python
import pyspark
import sys
from src import tasks


APP_NAME = 'CRYME_PIPELINE'
sc = pyspark.SparkContext()
spark = pyspark.sql.SparkSession(sc).builder.appName(APP_NAME).getOrCreate()

if __name__ == "__main__":
    # check for arguments
    if len(sys.argv) < 2:
        raise ValueError("No command provided.")
    try:
        getattr(tasks, sys.argv[1])(spark)
    except AttributeError:
        raise ValueError("{sys.argv[1]} is not a valid task. Check for typos.")