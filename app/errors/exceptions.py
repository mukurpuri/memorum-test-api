from typing import Optional, Dict, Any
from app.errors.codes import ErrorCode


class AppException(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details,
            }
        }


class ValidationError(AppException):
    def __init__(
        self,
        message: str = "Validation failed",
        code: ErrorCode = ErrorCode.VALIDATION_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(code, message, 400, details)


class NotFoundError(AppException):
    def __init__(
        self,
        message: str = "Resource not found",
        code: ErrorCode = ErrorCode.NOT_FOUND,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(code, message, 404, details)


class AuthenticationError(AppException):
    def __init__(
        self,
        message: str = "Authentication required",
        code: ErrorCode = ErrorCode.AUTHENTICATION_REQUIRED,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(code, message, 401, details)


class AuthorizationError(AppException):
    def __init__(
        self,
        message: str = "Access denied",
        code: ErrorCode = ErrorCode.AUTHORIZATION_DENIED,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(code, message, 403, details)


class ConflictError(AppException):
    def __init__(
        self,
        message: str = "Resource conflict",
        code: ErrorCode = ErrorCode.CONFLICT,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(code, message, 409, details)


class RateLimitError(AppException):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        code: ErrorCode = ErrorCode.RATE_LIMIT_EXCEEDED,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(code, message, 429, details)
