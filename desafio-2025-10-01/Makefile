# General tasks.
format:
	ruff check --select I --fix . \
	ruff format .

# Streamlit App tasks.
launch-streamlit-app:
	uv run launch_streamlit_app.py

# Streamlit App and PostgreSQL containers tasks.
startup-streamlit-app-container:
	docker-compose up --build -d streamlit-app

shutdown-streamlit-app-container:
	docker-compose down -v streamlit-app

startup-postgresql-container:
	docker-compose up --build -d postgresql

shutdown-postgresql-container:
	docker-compose down -v postgresql
