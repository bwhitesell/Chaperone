# CrymePipelines
#### Summary
🚓CrymePipelines is the analytics engine powering CrymeClarity. At its core,
it performs OLAP on the data provided by crymefeeder and persists results to a 
database for use by crymeweb.

The functional object in CrymePipelines is a `CrymeTask`. CrymeTasks are defined in the
 `src/tasks.py` file and scheduled via an airflow DAG. CrymeTasks are built by defining a
 class in the `src/tasks` directory. If the task will utilize pyspark functionality, then it must 
 inherit from `tasks.base.BaseCrymeTask` (as well as any mixins). Each class should have a single 
 `run` method that is run on execution of the task.
 
 
#### Config
CrymePipelines must be configured to communicate with the mongodb 
instance managed by CrymeFeeder, the mysql db instance managed by CrymeWeb and an additional mysql db
instance for storing metadata necessary for CrymePipelines to function. All three
of these connections are configured via `src/shared/settings.py` E.G.
```bash
DB_URL = 'mysql://root@localhost/crymepipelines?serverTimezone=UTC'
FEEDER_DB_URL = 'mongodb://localhost:27017/crymeclarity'
CRYMEWEB_DB_URL = 'mysql://root@localhost/crymeweb'
```

Once this file has been edited with the appropriate strings, the app can be built from the 
`CrymeClarity/crymepipelines` directory with
```bash
$ pip install -r requirements/native.txt
$ make CrymePipelines
```

#### Scheduling & Airflow
CrymePipelines operates through a series of scheduled pipelines defined and managed 
via airflow. These pipelines are defined in `dags` and symlinked to `$AIRFLOW_HOME` in
the build scripts.