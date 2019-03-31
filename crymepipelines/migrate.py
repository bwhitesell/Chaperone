#  Setup needed db and tables for the crymepipelines application.
import os
import pymysql
from urllib.parse import urlparse


MYSQL_URL = os.environ.get('MYSQL_URL')
conn_params = urlparse(MYSQL_URL)

conn = pymysql.connect(host=conn_params.hostname,
                       user=conn_params.username,
                       password=conn_params.password,
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)
cursor = conn.cursor()

cursor.execute("CREATE DATABASE crymepipelines;")
cursor.close()

conn = pymysql.connect(host=conn_params.hostname,
                       user=conn_params.username,
                       password=conn_params.password, charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor,
                       database='crymepipelines')
cursor = conn.cursor()

cursor.execute(
    'CREATE TABLE IF NOT EXISTS dataset (' +
        'id INT AUTO_INCREMENT, ' +
        'latitude FLOAT(53) NOT NULL, ' +
        'longitude FLOAT(53) NOT NULL, ' +
        'timestamp DATETIME NOT NULL, ' +
        'estimate VARCHAR(255), ' +
        'model_id VARCHAR(255), ' +
        'lat_bb INT NOT NULL, ' +
        'lon_bb INT NOT NULL, ' +
        'timestamp_unix BIGINT NOT NULL, ' +
        'count INT, ' +
        'PRIMARY KEY (id)' +
        ')  ENGINE=INNODB;'
)

cursor.execute(
    'CREATE TABLE IF NOT EXISTS cryme_classifiers (' +
        'id INT AUTO_INCREMENT, ' +
        'log_loss FLOAT(53) NOT NULL, ' +
        'n_samples_train INT NOT NULL, ' +
        'n_samples_test INT NOT NULL, ' +
        'model_generated_on DATETIME NOT NULL, ' +
        'saved_to VARCHAR(255), ' +
        'PRIMARY KEY (id)' +
        ')  ENGINE=INNODB;'
)

cursor.close()
