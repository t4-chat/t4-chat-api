import functools
import json
import traceback
from uuid import UUID

from src.services.common import errors

from src.logging.logging_config import get_logger

logger = get_logger(__name__)


def stream_error_handler(func):
    """
    Decorator for streaming functions that handles errors and formats them as SSE events.
    Works with async generator functions that yield SSE data.
    """

    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        assistant_message = None

        try:
            # Get the generator from the wrapped function
            generator = func(self, *args, **kwargs)

            # Process generator items
            async for item in generator:
                # This will be SSE formatted data
                yield item

                # Try to extract message ID if this is the first message
                if not assistant_message and "message_start" in item:
                    try:
                        # Parse the SSE data to get message ID
                        data_str = item.split("data: ")[1].strip()
                        data = json.loads(data_str)
                        if data.get("type") == "message_start" and "message" in data:
                            message_id = data["message"].get("id")
                            if message_id:
                                assistant_message = {"id": UUID(message_id)}
                    except (IndexError, json.JSONDecodeError, KeyError):
                        logger.error("Failed to parse message ID from SSE data")
                        pass

        except (errors.NotFoundError, errors.BudgetExceededError, errors.LimitsExceededError, errors.ModelApiError,
                errors.BYOKError) as e:
            error_code = e.status_code if hasattr(e, "status_code") else 500
            error_message = {"type": "error", "error": str(e), "code": error_code}
            yield f"data: {json.dumps(error_message)}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {str(e)}")
            logger.error(traceback.format_exc())
            error_message = {
                "type": "error",
                "error": "Internal server error",
                "code": 500,
            }
            yield f"data: {json.dumps(error_message)}\n\n"

        finally:
            # Always send done event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return wrapper
