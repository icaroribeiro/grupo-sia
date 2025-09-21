# General tasks.
format:
	ruff check --select I --fix . \
	ruff format .

# App tasks.
run-app:
	uv run scripts/run_app.py

# Containers tasks.
startup-app-container:
	docker-compose up --build -d app

shutdown-app-container:
	docker-compose down -v app

startup-postgres-container:
	docker-compose up --build -d postgres

shutdown-postgres-container:
	docker-compose down -v postgres
