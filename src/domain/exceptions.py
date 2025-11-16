from typing import Dict, Any, Optional

class DomainException(Exception):
    """Base domain exception with Sfera-compliant formatting"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or "DOMAIN_ERROR"
        self.details = details or {}
        super().__init__(self.message)
    
    def to_sfera_format(self, service_name: str = "petrovich") -> Dict[str, Any]:
        """Convert exception to Sfera response format"""
        return {
            "headers": {
                "sender": service_name,
                "status": "error"
            },
            "body": {
                "error": self.message,
                "error_code": self.error_code,
                "status": "error"
            },
            "extra": {
                "details": self.details,
                "exception_type": self.__class__.__name__
            }
        }


class SessionCreationError(DomainException):
    """Failed to create session"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SESSION_CREATION_FAILED",
            details=details or {}
        )


class SessionBlockedError(DomainException):
    """Session is blocked or invalid"""
    
    def __init__(self, message: str = "Session blocked or invalid", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SESSION_BLOCKED",
            details=details or {}
        )


class InvalidDataError(DomainException):
    """Invalid input data provided"""
    
    def __init__(self, message: str = "Invalid input data", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="INVALID_DATA",
            details=details or {}
        )


class SearchError(DomainException):
    """Search operation failed"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SEARCH_FAILED",
            details=details or {}
        )


class SourceParseError(DomainException):
    """Failed to parse source response"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SOURCE_PARSE_ERROR",
            details=details or {}
        )


class ValidationError(DomainException):
    """Data validation failed"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details or {}
        )


class ServiceUnavailableError(DomainException):
    """External service unavailable"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            details=details or {}
        )
        

class NoDataError(DomainException):
    """No data found (equivalent to legacy NoDataEvent)"""
    
    def __init__(self, message: str = "No data found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="NO_DATA",
            details=details or {}
        )

class SessionEmptyError(DomainException):
    """Session is empty (equivalent to legacy SessionEmpty)"""
    
    def __init__(self, message: str = "Session is empty", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SESSION_EMPTY",
            details=details or {}
        )