# General tasks.
set-env:
	.\scripts\set_env.bat

format:
	ruff check --select I --fix . \
	ruff format .

# Server tasks.
import-csv:
	uv run scripts/import_csv_to_postgresdb.py

migrate-db:
	uv run scripts/migrate_postgresdb.py

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
