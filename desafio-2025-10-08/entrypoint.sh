#!/bin/sh
set -e # Exit immediately if a command exits with a non-zero status

# Log with timestamp and context
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Docker entrypoint..."

# Log the attempt to launch the Streamlit application
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Launching Streamlit application..."

# Run the Python launcher script and capture its exit status
if ! python launch_streamlit_app.py; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Failed to launch Streamlit application"
    exit 1
fi

# Log successful completion
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Streamlit application started successfully"