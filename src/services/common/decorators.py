import inspect
from functools import wraps
from inspect import iscoroutinefunction
from typing import Any, Callable, Type, TypeVar, Union, get_args, get_origin, get_type_hints

from pydantic import BaseModel

T = TypeVar("T")


def convert_to_dto(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that converts database models to the type specified in the return annotation.
    Works with both async and sync functions.
    Handles Optional types, Lists, and direct model-to-DTO conversions.
    """
    return_type_hints = get_type_hints(func).get("return")
    if return_type_hints is None:
        return func

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        return convert_result(result, return_type_hints)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return convert_result(result, return_type_hints)

    if iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def convert_result(result: Any, return_type: Type) -> Any:
    """Convert the result to the specified return type."""
    # Handle None result
    if result is None:
        return None

    origin = get_origin(return_type)

    # Handle Optional types
    if origin is Union:
        args = get_args(return_type)
        if type(None) in args:
            # Extract the real type from Optional
            real_type = next(arg for arg in args if arg is not type(None))
            return convert_result(result, real_type)

    # Handle List types
    elif origin is list:
        item_type = get_args(return_type)[0]
        if issubclass(item_type, BaseModel) and hasattr(item_type, "model_validate"):
            return [item_type.model_validate(item) for item in result]
        else:
            return result

    # Handle direct model to DTO conversion
    elif inspect.isclass(return_type) and issubclass(return_type, BaseModel):
        if hasattr(return_type, "model_validate"):
            return return_type.model_validate(result)

    # Return as is if no conversion needed
    return result
