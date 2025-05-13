# Sole Log

A Python logging library designed for flexible, efficient, and thread-safe logging. It supports log levels, log rotation, and custom log formats (JSON and plain text).

## Features

- **Log Levels**: Supports `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`.
- **Log Rotation**: Automatically rotates log files when they exceed a configured size.
- **Flexible Formats**: Logs can be saved in either JSON or plain text format.
- **Thread-Safe**: Works safely in multi-threaded environments.
- **Customizable**: Configure whether to include timestamps in logs and whether to log to the console.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/The-Haroon/Sole_Logging.git

## Usage
```python
from solelog import SoleLog

# Create an instance of SoleLog
logger = SoleLog(
    colouredLog= True,
    logDirPath= "./",               # Log Dir Path
    logDirName= "Example",          # Log Dir Name
    maxLogSizeMb= 5,                # Max log file size before rotation
    flushInterval= 0,               # Interval to flush logs to disk
    logSaveFormat="json",           # Log file format ("json" or "txt")
    formatJsonLog= True,            # Whether to format logs as structured JSON
    showTime=True,                  # Include timestamp in logs
    showLogInConsole=True           # Whether to print log messages to the console.
)

# Logging messages at various levels
logger.DEBUG("This is a debug message")
logger.INFO("Informational message")
logger.WARNING("This is a warning")
logger.ERROR("An error occurred")
logger.CRITICAL("Critical failure!")

# Gracefully shutdown the userLogger
logger.close()
```
## Log Levels
DEBUG: Detailed information, typically useful for diagnosing problems.

INFO: General system information.

WARNING: Indicates something unexpected, but the application continues.

ERROR: For errors that might affect functionality.

CRITICAL: For severe errors that stop the program.

# Log Rotation
Log rotation occurs when the log file exceeds the specified maxLogSize. New files are created, and old ones are preserved, ensuring logs do not grow indefinitely.