# Dependency Injection System

This directory contains the dependency injection configuration for the application using the `dependency-injector` library.

## Structure

- `containers.py`: Main container definitions that wire up all dependencies
- `providers/`: Directory containing individual providers for different parts of the application
  - `settings.py`: Provider for application settings
  - `database.py`: Provider for database connections

## How It Works

The dependency injection system allows us to:

1. Define dependencies in a centralized location
2. Inject dependencies into classes without tightly coupling them
3. Easily swap implementations for testing
4. Manage object lifecycles efficiently

## Usage in Routes

In route handlers, use the `@inject` decorator and `Depends(Provide[AppContainer.some_service])` pattern:

```python
@router.get("/items/{item_id}")
@inject
async def get_item(
    item_id: str,
    service: SomeService = Depends(Provide[AppContainer.some_service])
):
    return service.get_item(item_id)
```

## Container Wiring

The container is wired to various modules in `main.py`:

```python
container.wire(
    modules=[
        "src.api.routes.module1",
        "src.api.routes.module2",
        # other modules
    ]
)
```

## Adding New Services

1. Create your service class with dependencies in the constructor
2. Configure the service in `src/containers/containers.py` with its dependencies
3. Wire the module that uses the service in `main.py`
4. Use `@inject` and `Depends(Provide[AppContainer.your_service])` in route handlers 