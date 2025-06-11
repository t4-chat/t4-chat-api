# Logging System

This document outlines the centralized logging system for the application.

## Usage

### Basic Usage

To use logging in any file:

```python
from src.utils.logging_config import get_logger

# Create a logger for the current module
logger = get_logger(__name__)

# Use the logger
logger.info("This is an info message")
logger.error("This is an error message")
logger.debug("This is a debug message")
```

### Configuring Logging

Logging is configured in `main.py` using the `configure_logging` function. The default configuration:

- Logs to console (stdout)
- Logs to a file named `app.log`
- Uses INFO level
- Uses a standard format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

To customize the logging configuration, modify the parameters in `main.py`:

```python
from src.utils.logging_config import configure_logging

configure_logging(
    level=logging.DEBUG,  # Change log level
    log_file='custom.log',  # Change log file name
    log_format='%(asctime)s - %(levelname)s - %(message)s',  # Custom format
    enable_console=True  # Set to False to disable console logging
)
```

## Integration with Datadog

To integrate with Datadog, you can extend the `logging_config.py` file to include a Datadog handler.

Example implementation (requires `datadog` package):

```python
def configure_datadog_logging(api_key, app_name):
    from datadog_logger import DatadogLogHandler
    
    datadog_handler = DatadogLogHandler(
        api_key=api_key,
        source=app_name
    )
    
    # Add the Datadog handler to the root logger
    logging.getLogger().addHandler(datadog_handler)
``` 