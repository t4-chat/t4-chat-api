#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Run setup script to initialize test data
echo "Seeding database..."
python scripts/seed_data.py --env poc
# TODO: remove, run everything just for now to allow FE test locally
python scripts/seed_data.py --env local

echo "Database seeded successfully"

# Start the application
echo "Starting application..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 