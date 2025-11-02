# General tasks.
# --------------------------------------------------------------------------------------
format:
	ruff check --select I --fix . \
	ruff format .

format-entrypoint:
	dos2unix entrypoint.sh

# Streamlit App tasks.
# --------------------------------------------------------------------------------------
launch-streamlit-app:
	uv run launch_streamlit_app.py

# PostgreSQL DB tasks.
# --------------------------------------------------------------------------------------
migrate-postgresql-db:
	uv run migrate_postgresql_db.py

# Streamlit App and PostgreSQL DB containers tasks.
# --------------------------------------------------------------------------------------
startup-streamlit-app:
	docker-compose up --build -d streamlit_app

shutdown-streamlit-app:
	docker-compose down -v streamlit_app

startup-postgresql-db:
	docker-compose up --build -d postgresql_db

shutdown-postgresql-db:
	docker-compose down -v postgresql_db
