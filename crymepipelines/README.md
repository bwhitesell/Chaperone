# CrymePipelines
🚓CrymePipelines is the analytics engine powering CrymeClarity. At its core,
it performs OLAP on the data provided by crymefeeder and persists results for use
by crymeweb.

The functional object in CrymePipelines is a `CrymeTask`. CrymeTasks are defined in the
 `src/tasks.py` file and scheduled via an airflow DAG.
 
 
#### Config
As mentioned above, CrymePipelines must be configured to communicate with the mongodb 
instance managed by CrymeFeeder, the mysql db instance managed by CrymeWeb and an additional mysql db
instance for storing metadata necessary for CrymePipelines to function. All three
of these connections are configured via environmental variable. E.g.
```bash
$ export CRYMEPIPELINES_DB_URL=''
$ export CRYMEFEEDER_DB_URL=''
$ export CRYMEWEB_DB_URL=''
```