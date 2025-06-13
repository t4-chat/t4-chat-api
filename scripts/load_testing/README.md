# API Load Testing

This directory contains Locust load tests for the API endpoints.

## Setup

Install required packages:

```bash
pip install locust sseclient-py
```

## Running Tests

From the project root directory:

```bash
# Run with web UI (default)
python scripts/run_load_tests.py

# Run with a specific token
python scripts/run_load_tests.py --token "your-auth-token"

# Run headless with specific parameters
python scripts/run_load_tests.py --headless -u 100 -r 10 -t 5m --token "your-auth-token"
```

Then open http://localhost:8089 in your browser to access the Locust web interface.

## Configuration

- `-u` or `--users`: Number of concurrent users
- `-r` or `--spawn-rate`: Rate at which users are spawned (users per second)
- `-t` or `--run-time`: Duration of the test (e.g., 1m, 5m, 1h)
- `--host`: API host to test against (default: http://localhost:8000)
- `--token`: Authentication token (default: "<token>")

## Authentication

The tests use Bearer token authentication. You can provide your token using the `--token` parameter 
or by setting the `LOCUST_AUTH_TOKEN` environment variable.

## Adding New Tests

1. Create new task classes in separate modules (like `chat_tasks.py`)
2. Import and combine them in `locustfile.py`

See [Locust documentation](https://docs.locust.io/) for more details. 