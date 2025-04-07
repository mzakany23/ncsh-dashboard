# Stage 1: Builder stage for dependencies
FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster pip installs
RUN pip install --no-cache-dir uv

# Copy only dependency files first
COPY pyproject.toml .

# Install dependencies into a virtual environment
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
RUN . /app/venv/bin/activate && \
    pip install --no-cache-dir -e .

# Stage 2: Runtime stage
FROM python:3.10-slim

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    nginx \
    ca-certificates \
    fuse3 \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy LiteFS binary
COPY --from=flyio/litefs:0.5 /usr/local/bin/litefs /usr/local/bin/litefs

# Copy virtual environment from builder stage
COPY --from=builder /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/venv"

# Create directory for data and set permissions
RUN mkdir -p /app/data && chmod 755 /app/data
# Create a backup directory that won't be affected by volume mounts
RUN mkdir -p /app/backup_data && chmod 755 /app/backup_data

# Copy application files
COPY gunicorn.conf.py .
COPY app.py .
COPY src /app/src
COPY litefs.yml /etc/litefs.yml
COPY data/data.parquet /app/data/data.parquet
COPY data/team_groups.db /app/data/team_groups.db
# Also copy to backup directory
COPY data/data.parquet /app/backup_data/data.parquet
COPY data/team_groups.db /app/backup_data/team_groups.db
COPY entrypoint.sh /app/entrypoint.sh

# Set executable permission for entrypoint script
RUN chmod +x /app/entrypoint.sh

# Verify data files exist and set permissions
RUN ls -la /app/data/data.parquet && \
    ls -la /app/data/team_groups.db && \
    chmod 644 /app/data/data.parquet && \
    chmod 644 /app/data/team_groups.db

# Create Nginx configuration
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