#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status

echo "Starting container entrypoint..."

echo "Running Client application..."
python scripts/run_client.py

echo "All scripts finished."
