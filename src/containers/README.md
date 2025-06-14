# Dependency Injection System

This directory contains the dependency injection configuration for the application using FastAPI's built-in dependency injection system.

## Structure

- `di.py`: Centralized dependency injection configuration file with provider functions for all services

## How It Works

The dependency injection system allows us to:

1. Define dependencies in a centralized location
2. Inject dependencies into routes without tightly coupling them
3. Easily swap implementations for testing
4. Manage service dependencies efficiently through FastAPI's dependency resolution

## Usage in Routes

In route handlers, use the services from di.py directly with type annotations:

```python
from fastapi import APIRouter
from src.containers.di import user_service

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/current")
async def get_current_user(service: user_service):
    return await service.get_user_by_id()
```

## Adding New Services

1. Create your service class with dependencies in the constructor
2. Configure the service in `src/containers/di.py` with its dependencies:

```python
def get_new_service(
    db: AsyncSession = Depends(get_db_session),
    context: Context = Depends(get_context),
    other_service: OtherService = Depends(get_other_service)
) -> NewService:
    return NewService(context=context, db=db, other_service=other_service)

new_service = Annotated[NewService, Depends(get_new_service)]
```

3. Import the service in your route files and use it with type annotation: `service: new_service`

## Context Handling

The `get_context` dependency extracts the user_id from the request and creates a Context object, which is then injected into services. This ensures the proper context (like user ID) is available when needed. 