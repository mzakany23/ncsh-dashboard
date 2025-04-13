# Tiltfile for ncsh-dashboard
# This file configures Tilt to monitor and rebuild your Docker services automatically

# Watch files for changes
# Source code
watch_file('./src')
# Docker configuration
watch_file('./Dockerfile')
# Data files
watch_file('./data')
# Version information
watch_file('./CHANGELOG.md')
# Scripts that might affect chart data
watch_file('./scripts')
# Documentation files including chart implementation plans
watch_file('./*.md')
# Additional files for chart updates
watch_file('./entrypoint.sh')
watch_file('./requirements.txt')
watch_file('./pyproject.toml')
watch_file('./gunicorn.conf.py')
watch_file('./.env.example')

# Load Docker Compose file
docker_compose('./docker-compose.yml')

# Configure resources for each service without the unsupported 'deps' parameter
dc_resource(
    'analytics',
    trigger_mode=TRIGGER_MODE_AUTO
)

dc_resource(
    'dashboard',
    trigger_mode=TRIGGER_MODE_AUTO
)

# Add a helpful message when Tilt starts
local_resource(
    'welcome',
    'echo "Welcome to ncsh-dashboard development environment!\nAnalytics: http://localhost:8050\nDashboard: http://localhost:8090"',
    auto_init=True
)

# Configure resource settings
config.set_enabled_resources(['welcome', 'analytics', 'dashboard'])