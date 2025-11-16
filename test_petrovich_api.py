import asyncio
import re
import aiohttp
from urllib import parse
from typing import Dict, Any, Optional, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StandalonePetrovichSearcher:
    """
    Standalone implementation of Petrovich.ru authorization and search
    without dependencies on proxies, MongoDB, or external queues
    """
    
    def __init__(self):
        self.session_cookies = {}
        self.session = None
        self.headers = {
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
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _extract_session_params(self, html_content: str) -> Tuple[Dict, Dict]:
        """
        Extract session initialization parameters from frontend HTML
        """
        # Find the session initialization URL with nonce parameter
        urls = re.findall(r'src="(.*?nonce.*?)">', html_content)
        if not urls:
            raise Exception("Could not find session initialization URL in frontend page")
        
        url = urls[0]
        logger.info(f"Found session URL: {url}")
        
        # Parse query parameters from the URL
        parsed_url = parse.urlsplit(url)
        params = parse.parse_qs(parsed_url.query)
        
        # Convert values from list to single values
        clean_params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
        
        return {}, clean_params  # Return empty cookies and parsed params
    
    def _parse_session_cookies(self, response_cookies) -> Dict:
        """
        Parse and filter session cookies from aiohttp response cookies.
        """
        cookies_dict = {}
        allowed_cookies = ["SIK", "SIV"]
        allowed_masks = [
            {"key": r"^[A-Za-z\d]_?[A-Za-z\d\-_]{7,}$", "value": r"^A.*"}
        ]
        
        # response_cookies is a dict-like object
        for key, morsel in response_cookies.items():
            value = morsel.value

            # direct allowlist
            if key in allowed_cookies:
                cookies_dict[key] = value
                logger.info(f"Added allowed cookie: {key}")
                continue
            
            # regex matching
            for mask in allowed_masks:
                if (re.match(mask["key"], key) and 
                    re.match(mask["value"], value)):
                    cookies_dict[key] = value
                    logger.info(f"Added pattern-matched cookie: {key}")
                    break
        
        return cookies_dict

    
    async def create_session(self) -> bool:
        """
        Create a new authenticated session with Petrovich.ru
        """
        try:
            logger.info("Starting session creation...")
            
            # Step 1: Get frontend page to extract session parameters
            frontend_url = "https://petrovich.ru"
            logger.info(f"Requesting frontend page: {frontend_url}")
            
            async with self.session.get(frontend_url, timeout=15, ssl=False) as response:
                html_content = await response.text()
                initial_cookies, session_params = self._extract_session_params(html_content)
                logger.info(f"Extracted session params: {session_params}")
            
            # Step 2: Initialize session using the extracted parameters
            session_url = "https://api.petrovich.ru/session/v3/init.js"
            logger.info(f"Initializing session: {session_url}")
            
            async with self.session.get(
                session_url, 
                params=session_params,
                cookies=initial_cookies,
                timeout=15, 
                ssl=False
            ) as response:
                # Parse cookies from the session response
                self.session_cookies = self._parse_session_cookies(response.cookies)
                session_response = await response.text()
                logger.info(f"Session initialization response: {session_response[:100]}...")
            
            logger.info(f"Session created successfully. Cookies: {list(self.session_cookies.keys())}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return False
    
    async def search_phone(self, phone_number: str) -> Dict[str, Any]:
        """
        Search for a phone number in Petrovich.ru system
        """
        if not self.session_cookies:
            logger.warning("No active session. Creating new session...")
            if not await self.create_session():
                raise Exception("Failed to create session for search")
        
        search_url = "https://api.petrovich.ru/user/v1.1/login/check"
        
        # Prepare search parameters
        params = {
            "pet_case": "camel",
            "city_code": "spb", 
            "client_id": "pet_site"
        }
        
        json_data = {
            "type": "phone",
            "login": phone_number
        }
        
        logger.info(f"Searching for phone: {phone_number}")
        
        try:
            async with self.session.post(
                search_url,
                params=params,
                json=json_data,
                cookies=self.session_cookies,
                timeout=8,
                ssl=False
            ) as response:
                response_text = await response.text()
                logger.info(f"Search response: {response_text[:200]}...")
                
                # Parse the response
                return await self._parse_search_response(response, response_text)
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            # Check if session is blocked and retry with new session
            if "Session is broken" in str(e) or "Session is not started" in str(e):
                logger.info("Session blocked, creating new session and retrying...")
                if await self.create_session():
                    return await self.search_phone(phone_number)
            raise
    
    async def _parse_search_response(self, response, response_text: str) -> Dict[str, Any]:
        """
        Parse and validate the search response
        """
        # Check for session blocking
        if "Session is broken" in response_text or "Session is not started" in response_text:
            raise Exception("Session blocked")
        
        # Check for incorrect data
        if "Некорректный" in response_text:
            raise Exception("Incorrect data format")
        
        # Check for successful request marker
        if "Запрос успешно выполнен" not in response_text:
            raise Exception("Request not successful")
        
        try:
            data = await response.json()
        except:
            raise Exception(f"Response is not JSON: {response_text}")
        
        # Check response code
        code = data.get('state', {}).get('code')
        if code != 200:
            raise Exception(f"Unexpected response code: {code}")
        
        # Parse the actual result
        is_used = data.get('data', {}).get('isUsed')
        
        if is_used:
            return {
                "status": "success",
                "result": "Найден",
                "result_code": "FOUND",
                "data": data
            }
        elif is_used is False:
            return {
                "status": "success", 
                "result": "Не найден",
                "result_code": "NOT_FOUND",
                "data": data
            }
        else:
            raise Exception(f"Unknown response format: {data}")

async def main():
    """
    Example usage of the standalone searcher
    """
    # Example phone numbers to test
    test_phones = [
        "79211234567",  # Replace with actual test numbers
        "79319876543"
    ]
    
    async with StandalonePetrovichSearcher() as searcher:
        # Create initial session
        logger.info("Creating initial session...")
        success = await searcher.create_session()
        
        if not success:
            logger.error("Failed to create initial session")
            return
        
        # Search for each phone number
        for phone in test_phones:
            try:
                logger.info(f"\n--- Searching for {phone} ---")
                result = await searcher.search_phone(phone)
                
                print(f"Phone: {phone}")
                print(f"Result: {result['result']}")
                print(f"Code: {result['result_code']}")
                print("-" * 40)
                
            except Exception as e:
                print(f"Error searching {phone}: {e}")
            
            # Small delay between requests to be respectful
            await asyncio.sleep(2)

if __name__ == "__main__":
    # Run the example
    asyncio.run(main())