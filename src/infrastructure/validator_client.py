import aiohttp
import asyncio
import logging
from typing import Dict, Any, List, Optional
from src.core.config import settings
from src.domain.exceptions import ServiceUnavailableError, ValidationError

logger = logging.getLogger(__name__)

class ValidatorHTTPClient:
    """HTTP client for communicating with Validator IS"""
    
    def __init__(self):
        self.base_url = settings.VALIDATOR_URL
        self.timeout = settings.VALIDATOR_TIMEOUT
        self.max_retries = settings.VALIDATOR_MAX_RETRIES
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                "Content-Type": "application/json",
                "User-Agent": f"PetrovichService/{settings.SERVICE_NAME}"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def validate_queries(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Validate queries using Validator IS
        Returns list of validated payloads in legacy-compatible format
        """
        payload = {"query": queries}
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Validating {len(queries)} queries with Validator IS (attempt {attempt + 1})")
                
                async with self.session.post(
                    self.base_url,
                    json=payload,
                    ssl=False
                ) as response:
                    
                    if response.status == 200:
                        validation_results = await response.json()
                        logger.info(f"Validator IS returned {len(validation_results)} results")
                        return self._parse_validator_response(validation_results)
                    
                    elif response.status >= 500:
                        logger.warning(f"Validator IS server error: {response.status}, retrying...")
                        continue
                    
                    else:
                        error_text = await response.text()
                        raise ValidationError(
                            f"Validator IS returned status {response.status}",
                            {"response_text": error_text[:500], "attempt": attempt + 1}
                        )
                        
            except aiohttp.ClientError as e:
                logger.warning(f"Validator IS connection error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise ServiceUnavailableError(
                        f"Failed to connect to Validator IS after {self.max_retries} attempts",
                        {"error": str(e), "max_retries": self.max_retries}
                    )
            except asyncio.TimeoutError:
                logger.warning(f"Validator IS timeout (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    raise ServiceUnavailableError(
                        f"Validator IS timeout after {self.max_retries} attempts",
                        {"timeout_seconds": self.timeout, "max_retries": self.max_retries}
                    )
        
        # This should not be reached, but for safety
        raise ServiceUnavailableError("Validator IS unavailable after all retries")
    
    def _parse_validator_response(self, validation_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse Validator IS response into legacy-compatible payload format"""
        parsed_results = []
        
        for result in validation_results:
            try:
                body = result.get("body", {})
                headers = result.get("headers", {})
                
                request_data = body.get("request_data", "")
                data_type = body.get("type", "").lower()
                clean_data = body.get("clean_data", request_data)
                
                # Map Validator IS types to legacy payload format
                legacy_payload = self._map_to_legacy_format(data_type, clean_data)
                parsed_results.append(legacy_payload)
                
                logger.debug(f"Mapped Validator IS type '{data_type}' to legacy format: {list(legacy_payload.keys())}")
                
            except Exception as e:
                logger.error(f"Failed to parse Validator IS result: {result}, error: {e}")
                # Fallback to basic detection for this item
                fallback = self._fallback_payload_detection(body.get("request_data", ""))
                parsed_results.append(fallback)
        
        return parsed_results
    
    def _map_to_legacy_format(self, data_type: str, clean_data: str) -> Dict[str, Any]:
        """Map Validator IS types to legacy payload format"""
        type_mapping = {
            "phone": "phone",
            "email": "email", 
            "nickname": "nick",     # ✅ Maps to "nick" which becomes "login"
            "login": "nick",        # ✅ Maps to "nick" which becomes "login"
            "username": "nick",     # ✅ Maps to "nick" which becomes "login"
            "user": "nick",         # ✅ Maps to "nick" which becomes "login"
        }
        
        legacy_type = type_mapping.get(data_type)
        if legacy_type:
            return {legacy_type: clean_data}
        
        # If type is not directly mappable, use fallback detection
        logger.warning(f"Unmapped Validator IS type: {data_type}, using fallback detection")
        return self._fallback_payload_detection(clean_data)
    
    def _fallback_payload_detection(self, query: str) -> Dict[str, Any]:
        """Fallback payload detection when Validator IS is unavailable or returns unknown types"""
        # PRESERVES EXACT LEGACY LOGIC for type detection
        query_clean = query.strip()
        
        # Email detection
        if "@" in query_clean and "." in query_clean:
            local_part, domain = query_clean.split("@", 1)
            if len(local_part) > 0 and len(domain) > 0 and "." in domain:
                return {"email": query_clean}
        
        # Phone detection - Russian phone format
        phone_clean = query_clean.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if phone_clean.isdigit():
            if len(phone_clean) == 11 and phone_clean.startswith(('7', '8')):
                return {"phone": query_clean}
            elif len(phone_clean) == 10:
                return {"phone": f"7{phone_clean}"}  # Convert to 11-digit format
            elif len(phone_clean) in [10, 11]:  # Allow other international formats
                return {"phone": query_clean}
        
        # Default to nickname (preserves legacy behavior)
        return {"nick": query_clean}