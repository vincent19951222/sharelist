from enum import Enum

class ErrorCode(str, Enum):
    # Auth Errors
    AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN"
    AUTH_NO_PERMISSION = "AUTH_NO_PERMISSION"
    
    # Room Errors
    ROOM_NOT_FOUND = "ROOM_NOT_FOUND"
    ROOM_FULL = "ROOM_FULL"
    ROOM_EXPIRED = "ROOM_EXPIRED"
    
    # Business Logic Errors
    ITEM_LIMIT_REACHED = "ITEM_LIMIT_REACHED"
    INVALID_INPUT = "INVALID_INPUT"
    
    # System Errors
    DB_ERROR = "DB_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"

class AppError(Exception):
    def __init__(self, code: ErrorCode, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
