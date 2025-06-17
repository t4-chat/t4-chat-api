# t4-chat-api

A FastAPI-based AI API service with PostgreSQL database integration.

## Prerequisites

- Conda (Miniconda or Anaconda)
- PostgreSQL
- Docker and Docker Compose (optional, for containerized setup)

## Local Setup

1. Clone the repository:
```bash
git clone https://github.com/t4-chat/t4-chat-api
cd t4-chat-api
```

2. Create and activate a Conda environment:
```bash
conda create -n t4-chat-api python=3.11
conda activate t4-chat-api
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following content:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/t4-chat
```

## Database Setup

### Using Docker (Recommended)
1. Start the PostgreSQL database using Docker Compose:
```bash
sh docker-compose.sh
```

### Manual Setup
1. Create a PostgreSQL database named `t4-chat`
2. Update the `DATABASE_URL` in `.env` if using different credentials

## Running Migrations

### Generating Migrations
After making changes to database models (in `src/storage/models/`), generate a new migration:
```bash
alembic revision --autogenerate -m "description of your changes"
```
Review the generated migration file in `src/storage/migrations/versions/` before applying.

### Applying & Rolling Back
Apply all pending migrations:
```bash
alembic upgrade head
```

Rollback the latest migration:
```bash
alembic downgrade -1
```

Other useful migration commands:
```bash
alembic current    # Show current revision
alembic history    # Show migration history
alembic downgrade base  # Rollback all migrations
```

## Running the Application

### Local Development
```bash
uvicorn src.main:app --reload --port 9001
```

### Using Docker Compose
```bash
docker-compose up -d
```

The API will be available at `http://localhost:9001`

## API Documentation

Once the application is running, you can access:
- Swagger UI documentation: `http://localhost:9001/docs`

## Development

To create new database migrations:
```bash
alembic revision --autogenerate -m "description of changes"
alembic upgrade head
```

To seed database with data
```
python scripts/setup_test_environment.py
```
