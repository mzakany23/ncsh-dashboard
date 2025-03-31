FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Create directory for data and copy data files
RUN mkdir -p /app/data
COPY data/data.parquet /app/data/
COPY data/team_groups.db /app/data/

# Install uv using pip
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml .
COPY gunicorn.conf.py .
COPY app.py .
COPY src /app/src

# Install dependencies using uv and add eventlet
RUN uv pip install --system . && \
    pip install --no-cache-dir eventlet

# Create Nginx configuration without basic auth
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    \
    # Increase header size limits \
    large_client_header_buffers 4 16k; \
    client_header_buffer_size 16k; \
    client_body_buffer_size 16k; \
    fastcgi_buffers 16 16k; \
    fastcgi_buffer_size 32k; \
    proxy_buffer_size 128k; \
    proxy_buffers 4 256k; \
    proxy_busy_buffers_size 256k; \
    \
    # Forward all traffic to Dash app without auth \
    location / { \
        proxy_pass http://localhost:8050; \
        proxy_http_version 1.1; \
        proxy_set_header Upgrade $http_upgrade; \
        proxy_set_header Connection "upgrade"; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
        proxy_read_timeout 86400; \
        proxy_cache_bypass $http_upgrade; \
    } \
}' > /etc/nginx/conf.d/dash.conf

# Create improved entrypoint script with better debugging
RUN echo '#!/bin/bash \n\
echo "Starting NC Soccer Analytics Dashboard" \n\
\n\
# Explicitly set the environment variables needed by the app \n\
export PARQUET_FILE=${PARQUET_FILE:-"/app/data/data.parquet"} \n\
export AUTH_FLASK_ROUTES=${AUTH_FLASK_ROUTES:-"true"} \n\
\n\
# Log important environment settings \n\
echo "Environment:" \n\
echo "- PARQUET_FILE: $PARQUET_FILE" \n\
echo "- AUTH_FLASK_ROUTES: $AUTH_FLASK_ROUTES" \n\
echo "- AUTH0_CALLBACK_URL: $AUTH0_CALLBACK_URL" \n\
echo "- PYTHONPATH: $PYTHONPATH" \n\
\n\
# Check if data files exist \n\
if [ ! -f "$PARQUET_FILE" ]; then \n\
    echo "ERROR: Parquet file not found at $PARQUET_FILE" \n\
    exit 1 \n\
fi \n\
\n\
if [ ! -f "/app/data/team_groups.db" ]; then \n\
    echo "WARNING: team_groups.db not found, will be created by the app" \n\
fi \n\
\n\
# Create assets directory if it doesn\'t exist \n\
mkdir -p /app/assets \n\
\n\
# Start Nginx \n\
echo "Starting Nginx..." \n\
service nginx start \n\
\n\
# Start Dash app with Gunicorn config \n\
echo "Starting Dash application..." \n\
cd /app && gunicorn -c gunicorn.conf.py app:server \n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Expose ports
EXPOSE 80 8050

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PARQUET_FILE=/app/data/data.parquet

# Run the entrypoint script
CMD ["/app/entrypoint.sh"]

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8050/ || exit 1