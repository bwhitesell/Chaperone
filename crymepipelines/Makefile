CrymePipelines:
	pip install -r requirements/spark.txt -t src/lib
	mkdir ./dist
	mkdir ./dist/tmp
	cp ./src/run.py ./dist
	cd ./src && zip -r ../dist/tasks.zip ./tasks && zip -r ../dist/shared.zip ./shared
	cd ./src/libs && zip -r ../../dist/libs.zip .
