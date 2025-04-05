#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Check if Redis is running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis server..."
    redis-server &
    sleep 2
fi

# Start Celery worker
echo "Starting Celery worker..."
celery -A agenttoast.tasks.celery worker --loglevel=info 