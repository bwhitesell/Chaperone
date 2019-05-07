from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta


default_args = {
    'owner': 'airflow',
    'start_date': datetime(2019, 5, 1),
    'depends_on_past': False,
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

base_spark_submit = 'cd $HOME/.envs/cc/CrymeClarity/crymepipelines/dist && spark-submit --py-files shared.zip,tasks.zip '

dag = DAG('train_cryme_classifier', default_args=default_args, schedule_interval='*/5 * * * *', catchup=False)

# t1, t2 and t3 are examples of tasks created by instantiating operators

t1 = BashOperator(
    task_id='generate_location_time_samples',
    bash_command=base_spark_submit + 'run.py --task GenerateLocationTimeSamples',
    dag=dag)

t2 = BashOperator(
    task_id='build_dataset',
    bash_command=base_spark_submit + 'run.py --task BuildDataset',
    dag=dag)

t3 = BashOperator(
    task_id='clean_dataset',
    bash_command=base_spark_submit + 'run.py --task CleanDataset',
    dag=dag)

t4 = BashOperator(
    task_id='engineer_features',
    bash_command=base_spark_submit + 'run.py --task EngineerFeatures',
    dag=dag)

t5 = BashOperator(
    task_id='train_model',
    bash_command=base_spark_submit + 'run.py --task TrainCrymeClassifier',
    dag=dag)

t2.set_upstream(t1)
t3.set_upstream(t2)
t4.set_upstream(t3)
t5.set_upstream(t4)
