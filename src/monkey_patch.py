"""
Monkey patching module.
This module should be imported first to ensure proper patching before any other modules are loaded.
"""
import eventlet

# Apply monkey patch to make eventlet work properly
eventlet.monkey_patch(all=True)

print("Eventlet monkey patching completed successfully")