# Common tasks.
set-env:
	.\scripts\set_env.bat

format:
	ruff check --select I --fix . \
	ruff format .

# MongoDB tasks.
init-mongodb:
	python scripts/init_mongodb.py

create-migration:
	beanie new-migration -n $(MIGRATION_NAME) -p mongodb/migrations

roll-one-forward-migration:
	beanie migrate -uri 'mongodb://${MONGODB_USERNAME}:${MONGODB_PASSWORD}@${MONGODB_HOST}:${MONGODB_PORT}' -db ${MONGODB_DATABASE} -p mongodb/migrations --distance 1 --forward --no-use-transaction

# Server tasks.
run-server:
	python scripts/run_server.py

# Container tasks.
build-container:
	docker build -f Dockerfile.server -t server-app-image .

startup-container:
	docker run --name server-app-container --env-file .env -p 8080:8080 server-app-image

shutdown-container:
	docker stop server-app-container && docker rm server-app-container

remove-image:
	docker rmi server-app-image