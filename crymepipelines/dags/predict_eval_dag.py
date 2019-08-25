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

# TRAIN CRYME CLASSIFIER DAG #
train_cryme_classifier_dag = DAG('train_cryme_classifier', default_args=default_args,
                                 schedule_interval=None, catchup=False)
t1 = BashOperator(
    task_id='clean_crime_incidents',
    bash_command=cli_args['spark-submit'] + 'run.py --task CleanCrimeIncidents',
    dag=train_cryme_classifier_dag)

t2 = BashOperator(
    task_id='add_features_to_crime_incidents',
    bash_command=cli_args['spark-submit'] + 'run.py --task AddFeaturesToCrimeIncidents',
    dag=train_cryme_classifier_dag)


t3 = BashOperator(
    task_id='generate_location_time_samples',
    bash_command=cli_args['local_python_exec'] + 'run.py --task GenerateLocationTimeSamples',
    dag=train_cryme_classifier_dag)

t4 = BashOperator(
    task_id='engineer_features_location_time_samples',
    bash_command=cli_args['spark-submit'] + 'run.py --task EngineerFeaturesLocationTimeSamples',
    dag=train_cryme_classifier_dag)

t5 = BashOperator(
    task_id='train_cryme_classifiers',
    bash_command=cli_args['spark-submit'] + 'run.py --task TrainCrymeClassifiers',
    dag=train_cryme_classifier_dag)

t2.set_upstream(t1)
t3.set_upstream(t2)
t4.set_upstream(t3)
t5.set_upstream(t4)


# EVAL CRYME CLASSIFIER DAG #
eval_cryme_classifier_dag = DAG('eval_cryme_classifier', default_args=default_args,
                                schedule_interval='0 12 * * *', catchup=False)
t7 = BashOperator(
    task_id='clean_crime_incidents',
    bash_command=cli_args['spark-submit'] + 'run.py --task CleanCrimeIncidents',
    dag=eval_cryme_classifier_dag)


t8 = BashOperator(
    task_id='add_features_to_crime_incidents',
    bash_command=cli_args['spark-submit'] + 'run.py --task AddFeaturesToCrimeIncidents',
    dag=eval_cryme_classifier_dag)

t9 = BashOperator(
    task_id='generate_location_time_samples',
    bash_command=cli_args['local_python_exec'] + 'run.py --task GenerateLocationTimeSamples',
    dag=eval_cryme_classifier_dag)

t10 = BashOperator(
    task_id='engineer_features_daily_location_time_samples',
    bash_command=cli_args['spark-submit'] + 'run.py --task EngineerFeaturesEvalTimeSamples',
    dag=eval_cryme_classifier_dag)

t11 = BashOperator(
    task_id='eval_cryme_classifiers',
    bash_command=cli_args['spark-submit'] + 'run.py --task EvalCrymeClassifiers',
    dag=eval_cryme_classifier_dag)


t8.set_upstream(t7)
t9.set_upstream(t8)
t10.set_upstream(t9)
t11.set_upstream(t10)
