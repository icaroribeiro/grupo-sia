#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status

echo "Starting container entrypoint..."

echo "Running Server application..."
python scripts/run_server.py

echo "All scripts finished."
