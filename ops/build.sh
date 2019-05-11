#!/bin/bash
# A script to install dependencies and setup all configurations for production deployment.

export USER=ubuntu

yes Y | sudo apt-get upgrade
sudo apt-get update

### GLOBAL DEPENDENCIES ###
echo "Installing Dependencies..."

yes Y | sudo apt-get install mongodb mysql-server libmysqlclient-dev nginx python3-dev python3-pip git cron libgeos-dev vim zip

# Intall OpenJDK 8 - Oracle Java no longer available
#
sudo add-apt-repository ppa:openjdk-r/ppa
sudo apt-get update
sudo apt-get install -y openjdk-8-jdk

echo "# Java" | sudo tee -a $HOME/.bashrc
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
echo "export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64" | sudo tee -a $HOME/.bashrc


# Install Spark
curl -Lko /tmp/spark-2.4.2-bin-hadoop2.7.tgz https://archive.apache.org/dist/spark/spark-2.4.2/spark-2.4.2-bin-hadoop2.7.tgz
mkdir -p $HOME/spark
cd $HOME
tar -xvf /tmp/spark-2.4.2-bin-hadoop2.7.tgz -C $HOME/spark --strip-components=1

echo "# Spark environment setup" | sudo tee -a $HOME/.bashrc
export SPARK_HOME=$HOME/spark
echo 'export SPARK_HOME=$HOME/spark' | sudo tee -a $HOME/.bashrc
export PATH=$PATH:$SPARK_HOME/bin
echo 'export PATH=$PATH:$SPARK_HOME/bin' | sudo tee -a $HOME/.bashrc

# Have to set spark.io.compression.codec in Spark local mode
cp $HOME/spark/conf/spark-defaults.conf.template $HOME/spark/conf/spark-defaults.conf
echo 'spark.io.compression.codec org.apache.spark.io.SnappyCompressionCodec' | sudo tee -a /$HOME/spark/conf/spark-defaults.conf

# Give Spark 2GB of RAM, use Python3
echo "spark.driver.memory 2g" | sudo tee -a $SPARK_HOME/conf/spark-defaults.conf
echo "spark.executor.cores 2" | sudo tee -a $SPARK_HOME/conf/spark-defaults.conf
echo "PYSPARK_PYTHON=python3" | sudo tee -a $SPARK_HOME/conf/spark-env.sh
echo "PYSPARK_DRIVER_PYTHON=python3" | sudo tee -a $SPARK_HOME/conf/spark-env.sh

# Setup log4j config to reduce logging output
cp $SPARK_HOME/conf/log4j.properties.template $SPARK_HOME/conf/log4j.properties
sed -i 's/INFO/ERROR/g' $SPARK_HOME/conf/log4j.properties

# install jars
curl -o $SPARK_HOME/jars/mongo-spark-connector_2.12-2.4.0.jar http://central.maven.org/maven2/org/mongodb/spark/mongo-spark-connector_2.12/2.4.0/mongo-spark-connector_2.12-2.4.0.jar
curl -o $SPARK_HOME/jars/scala-library-2.12.7.jar http://central.maven.org/maven2/org/scala-lang/scala-library/2.12.7/scala-library-2.12.7.jar
curl -o $SPARK_HOME/jars/mongo-java-driver-3.9.0.jar http://central.maven.org/maven2/org/mongodb/mongo-java-driver/3.9.0/mongo-java-driver-3.9.0.jar
curl -o $SPARK_HOME/jars/mysql-connector-java-8.0.14.jar http://central.maven.org/maven2/mysql/mysql-connector-java/8.0.14/mysql-connector-java-8.0.14.jar


# Give to user
sudo chown -R $USER $HOME/spark
sudo chgrp -R $USER $HOME/spark

echo "Done Installing Dependencies."



### BUILDING VIRTUAL ENVIRONMENT ###
echo "Building Virtual Environment..."
pip3 install virtualenv virtualenvwrapper
mkdir $HOME/.envs/

echo 'export PATH=$PATH:$HOME/.local/bin' | sudo tee -a $HOME/.bashrc
echo 'export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3' | sudo tee -a $HOME/.bashrc
echo 'export WORKON_HOME=$HOME/.envs' | sudo tee -a $HOME/.bashrc
echo '. ~/.local/bin/virtualenvwrapper.sh' | sudo tee -a $HOME/.bashrc
source ~/.bashrc

mkvirtualenv cc

# customize the postactivate functionality of virtualenvwrapper #
echo 'cd $VIRTUAL_ENV' | sudo tee -a $HOME/.envs/postactivate
echo 'source $VIRTUAL_ENV/postactivate' | sudo tee -a $HOME/.envs/postactivate
touch $HOME/.envs/cc/postactivate

# configure postactivate w/ the necessary environemental variables #
echo "echo 'Activating CrymeClarity Virtual Environment...'" | sudo tee -a $HOME/.envs/cc/postactivate
echo "cd ./CrymeClarity" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export SOCRATA_APP_TOKEN='UqbVdWcsfLzu2aG4CVLtd4P0O'" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export DB_URL=mongodb://localhost:27017" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export DB_NAME=crymeclarity" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export MONGO_URL=mongodb://localhost:27017/crymeclarity" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export SECRET_KEY=''" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export STATIC_ROOT=/home/ubuntu/static" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export DJANGO_DEBUG=True" | sudo tee -a $HOME/.envs/cc/postactivate

source $HOME/.bashrc
echo "Virtual Environment built. Use command 'workon cc' to activate it."

# Install Airflow
echo "# Airflow" | sudo tee -a $HOME/.profile
echo "export AIRFLOW_HOME=$HOME/airflow" | sudo tee -a $HOME/.profile
export AIRFLOW_HOME=$HOME/airflow
workon cc & pip install gunicorn & pip install apache-airflow
sudo mkdir /etc/sysconfig
sudo mkdir /run/airflow
sudo chown -R $USER /run/airflow
sudo mkdir $AIRFLOW_HOME/dags

# Give to user
sudo chown -R $USER $HOME/airflow
sudo chgrp -R $USER $HOME/airflow

### ADDING CONFIGURATION TO MYSQL, MONGODB, NGINX, GUNICORN, AIRFLOW ###
cd $HOME/.envs/cc
git clone https://github.com/bwhitesell/CrymeClarity.git

#AIRFLOW
sudo cp $HOME/.envs/cc/CrymeClarity/ops/airflow/airflow-scheduler.service /etc/systemd/system
sudo cp $HOME/.envs/cc/CrymeClarity/ops/airflow/airflow-webserver.service /etc/systemd/system
sudo cp $HOME/.envs/cc/CrymeClarity/ops/airflow/airflow.conf /etc/tmpfiles.d
sudo cp $HOME/.envs/cc/CrymeClarity/ops/airflow/airflow /etc/sysconfig

echo "AIRFLOW_HOME=$AIRFLOW_HOME" | sudo tee -a /etc/sysconfig/airflow
echo "SPARK_HOME=$SPARK_HOME" | sudo tee -a /etc/sysconfig/airflow
echo "AIRFLOW_CONFIG=$AIRFLOW_HOME/airflow.cfg" | sudo tee -a /etc/sysconfig/airflow
echo "PATH=$PATH" | sudo tee -a /etc/sysconfig/airflow

sudo ln -s $HOME/.envs/cc/CrymeClarity/crymepipelines/cp_dags.py $AIRFLOW_HOME/dags

cd $AIRFLOW_HOME
airflow initdb


sudo systemctl start airflow-webserver
sudo systemctl start airflow-scheduler

# MYSQL
sudo cp $HOME/.envs/cc/CrymeClarity/ops/mysql/analytics_my.cnf /etc/mysql/my.cnf
sudo systemctl restart mysql

#MONGODB
sudo cp $HOME/.envs/cc/CrymeClarity/ops/mongodb/mongod.conf /etc
sudo systemctl restart mongodb

#NGINX
sudo cp $HOME/.envs/cc/CrymeClarity/ops/nginx/nginx.conf /etc/nginx/
sudo systemctl enable nginx.service

#GUNICORN
sudo cp $HOME/.envs/cc/CrymeClarity/ops/gunicorn/gunicorn.socket /etc/systemd/system
sudo cp $HOME/.envs/cc/CrymeClarity/ops/gunicorn/gunicorn.service /etc/systemd/system

sudo touch /etc/tmpfiles.d/gunicorn.conf
echo "d /run/gunicorn 0755 $USER www-data -" | sudo tee -a /etc/tmpfiles.d/gunicorn.conf

sudo systemctl enable gunicorn.socket

#CRON (add jobs to crontab)
crontab $HOME/.envs/cc/CrymeClarity/ops/cron/crymejobs.txt

### SETUP CRYMECLARITY APPLICATIONS ###
workon cc
pip install -r $HOME/.envs/cc/CrymeClarity/requirements.txt

#Setup crymefeeder
echo "Syncing crymefeeder with LAPD crime API ..."
$HOME/.envs/cc/CrymeClarity/crymefeeder/run.py populate_data


#Setup crymepipelines
mysql -u root -e "CREATE DATABASE crymepipelines";
mysql -u root crymepipelines < $HOME/.envs/cc/CrymeClarity/crymepipelines/migrations/crymePipelines.sql
cd $HOME/.envs/cc/CrymeClarity/crymepipelines/
make CrymePipelines

#Setup crymeweb
mysql -u root -e "CREATE DATABASE crymeweb";
cd $HOME/.envs/cc/CrymeClarity/crymeweb/
./manage.py migrate
yes Y | ./manage.py collectstatic
#download default model
curl -o $HOME/.envs/cc/CrymeClarity/crymeweb/bin/rfc_cryme_classifier_2019_03_31.p https://s3-us-west-1.amazonaws.com/crymeclarity/rcf_cryme_classifier_2019-03-31.p
$HOME/.envs/cc/CrymeClarity/crymeweb/manage.py publish_model 'rfc_cryme_classifier_2019_03_31' '0.1' 'PC' --guarantee

sudo systemctl stop gunicorn.service
sudo systemctl stop gunicorn.socket
sudo systemctl start gunicorn.socket
sudo systemctl restart nginx