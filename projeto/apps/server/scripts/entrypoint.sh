#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status

echo "Starting container entrypoint..."

echo "Initiating Mongo database..."
uv run scripts/init_mongodb.py

echo "Running server application..."
uv run scripts/run_server.py

echo "All scripts finished."
