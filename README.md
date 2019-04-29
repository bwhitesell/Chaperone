# CrymeClarity
🚓 CrymeClarity is an analytics application that estimates and serves safety information to the city of Los Angeles.

CrymeClarity is composed of three distinct but co-dependent applications, these are:
  - CrymeWeb (A django application to serve safety information via web app)
  
  - CrymePipelines (A Spark application to run all ETL and model training tasks)
  
  - CrymeFeeder (A python application to manage retrieval and storage of crime data from the city of LA's public API)
  
For additional details on each of these applications and their dependencies see the readme contained in each of their respective directories.

#### Setup
 `ops/build.sh` is a shell script that can be run from any directory on a machine running ubuntu 18.04 and will build 
 a production configuration of this application identical to the one running on http://crymeclarity.com.
 
 
