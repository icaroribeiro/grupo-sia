#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status

echo "Starting container entrypoint..."

echo "Initializing Mongo database..."
python scripts/init_mongodb.py

echo "Running server application..."
python scripts/run_server.py

echo "All scripts finished."
