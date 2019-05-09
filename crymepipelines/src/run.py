#!/usr/bin/env python
import argparse
import os
import sys

try:
    import pyspark
except ImportError:
    import findspark
    findspark.init()
    import pyspark

APP_NAME = 'CRYME_PIPELINE'
sc = pyspark.SparkContext()
spark = pyspark.sql.SparkSession(sc).builder.appName(APP_NAME).getOrCreate()


def import_rel_modules():
    if os.path.exists('tasks.zip'):
        sys.path.insert(0, 'tasks.zip')
    else:
        sys.path.insert(0, os.path.abspath(__file__) + '/tasks')

    if os.path.exists('shared.zip'):
        sys.path.insert(0, 'shared.zip')
    else:
        sys.path.insert(0, os.path.abspath(__file__) + '/shared')

    if os.path.exists('libs.zip'):
        sys.path.insert(0, 'libs.zip')
    else:
        sys.path.insert(0, os.path.abspath(__file__) + '/libs')


if __name__ == "__main__":
    import_rel_modules()
    from tasks import tasks as tasks
    parser = argparse.ArgumentParser(description='Run a CrymeTask')
    parser.add_argument('--task', type=str, required=True, dest='task_name', help="The name of the CrymeTask class")
    args = parser.parse_args()

    # check for arguments`
    if len(sys.argv) < 2:
        raise ValueError("No command provided.")
    try:
        task = getattr(tasks, args.task_name)(spark).run()
    except AttributeError:
        raise ValueError(f"{args.task_name} is not a valid task. Check for typos.")
