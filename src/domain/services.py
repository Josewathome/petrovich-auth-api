import re
import logging
from urllib import parse
from typing import Dict, Any, Tuple, List
from src.domain.models import SessionData, SearchType

from src.domain.exceptions import SourceParseError, SearchError
from src.core.response_helper import ResponseHelper
from src.domain.exceptions import InvalidDataError

logger = logging.getLogger(__name__)

class SessionAdapter:
    """Domain service for session data adaptation"""
    
    @staticmethod
    def parse_frontend_response(response_text: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Parse frontend response to extract session initialization parameters
        """
        urls = re.findall(r'src="(.*?nonce.*?)">', response_text)
        if not urls:
            raise SourceParseError("Источник не отдал ссылку для генерации сессии")
        
        url = urls[0]
        logger.info(f"Found session URL: {url}")
        
        parsed_url = parse.urlsplit(url)
        params = parse.parse_qs(parsed_url.query)
        clean_params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
        
        return {}, clean_params

    @staticmethod
    def parse_session_cookies(response_cookies) -> Dict[str, str]:
        """
        Parse and filter session cookies from response
        """
        cookies_dict = {}
        allowed_cookies = ["SIK", "SIV"]
        allowed_masks = [
            {"key": r"^[A-Za-z\d]_?[A-Za-z\d\-_]{7,}$", "value": r"^A.*"}
        ]
        
        for key, morsel in response_cookies.items():
            value = morsel.value

            # Direct allowlist
            if key in allowed_cookies:
                cookies_dict[key] = value
                logger.info(f"Added allowed cookie: {key}")
                continue
            
            # Regex pattern matching
            for mask in allowed_masks:
                if (re.match(mask["key"], key) and 
                    re.match(mask["value"], value)):
                    cookies_dict[key] = value
                    logger.info(f"Added pattern-matched cookie: {key}")
                    break
        
        return cookies_dict


class PayloadAdapter:
    """Domain service for payload type detection - PRESERVES LEGACY LOGIC"""
    
    ALLOWED_TYPES = {
        "nick": SearchType.LOGIN,
        "phone": SearchType.PHONE, 
        "email": SearchType.EMAIL
    }
    
    @staticmethod
    def parse_payload(payload: Dict[str, Any]) -> Tuple[str, SearchType]:
        """
        Parse payload to extract data and determine type
        PRESERVES EXACT LEGACY LOGIC from PayloadType.parse()
        """
        if not isinstance(payload, dict):
            return payload, SearchType.PHONE  # Legacy default
        
        # Legacy logic: search for allowed keys in payload
        for key, search_type in PayloadAdapter.ALLOWED_TYPES.items():
            if payload.get(key):
                return payload[key], search_type
        
        raise InvalidDataError("No valid search type found in payload")

class ResponseAdapter:
    """Domain service for response processing - PRESERVES LEGACY LOGIC"""
    @staticmethod
    def parse_search_response(response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse and validate search response - PRESERVES EXACT LEGACY LOGIC
        Returns EXACT same format as legacy ResponseAdapter.cast()
        """
        is_used = response_data.get('data', {}).get('isUsed')
        
        if is_used:
            # LEGACY FORMAT: [{"Result": "Найден", "ResultCode": "FOUND"}]
            return [{"Result": "Найден", "ResultCode": "FOUND"}]
        elif is_used is False:
            from src.domain.exceptions import NoDataError
            # LEGACY BEHAVIOR: raise NoDataEvent for not found
            raise NoDataError("No data found")
        else:
            raise SearchError(
                f"Unknown response format from target service",
                {"response_data": response_data}
            )