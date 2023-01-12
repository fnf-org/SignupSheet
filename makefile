db:
	podman run -it --rm -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=root -e MONGO_INITDB_ROOT_PASSWORD=example docker.io/mongo 

dev:
	python3 ./manage.py runserver	
