# Chaperone
🚓 Chaperone is an analytics application that estimates and serves safety information to the city of Los Angeles.

Chaperone is composed of three distinct but co-dependent applications, these are:
  - CrymeWeb (A django application to serve safety information via web app)
  
  - CrymePipelines (A Spark application to run all ETL and model training tasks)
  
  - CrymeFeeder (A python application to manage retrieval and storage of crime data from the city of LA's public API)
  
For additional details on each of these applications and their dependencies see the readme contained in each of their respective directories.

#### Setup (Ubuntu 18.04)
```bash
$ cd /tmp
$ git clone git@github.com:bwhitesell/CrymeClarity.git
$ cd CrymeClarity
# update the username in ops files if needed.
$ source ops/build.sh
$ rm -rf /tmp/CrymeClarity
```
`ops/build.sh` will perform a complete build of crymeclarity. If using a user with a name other than "ubuntu" some of 
the config files in `ops/` will need to be updated with the corresponding username.

Once run, the crymeweb-webserver should be avail at http://localhost:80 and the airflow webserver
should be avail at http://localhost:8080

These can be shutdown for development with 
```bash
$ systemctl stop gunicorn.socket
$ systemctl stop gunicorn.service
$ systemctl stop nginx
$ systemctl stop airflow-webserver.service
$ systemctl stop airflow-scheduler.service
```

and instead the development webservers can be used for airflow and django. For further detail on 
development within each of the subapps see the readme contained in each respective directory.
 
 
 
 
