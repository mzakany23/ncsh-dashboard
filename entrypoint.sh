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

# Backup data directory (not mounted by LiteFS)
BACKUP_DATA_DIR="/app/backup_data"

# Check if we're running in a Docker/Fly.io environment
if [ -d "/app/data" ]; then
  echo "Running in production environment with mounted data directory"

  # Ensure data directory has correct permissions
  chmod 755 /app/data

  # Handle team_groups.db: Merge if both exist, otherwise use backup if available
  if [ -f "/app/data/team_groups.db" ]; then
    echo "Database file exists in mounted volume, size: $(stat -c%s /app/data/team_groups.db) bytes"
    echo "File permissions: $(stat -c%a /app/data/team_groups.db)"

    if [ -f "$BACKUP_DATA_DIR/team_groups.db" ]; then
      echo "Backup database found, size: $(stat -c%s $BACKUP_DATA_DIR/team_groups.db) bytes"
      echo "Merging team groups from backup database (S3 version) to volume database"
      python /app/scripts/merge_team_groups.py "/app/data/team_groups.db" "$BACKUP_DATA_DIR/team_groups.db"

      # Ensure appropriate permissions
      chmod 644 "/app/data/team_groups.db"
    else
      echo "No backup database found, using existing volume database"
    fi
  else
    echo "Database file does not exist in mounted volume"
    if [ -f "$BACKUP_DATA_DIR/team_groups.db" ]; then
      echo "Copying database from backup (S3 version)"
      cp "$BACKUP_DATA_DIR/team_groups.db" "/app/data/team_groups.db"
      chmod 644 "/app/data/team_groups.db"
    else
      echo "WARNING: No database file found in backup. A new empty database will be created."
    fi
  fi

  # Check if parquet file exists, if not copy from backup
  if [ -f "$PARQUET_FILE" ]; then
    echo "Parquet file exists, size: $(stat -c%s $PARQUET_FILE) bytes"
    if [ -f "$BACKUP_DATA_DIR/data.parquet" ]; then
      echo "Updating parquet file from backup (S3 version)"
      cp "$BACKUP_DATA_DIR/data.parquet" "$PARQUET_FILE"
      chmod 644 "$PARQUET_FILE"
      echo "Updated parquet file, new size: $(stat -c%s $PARQUET_FILE) bytes"
    else
      echo "No backup parquet file found, using existing volume parquet file"
    fi
  else
    echo "Parquet file not found at $PARQUET_FILE"
    if [ -f "$BACKUP_DATA_DIR/data.parquet" ]; then
      echo "Copying Parquet file from backup"
      cp "$BACKUP_DATA_DIR/data.parquet" "$PARQUET_FILE"
      chmod 644 "$PARQUET_FILE"
      echo "Copied Parquet file, size: $(stat -c%s $PARQUET_FILE) bytes"
    else
      echo "ERROR: Parquet file not found in backup. Cannot continue."
      exit 1
    fi
  fi
else
  echo "Running in development environment"
  mkdir -p /app/data
fi

# Start the Dash application
echo "Starting Dash application with Gunicorn..."
cd /app && gunicorn -c gunicorn.conf.py app:server