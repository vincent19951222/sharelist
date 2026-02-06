import logging
import json
import time
from datetime import datetime
from contextvars import ContextVar
from typing import Optional, Dict, Any

# Context variable to hold request-scoped data (roomId, userId, etc.)
_log_context: ContextVar[Dict[str, Any]] = ContextVar("log_context", default={})

class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings with context injection.
    """
    def format(self, record: logging.LogRecord) -> str:
        # 1. Basic Log Data
        log_record = {
            "time": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # 2. Add Exception Info if present
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)

        # 3. Add Context Data (from ContextVar)
        ctx = _log_context.get()
        if ctx:
            log_record["context"] = ctx

        # 4. Add Extra Data (passed via extra={...})
        if hasattr(record, "extra_data"):
            log_record["data"] = record.extra_data

        return json.dumps(log_record)

def setup_logger(name: str = "app") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
    return logger

class LogContext:
    """
    Context Manager to bind variables to the current execution context (async-safe).
    Usage:
        with LogContext(room_id="123", user="Alice"):
            logger.info("Something happened")
    """
    def __init__(self, **kwargs):
        self.new_ctx = kwargs
        self.token = None

    def __enter__(self):
        current = _log_context.get()
        # Merge current context with new context
        self.token = _log_context.set({**current, **self.new_ctx})
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.token:
            _log_context.reset(self.token)

# Global logger instance
logger = setup_logger("sharelist")
