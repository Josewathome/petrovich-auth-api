from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from enum import Enum

class SearchType(str, Enum):
    PHONE = "phone"
    EMAIL = "email"
    LOGIN = "login"

class SearchResult(BaseModel):
    result: str
    result_code: str
    raw_data: Dict[str, Any]

class SessionData(BaseModel):
    cookies: Dict[str, str]
    params: Dict[str, str]

class ValidationResult(BaseModel):
    request_data: str
    type: str
    clean_data: str
    extra: Optional[Dict[str, Any]] = None