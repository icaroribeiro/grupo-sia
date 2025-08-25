#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status

echo "Starting container entrypoint..."

echo "Migrate Postgres database..."
uv run scripts/migrate_postgresdb.py

echo "Run Server application..."
uv run scripts/run_server.py

echo "All scripts finished."
