#!/bin/bash
# Setup script for Streamlit Cloud deployment

# Increase inotify limits to prevent EMFILE errors
echo "Increasing inotify limits..."

# Set higher limits for inotify instances
echo 524288 > /proc/sys/fs/inotify/max_user_instances
echo 524288 > /proc/sys/fs/inotify/max_user_watches
echo 524288 > /proc/sys/fs/inotify/max_queued_events

# Alternative: try to set limits via sysctl if available
if command -v sysctl &> /dev/null; then
    sysctl -w fs.inotify.max_user_instances=524288
    sysctl -w fs.inotify.max_user_watches=524288
    sysctl -w fs.inotify.max_queued_events=524288
fi

echo "Setup complete!"
