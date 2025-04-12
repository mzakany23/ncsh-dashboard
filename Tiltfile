# Tiltfile for NC Soccer Analytics Dashboard
# This file configures Tilt to automatically rebuild and restart your containers during development

# Load docker-compose configuration
docker_compose('./docker-compose.yml')

# Watch for changes in these directories and rebuild when they change
watch_file('./src')
watch_file('./app.py')
watch_file('./requirements.txt')
watch_file('./Dockerfile')
watch_file('./entrypoint.sh')

# Configure resource settings for each service
dc_resource('analytics', 
    labels=['app'],
    auto_init=True,
    trigger_mode=TRIGGER_MODE_AUTO
)

dc_resource('dashboard', 
    labels=['app'],
    auto_init=True,
    trigger_mode=TRIGGER_MODE_AUTO
)

# Print helpful message when Tilt starts
print("""
-----------------------------------------------------------------
🚀 NC Soccer Analytics Dashboard Development Environment

Tilt is now managing your development environment!
- Local dashboard: http://localhost:8050
- Tilt UI: http://localhost:10350

Changes to your code will automatically trigger rebuilds.
-----------------------------------------------------------------
""")
