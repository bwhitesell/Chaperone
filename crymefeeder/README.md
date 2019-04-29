# CrymeFeeder
CrymeFeeder is a tool to manage retrieval and storage of
historical as well as real-time crime data. 

#### Supported Data Sources
- LAPD Open API https://data.lacity.org/A-Safe-City/Crime-Data-from-2010-to-Present/y8tr-7khq


CrymeFeeder's functionality is oriented around two objectives. One, backfill all available historical
data and two, maintaining synchronicity with all data sources.

configuration is done via the `settings.py` file.

Commands can be issued via the `run.py` file.

To serve the other CrymeClarity apps, upon initialization run
```
$ ./run.py populate_data
$ ./run.py update_data
```
The `update_data` command should be run on  a schedule via cron. 
A cronjob to do exactly this is contained in `ops/cron/crymejobs.txt`


#### Scope
Each record managed by CrymeFeeder should represent a unique crime report.
CrymeFeeder should manage the rectification of potential duplicate entries,
synchronicity of entries between all sources and availability of data to all other
CrymeClarity services without user intervention.

CrymeFeeder should NEVER perform any updates or deletions of existing data.
Additionally, no guarantees are provided on the completeness of the dataset prior to any given timestamp.
This means as new crime reports are created, there is no constraint on the recency of the crime event.
For example, a crime that occurred 6 months ago, but was reported today will be ingested by CrymeFeeder.
As a product of this, any ETL on historical crime data will likely
need to be re-performed regularly.

