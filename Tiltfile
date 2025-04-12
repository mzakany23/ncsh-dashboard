# Tiltfile for ncsh-dashboard
# This file configures Tilt to monitor and rebuild your Docker services automatically

# Load Docker Compose file
docker_compose('./docker-compose.yml')

# Configure resources for each service
dc_resource('analytics', trigger_mode=TRIGGER_MODE_AUTO)
# Add file watching for analytics service
watch_file('./src')
watch_file('./Dockerfile')

dc_resource('dashboard', trigger_mode=TRIGGER_MODE_AUTO)
# Add file watching for dashboard service
watch_file('./src')
watch_file('./Dockerfile')
watch_file('./data')

# Add a helpful message when Tilt starts
local_resource(
    'welcome',
    'echo "Welcome to ncsh-dashboard development environment!\nAnalytics: http://localhost:8050\nDashboard: http://localhost:8090"',
    auto_init=True
)

# Configure resource settings
config.set_enabled_resources(['welcome', 'analytics', 'dashboard'])