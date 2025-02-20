import logging
import os
import sys
import asyncio
import time
from datetime import datetime
from fastapi import Request

# Define log directory and file path
LOG_DIR = r"E:\TrendConnect\Logging"
LOG_FILE_PATH = os.path.join(LOG_DIR, "trendconnect.log")

# Ensure the log directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Create a logger
logger = logging.getLogger("trendconnect_logger")
logger.setLevel(logging.INFO)  # Set logging level

# Formatter for logs
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

# File Handler - Stores logs in a file
file_handler = logging.FileHandler(LOG_FILE_PATH, mode="a", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console Handler - Outputs logs to the terminal
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


async def log_event(request: Request, response_status: int, execution_time: float, response_body: str = None, error: str = None):
    """
    Logs request and response details asynchronously.
    
    :param request: The incoming HTTP request
    :param response_status: HTTP response status code
    :param execution_time: Time taken to execute the request (in seconds)
    :param response_body: Optional response content (truncated for readability)
    :param error: Optional error message if an exception occurred
    """
    log_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    client_ip = request.client.host if request.client else "Unknown"
    method = request.method
    url = str(request.url)
    endpoint = request.url.path  # Extract endpoint name
    execution_time_ms = round(execution_time * 1000, 2)  # Convert to milliseconds

    log_message = (
        f"[{log_time}] - IP: {client_ip} | {method} {url} "
        f"| Endpoint: {endpoint} | Status: {response_status} | Time: {execution_time_ms} ms"
    )

    if error:
        log_message += f" | ERROR: {error}"

    if response_body:
        log_message += f" | Response: {response_body[:500]}"  # Limit response size for readability

    # Run logging in the background
    asyncio.create_task(write_log(log_message))


async def write_log(message: str):
    """
    Writes log message asynchronously to both the log file and console.
    
    :param message: The formatted log message
    """
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, logger.info, message)
