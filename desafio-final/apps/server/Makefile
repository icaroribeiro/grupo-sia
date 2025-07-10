# Common tasks.
set-env:
	.\scripts\set_env.bat

format:
	ruff check --select I --fix . \
	ruff format .

# MongoDB tasks.
init-mongodb:
	uv run scripts/init_mongodb.py

create-migration:
	beanie new-migration -n $(MIGRATION_NAME) -p mongodb/migrations

roll-one-forward-migration:
	beanie migrate -uri 'mongodb://${MONGODB_USERNAME}:${MONGODB_PASSWORD}@${MONGODB_HOST}:${MONGODB_PORT}' -db ${MONGODB_DATABASE} -p mongodb/migrations --distance 1 --forward --no-use-transaction

# Server tasks.
run-server:
	uv run scripts/run_server.py

# Container tasks.
build-container:
	docker build -f Dockerfile.server -t server-image .

startup-container:
	docker run -d --name server-container --env-file .env -p 8000:8000 -v server_data:/data/server server-image

shutdown-container:
	docker stop server-container && docker rm server-container

remove-image:
	docker rmi server-image
