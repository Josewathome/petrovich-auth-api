import asyncio
import logging
from typing import Dict, Any
from src.domain.models import SearchType
from src.domain.services import SessionAdapter, PayloadAdapter, ResponseAdapter
from src.domain.exceptions import SessionBlockedError, SessionCreationError, SearchError
from src.infrastructure.http_client import PetrovichHTTPClient
from src.infrastructure.session_store import InMemorySessionStore
from src.core.response_helper import ResponseHelper
from src.domain.exceptions import NoDataError
from src.core.config import settings

logger = logging.getLogger(__name__)

# In src/application/services.py - Update the search method
class PetrovichSearchService:
    """Application service coordinating the search workflow with configurable session retries"""
    
    def __init__(self):
        self.session_store = InMemorySessionStore()
        self.settings = settings
        self.response_helper = ResponseHelper()
    
    async def search(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main search method with session retry logic and request delay
        """
        try:
            search_data, search_type = PayloadAdapter.parse_payload(payload)
            
            async with PetrovichHTTPClient(self.settings) as client:
                attempt = 0
                last_exception = None

                while attempt <= self.settings.MAX_SESSION_RETRIES:
                    attempt += 1
                    try:
                        # Get or create session
                        session_data = await self._get_or_create_session(client)
                        
                        # Execute search
                        response_data = await client.search(search_data, search_type.value, session_data.cookies)
                        
                        # LEGACY BEHAVIOR: This returns a list [{"Result": "...", "ResultCode": "..."}]
                        legacy_result = ResponseAdapter.parse_search_response(response_data)
                        
                        # Convert legacy list format to Sfera format
                        return self.response_helper.from_legacy_response(
                            legacy_result,
                            extra={
                                "raw_data": response_data,
                                "search_type": search_type.value,
                                "searched_value": search_data,
                                "session_retries": attempt - 1
                            }
                        )
                        
                    except SessionBlockedError as e:
                        last_exception = e
                        logger.warning(f"Session blocked on attempt {attempt}, retrying after delay...")
                        # Wait before retrying
                        await asyncio.sleep(self.settings.REQUEST_DELAY)
                        # Create a new session before retry
                        await self._create_new_session(client)
                        continue  # retry with new session
                    
                    except NoDataError as e:
                        # LEGACY BEHAVIOR: NoDataError means "not found"
                        logger.info(f"No data found for {search_type.value}: {search_data}")
                        return self.response_helper.not_found_response(
                            details={
                                "payload": payload,
                                "search_attempted": True,
                                "search_retries": attempt - 1,
                                "searched_value": search_data,
                                "search_type": search_type.value
                            }
                        )
                    
                    except Exception as e:
                        last_exception = e
                        if attempt <= self.settings.MAX_SESSION_RETRIES:
                            logger.warning(f"Search failed on attempt {attempt}, retrying after delay...")
                            await asyncio.sleep(self.settings.REQUEST_DELAY)
                            continue
                        else:
                            logger.error(f"Search failed after {attempt} attempts: {e}")
                            raise

                # If all retries failed
                logger.error(f"All {self.settings.MAX_SESSION_RETRIES} session retries failed.")
                raise last_exception or SessionBlockedError("Session blocked and max retries exceeded")
                    
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return self.response_helper.error_response(
                exception=e,
                extra={
                    "payload": payload,
                    "search_attempted": True,
                    "search_retries": self.settings.MAX_SESSION_RETRIES
                }
            )
    
    async def _get_or_create_session(self, client: PetrovichHTTPClient):
        """Get existing session or create new one"""
        session_data = await self.session_store.get_any_session()
        if not session_data:
            session_data = await self._create_new_session(client)
        return session_data
    
    async def _create_new_session(self, client: PetrovichHTTPClient):
        """Create new authenticated session"""
        logger.info("Creating new session...")
        
        try:
            # Step 1: Get frontend page
            frontend_html = await client.get_frontend_page()
            cookies, params = SessionAdapter.parse_frontend_response(frontend_html)
            
            # Step 2: Initialize session
            response_cookies = await client.initialize_session(params, cookies)
            session_cookies = SessionAdapter.parse_session_cookies(response_cookies)
            
            from src.domain.models import SessionData
            session_data = SessionData(
                cookies=session_cookies,
                params=params
            )
            
            # Store session
            await self.session_store.create_session(session_data)
            logger.info(f"Session created successfully with cookies: {list(session_cookies.keys())}")
            
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise SessionCreationError(
                f"Session creation failed: {str(e)}",
                {"attempt": "session_creation", "error_details": str(e)}
            )