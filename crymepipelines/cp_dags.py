from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG('CrymeFeeder Train Model', default_args=default_args, schedule_interval=timedelta(days=1))

# t1, t2 and t3 are examples of tasks created by instantiating operators

base_spark_submit = 'cd $HOME/.envs/cc/CrymeClarity/crymepipelines/dist && spark-submit --py-files shared.zip,tasks.zip'
t1 = BashOperator(
    task_id='',
    bash_command=base_spark_submit + 'run.py --task GenerateLocationTimeSamples',
    dag=dag)

t2 = BashOperator(
    task_id='',
    bash_command=base_spark_submit + 'run.py --task BuildDataset',
    dag=dag)

t3 = BashOperator(
    task_id='',
    bash_command=base_spark_submit + 'run.py --task CleanDataset',
    dag=dag)

t4 = BashOperator(
    task_id='',
    bash_command=base_spark_submit + 'run.py --task EngineerFeatures',
    dag=dag)

t5 = BashOperator(
    task_id='',
    bash_command=base_spark_submit + 'run.py --task EngineerFeatures',
    dag=dag)

t2.set_upstream(t1)
