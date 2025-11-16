import aiohttp
import logging
from typing import Dict, Any, Optional
from src.domain.exceptions import (
    SessionBlockedError, 
    InvalidDataError, 
    SearchError, 
    SourceParseError,
    ServiceUnavailableError
)
from src.core.config import settings

logger = logging.getLogger(__name__)

class PetrovichHTTPClient:
    """Infrastructure service for HTTP communication with Petrovich API"""
    
    DEFAULT_HEADERS = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "DNT": "1",
        "Origin": "https://petrovich.ru",
        "Referer": "https://petrovich.ru/cart/pre-order/fiz/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "x-requested-with": "XmlHttpRequest",
    }
    
    def __init__(self, settings):
        self.settings = settings
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.DEFAULT_HEADERS)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_frontend_page(self) -> str:
        """Get frontend page to extract session parameters"""
        logger.info(f"Requesting frontend page: {settings.PETROVICH_FRONTEND_URL}")
        
        try:
            async with self.session.get(
                settings.PETROVICH_FRONTEND_URL,
                timeout=settings.FRONTEND_TIMEOUT,
                ssl=False
            ) as response:
                if response.status != 200:
                    raise ServiceUnavailableError(
                        f"Frontend unavailable: HTTP {response.status}",
                        {"url": settings.PETROVICH_FRONTEND_URL, "status": response.status}
                    )
                return await response.text()
        except aiohttp.ClientError as e:
            raise ServiceUnavailableError(
                f"Failed to connect to frontend: {str(e)}",
                {"url": settings.PETROVICH_FRONTEND_URL, "error": str(e)}
            )
    
    async def initialize_session(self, params: Dict[str, str], cookies: Dict[str, str]) -> Dict[str, str]:
        """Initialize session with extracted parameters"""
        logger.info(f"Initializing session: {settings.PETROVICH_SESSION_URL}")
        
        try:
            async with self.session.get(
                settings.PETROVICH_SESSION_URL,
                params=params,
                cookies=cookies,
                timeout=settings.SESSION_TIMEOUT,
                ssl=False
            ) as response:
                response_text = await response.text()
                logger.info(f"Session initialization response: {response_text[:100]}...")
                
                if response.status != 200:
                    raise SessionBlockedError(
                        f"Session initialization failed: HTTP {response.status}",
                        {"url": settings.PETROVICH_SESSION_URL, "status": response.status}
                    )
                
                return response.cookies
        except aiohttp.ClientError as e:
            raise ServiceUnavailableError(
                f"Failed to initialize session: {str(e)}",
                {"url": settings.PETROVICH_SESSION_URL, "error": str(e)}
            )
    
    async def search(self, payload: str, search_type: str, cookies: Dict[str, str]) -> Dict[str, Any]:
        """Execute search request"""
        params = {
            "pet_case": settings.DEFAULT_PET_CASE,
            "city_code": settings.DEFAULT_CITY_CODE,
            "client_id": settings.DEFAULT_CLIENT_ID
        }
        
        json_data = {
            "type": search_type,  # ✅ This will be "login" for nick searches
            "login": payload      # ✅ The actual search value
        }
        
        logger.info(f"Searching for {search_type}: {payload}")
        
        try:
            async with self.session.post(
                settings.PETROVICH_SEARCH_URL,
                params=params,
                json=json_data,
                cookies=cookies,
                timeout=settings.SEARCH_TIMEOUT,
                ssl=False
            ) as response:
                response_text = await response.text()
                logger.info(f"Search response: {response_text[:200]}...")
                
                # Validate response
                self._validate_search_response(response_text, response.status)
                
                try:
                    return await response.json()
                except Exception as e:
                    raise SourceParseError(
                        f"Response is not JSON: {response_text}",
                        {"response_text": response_text, "error": str(e)}
                    )
        except aiohttp.ClientError as e:
            raise ServiceUnavailableError(
                f"Search request failed: {str(e)}",
                {"url": settings.PETROVICH_SEARCH_URL, "error": str(e)}
            )
    
    def _validate_search_response(self, response_text: str, status_code: int):
        """Validate search response for errors"""
        if status_code != 200:
            raise SearchError(
                f"Search API returned HTTP {status_code}",
                {"status_code": status_code, "response_preview": response_text[:200]}
            )
        
        if "Session is broken" in response_text or "Session is not started" in response_text:
            raise SessionBlockedError(
                "Session blocked by target service",
                {"response_preview": response_text[:200]}
            )
        
        if "Некорректный" in response_text:
            raise InvalidDataError(
                "Incorrect data format rejected by target service",
                {"response_preview": response_text[:200]}
            )
        
        if "Запрос успешно выполнен" not in response_text:
            raise SearchError(
                "Request was not successful according to target service",
                {"response_preview": response_text[:200]}
            )