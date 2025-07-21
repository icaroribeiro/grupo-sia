# Container tasks.
build-container:
	docker build -f Dockerfile.postgresdb -t postgresdb-image .

startup-container:
	docker run -d --name postgresdb-container --env-file .env -p 5432:5432 -v postgresdb_data:/data/postgresdb postgresdb-image

shutdown-container:
	docker stop postgresdb-container && docker rm postgresdb-container

remove-image:
	docker rmi postgresdb-image
