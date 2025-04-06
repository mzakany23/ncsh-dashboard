import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8050"
backlog = 2048

# Use fewer workers to reduce SQLite contention
workers = 3  # Fixed number instead of CPU-based formula
worker_class = 'sync'  # Change from eventlet to sync to avoid context issues
worker_connections = 1000
timeout = 30
keepalive = 2

# Preload the app to avoid multiple SQLite connections during fork
preload_app = True

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'soccer-analytics'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Header size limits
limit_request_line = 8190
limit_request_fields = 32768
limit_request_field_size = 32768

# Worker initialization
def post_fork(server, worker):
    print(f"Worker {worker.pid} started, parent: {os.getppid()}")

def on_starting(server):
    print("Gunicorn server is starting with config:")
    print(f"- Worker class: {worker_class}")
    print(f"- Workers: {workers}")
    print(f"- Preload app: {preload_app}")
    print(f"- Bind: {bind}")

def worker_abort(worker):
    print(f"Worker {worker.pid} was aborted")