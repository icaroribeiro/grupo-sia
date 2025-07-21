# Container tasks.
build-container:
	docker build -f Dockerfile.mongodb -t mongodb-image .

startup-container:
	docker run -d --name mongodb-container --env-file .env -p 27017:27017 -v mongodb_data:/data/mongodb mongodb-image

shutdown-container:
	docker stop mongodb-container && docker rm mongodb-container

remove-image:
	docker rmi mongodb-image
