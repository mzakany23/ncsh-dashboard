#!/bin/bash
echo "Starting NC Soccer Analytics Dashboard"

# Activate virtual environment
source /app/venv/bin/activate

# Explicitly set environment variables
export PARQUET_FILE=${PARQUET_FILE:-"/app/data/data.parquet"}
export AUTH_FLASK_ROUTES=${AUTH_FLASK_ROUTES:-"true"}

# Log important environment settings
echo "Environment:"
echo "- PARQUET_FILE: $PARQUET_FILE"
echo "- AUTH_FLASK_ROUTES: $AUTH_FLASK_ROUTES"
echo "- AUTH0_CALLBACK_URL: $AUTH0_CALLBACK_URL"
echo "- PYTHONPATH: $PYTHONPATH"
echo "- VIRTUAL_ENV: $VIRTUAL_ENV"

# Create assets directory
mkdir -p /app/assets

# Start Nginx
echo "Starting Nginx..."
service nginx start

# Check if we're running in a Docker/Fly.io environment
if [ -d "/app/data" ]; then
  echo "Running in production environment with mounted data directory"

  # Ensure data directory has correct permissions
  chmod 755 /app/data

  # Check if database exists
  if [ -f "/app/data/team_groups.db" ]; then
    echo "Database file exists, size: $(stat -c%s /app/data/team_groups.db) bytes"
    echo "File permissions: $(stat -c%a /app/data/team_groups.db)"
    chmod 644 /app/data/team_groups.db
  else
    echo "Database file does not exist, will be created during initialization"
  fi

  # Check if parquet file exists
  if [ -f "$PARQUET_FILE" ]; then
    echo "Parquet file exists, size: $(stat -c%s $PARQUET_FILE) bytes"
  else
    echo "ERROR: Parquet file not found at $PARQUET_FILE"
    exit 1
  fi
else
  echo "Running in development environment"
  mkdir -p /app/data
fi

# Start the Dash application
echo "Starting Dash application with Gunicorn..."
cd /app && gunicorn -c gunicorn.conf.py app:server