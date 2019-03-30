#  Setup needed db and tables for the crymepipelines application.
import pymysql

conn = pymysql.connect(host='localhost', user='root', password='',
                charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
cursor = conn.cursor()

cursor.execute("CREATE DATABASE crymepipelines;")
cursor.close()

conn = pymysql.connect(host='localhost', user='root', password='', database='crymepipelines',
                charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
cursor = conn.cursor()

cursor.execute(
    'CREATE TABLE IF NOT EXISTS dataset (' +
        'id INT AUTO_INCREMENT, ' +
        'latitude FLOAT(53) NOT NULL, ' +
        'longitude FLOAT(53) NOT NULL, ' +
        'timestamp VARCHAR(255) NOT NULL, ' +
        'estimate VARCHAR(255), ' +
        'model_id VARCHAR(255), ' +
        'lat_bb INT NOT NULL, ' +
        'lon_bb INT NOT NULL, ' +
        'timestamp_unix BIGINT NOT NULL, ' +
        'count INT, ' +
        'PRIMARY KEY (id)' +
        ')  ENGINE=INNODB;'
)

cursor.close()
