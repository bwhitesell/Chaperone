#!/bin/bash
# A script to install dependencies and setup all configurations for production deployment.

export USER=ubuntu

echo "Installing Dependencies..."

yes Y | sudo apt-get upgrade
sudo apt-get update

yes Y | sudo apt-get install mongodb mysql-server libmysqlclient-dev nginx python3-dev python3-pip git cron libgeos-dev vim


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
echo "export CRYMEWEB_DB_URL=mysql://root@localhost/crymeweb" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export CRYMEPIPELINES_DB_URL=mysql://root@localhost/crymepipelines?serverTimezone=UTC" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export CRYMEFEEDER_DB_URL=mongodb://localhost:27017/crymeclarity" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export MONGO_URL=mongodb://localhost:27017/crymeclarity" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export SECRET_KEY=''" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export STATIC_ROOT=/home/ubuntu/static" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export DJANGO_DEBUG=False" | sudo tee -a $HOME/.envs/cc/postactivate
echo "AIRFLOW_HOME=$HOME/airflow" | sudo tee -a $HOME/.envs/cc/postactivate


source $HOME/.bashrc
echo "Virtual Environment built. Use command 'workon cc' to activate it."

### ADDING CONFIGURATION TO MYSQL, MONGODB, NGINX, GUNICORN ETC ###
cd $HOME/.envs/cc
git clone https://github.com/bwhitesell/CrymeClarity.git

# MYSQL
sudo cp $HOME/.envs/cc/CrymeClarity/ops/mysql/my.cnf /etc/mysql/
sudo systemctl restart mysql

#MONGODB
sudo cp $HOME/.envs/cc/CrymeClarity/ops/mongodb/mongod.conf /etc
sudo systemctl restart mongodb

#NGINX
sudo cp $HOME/.envs/cc/CrymeClarity/ops/nginx/nginx.conf /etc/nginx/
sudo systemctl enable nginx.service

#GUNICORN
gunicorn/gunicorn.socket /etc/systemd/system
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
$HOME/.envs/cc/CrymeClarity/crymefeeder/run.py build_dev_ds


#Setup crymepipelines
mysql -u root -e "CREATE DATABASE crymepipelines";
mysql -u root crymepipelines < $HOME/.envs/cc/CrymeClarity/crymepipelines/migrations/crymePipelines.sql

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








