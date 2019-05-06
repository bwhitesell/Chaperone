#!/bin/bash
# A script to install dependencies and setup all configurations for production deployment.

export USER=ubuntu

echo "Installing Dependencies..."

yes Y | sudo apt-get upgrade
sudo apt-get update

# Intall OpenJDK 8 - Oracle Java no longer available
#
sudo add-apt-repository ppa:openjdk-r/ppa
sudo apt-get update
sudo apt-get install -y openjdk-8-jdk

export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
echo "export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64" | sudo tee -a $HOME/.bashrc

# install scala (yuck)
sudo apt-get install scala


# Install Spark
curl -Lko /tmp/spark-2.4.2-bin-without-hadoop.tgz http://apache.mirrors.lucidnetworks.net/spark/spark-2.4.2/spark-2.4.2-bin-hadoop2.7.tgz
mkdir -p $HOME/spark
cd $HOME
tar -xvf /tmp/spark-2.4.2-bin-without-hadoop.tgz -C spark --strip-components=1

echo "# Spark environment setup" | sudo tee -a $HOME/.bashrc
export SPARK_HOME=$HOME/spark
echo 'export SPARK_HOME=$HOME/spark' | sudo tee -a $HOME/.bashrc
export PATH=$PATH:$SPARK_HOME/bin
echo 'export PATH=$PATH:$SPARK_HOME/bin' | sudo tee -a $HOME/.bashrc

# Have to set spark.io.compression.codec in Spark local mode
cp $HOME/spark/conf/spark-defaults.conf.template $HOME/spark/conf/spark-defaults.conf
echo 'spark.io.compression.codec org.apache.spark.io.SnappyCompressionCodec' | sudo tee -a /$HOME/spark/conf/spark-defaults.conf

# Give Spark 25GB of RAM, use Python3
echo "spark.driver.memory 30g" | sudo tee -a $SPARK_HOME/conf/spark-defaults.conf
echo "spark.executor.cores 12" | sudo tee -a $SPARK_HOME/conf/spark-defaults.conf
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
