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

base_dir_command = 'cd $HOME/.envs/cc/CrymeClarity/crymepipelines/dist'

cli_args = {
    'spark-submit': base_dir_command + ' && spark-submit --py-files shared.zip,tasks.zip,libs.zip ',
    'local_python_exec': base_dir_command + ' && $HOME/.envs/cc/bin/python ',
 }

# PIPE RAW EVENTS DAG #
pipe_events_dag = DAG('clean_agg_pipe', default_args=default_args,
                      schedule_interval='* 12 * * *', catchup=False)

t0 = BashOperator(
    task_id='generate_location_time_samples',
    bash_command=cli_args['local_python_exec'] + 'run.py --task GenerateLocationTimeSamples',
    dag=pipe_events_dag)

t1 = BashOperator(
    task_id='clean_crime_incidents',
    bash_command=cli_args['spark-submit'] + 'run.py --task CleanCrimeIncidents',
    dag=pipe_events_dag)

t2 = BashOperator(
    task_id='pipe_recent_crime_incidents',
    bash_command=cli_args['spark-submit'] + 'run.py --task PipeRecentCrimeIncidents',
    dag=pipe_events_dag)

t3 = BashOperator(
    task_id='add_features_to_crime_incidents',
    bash_command=cli_args['spark-submit'] + 'run.py --task AddFeaturesToCrimeIncidents',
    dag=pipe_events_dag)

t4 = BashOperator(
    task_id='aggregate_crime_volumes',
    bash_command=cli_args['spark-submit'] + 'run.py --task AggregateCrimeVolumes',
    dag=pipe_events_dag)

t5 = BashOperator(
    task_id='aggregate_crime_by_premises',
    bash_command=cli_args['spark-submit'] + 'run.py --task AggregateCrimesByPremises',
    dag=pipe_events_dag)

t1.set_upstream(t0)
t2.set_upstream(t1)
t3.set_upstream(t2)
t4.set_upstream(t3)
t5.set_upstream(t3)

