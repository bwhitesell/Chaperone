#!/bin/bash
# A script to install dependencies and setup all configurations for production deployment.


export USER=ubuntu

echo "Installing Dependencies..."

sudo apt-get update
sudo apt-get upgrade

sudo apt-get install mongodb mysql-server nginx python3-dev python3-pip, git


echo "Done Installing Dependencies."


### BUILDING VIRTUAL ENVIRONMENT ###
echo "Building Virtual Environment..."
pip3 install virtualenv virtualenvwrapper
mkdir $HOME/.envs/

echo 'VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3' | sudo tee -a $HOME/.bashrc
echo 'export WORKON_HOME=$HOME/.envs' | sudo tee -a $HOME/.bashrc
echo '. /usr/local/bin/virtualenvwrapper.sh' | sudo tee -a $HOME/.bashrc

mkvirtualenv cc

# customize the postactivate functionality of virtualenvwrapper #
echo 'cd $VIRTUAL_ENV' | sudo tee -a $HOME/.envs/postactivate
echo 'source $VIRTUAL_ENV/postactivate' | sudo tee -a $HOME/.envs/postactivate
touch $HOME/.envs/cc/postactivate

# configure postactivate w/ the necessary environemental variables #
echo "echo 'Activating CrymeClarity Virtual Environment...'" | sudo tee -a $HOME/.envs/cc/postactivate
echo "cd ./CrymeClarity" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export SOCRATA_APP_TOKEN=''" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export DB_URL=mongodb://localhost:27017" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export DB_NAME=crymeclarity" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export MYSQL_URL=mysql://root@localhost/crymeweb?serverTimezone=UTC" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export MONGO_URL=mongodb://localhost:27017/crymeclarity" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export SECRET_KEY=''" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export STATIC_ROOT=/home/ubuntu/static" | sudo tee -a $HOME/.envs/cc/postactivate
echo "export DJANGO_DEBUG=False" | sudo tee -a $HOME/.envs/cc/postactivate


source $HOME/.bashrc
echo "Virtual Environment built. Use command 'workon cc' to activate it."

cd $HOME/.envs/cc
git clone git@github.com:bwhitesell/CrymeClarity.git






