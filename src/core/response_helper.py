from typing import Dict, Any, Optional,List
from src.domain.exceptions import DomainException
from datetime import datetime, timezone
from src.core.config import settings

def current_utc_timestamp() -> str:
    """Return current UTC time in ISO 8601 'Z' format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

# processed_at
class ResponseHelper:
    """Helper class for creating Sfera-compliant responses"""
    
    @staticmethod
    def success_response(
        data: Dict[str, Any],
        service_name: str = "petrovich",
        extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create successful Sfera response"""
        return {
            "headers": {
                "sender": settings.SERVICE_NAME,
                "status": "success",
                "processed_at" : current_utc_timestamp()
            },
            "body": {
                **data,
                "status": "success"
            },
            "extra": extra or {}
        }
    
    @staticmethod
    def error_response(
        exception: Exception,
        service_name: str = "petrovich",
        extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create error Sfera response"""
        if isinstance(exception, DomainException):
            return exception.to_sfera_format(service_name)
        else:
            # For non-domain exceptions, create a generic error response
            return {
                "headers": {
                    "sender": settings.SERVICE_NAME,
                    "status": "error",
                    "processed_at" : current_utc_timestamp()
                },
                "body": {
                    "error": str(exception),
                    "error_code": "INTERNAL_ERROR",
                    "status": "error"
                },
                "extra": {
                    "details": extra or {},
                    "exception_type": exception.__class__.__name__
                }
            }
    
    @staticmethod
    def not_found_response(
        service_name: str = "petrovich",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create not found Sfera response"""
        return {
            "headers": {
                "sender": settings.SERVICE_NAME,
                "status": "success",  # Not found is a valid result, not an error
                "processed_at" : current_utc_timestamp()
            },
            "body": {
                "result": "Не найден",
                "result_code": "NOT_FOUND",
                "status": "success"
            },
            "extra": details or {}
        }
    
    @staticmethod
    def found_response(
        service_name: str = "petrovich",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create found Sfera response"""
        return {
            "headers": {
                "sender": settings.SERVICE_NAME,
                "status": "success",
                "processed_at" : current_utc_timestamp()
            },
            "body": {
                "result": "Найден",
                "result_code": "FOUND",
                "status": "success"
            },
            "extra": details or {}
        }
        
    @staticmethod
    def from_legacy_response(legacy_data: List[Dict[str, Any]], service_name: str = "petrovich", extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Convert legacy response format to Sfera format
        Handles the legacy list format: [{"Result": "...", "ResultCode": "..."}]
        """
        if not legacy_data or not isinstance(legacy_data, list):
            return ResponseHelper.not_found_response(service_name, details=extra)
        
        legacy_item = legacy_data[0]  # Legacy always returns list with one item
        
        # Map legacy keys to Sfera format
        result = legacy_item.get("Result", "")
        result_code = legacy_item.get("ResultCode", "")
        
        if result_code == "FOUND":
            return ResponseHelper.found_response(service_name, details=extra)
        elif result_code == "NOT_FOUND":
            return ResponseHelper.not_found_response(service_name, details=extra)
        else:
            # Fallback for unknown result codes
            return {
                "headers": {
                    "sender": settings.SERVICE_NAME,
                    "status": "success"
                },
                "body": {
                    "result": result,
                    "result_code": result_code,
                    "status": "success"
                },
                "extra": extra or {}
            }
    
    @staticmethod
    def validator_error_response(
        exception: Exception,
        service_name: str = "petrovich",
        extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create error response specifically for Validator IS failures"""
        return {
            "headers": {
                "sender": settings.SERVICE_NAME,
                "status": "error",
                "processed_at" : current_utc_timestamp()
            },
            "body": {
                "error": "Validation service unavailable",
                "error_code": "VALIDATOR_UNAVAILABLE",
                "status": "error",
                "fallback_used": True
            },
            "extra": {
                "details": extra or {},
                "original_error": str(exception),
                "exception_type": exception.__class__.__name__
            }
        }