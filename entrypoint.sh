#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Run setup script to initialize test data
echo "Running setup script..."
python scripts/setup_test_environment.py

# Start the application
echo "Starting application..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 