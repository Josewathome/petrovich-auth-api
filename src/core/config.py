import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Service configuration
    SERVICE_NAME: str = "petrovich_auth_api"
    MODE: str = os.getenv("MODE", "dev")
    VERSION_NO: str= os.getenv("VERSION_NO", "v1.0.0")
    VERSION_NO_VALUE: str= os.getenv("VERSION_NO_VALUE", "v1")
    
    # Petrovich API endpoints
    PETROVICH_FRONTEND_URL: str = "https://petrovich.ru"
    PETROVICH_SESSION_URL: str = "https://api.petrovich.ru/session/v3/init.js"
    PETROVICH_SEARCH_URL: str = "https://api.petrovich.ru/user/v1.1/login/check"
    
    # Legacy compatibility settings
    DEFAULT_CITY_CODE: str = "spb"
    DEFAULT_CLIENT_ID: str = "pet_site"
    DEFAULT_PET_CASE: str = "camel"
    
    
    # Request timeouts
    FRONTEND_TIMEOUT: int = int(os.getenv("FRONTEND_TIMEOUT",15))
    SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT",15))
    SEARCH_TIMEOUT: int = int(os.getenv("SEARCH_TIMEOUT",8))

    # common controller validator
    VALIDATOR_URL: str = os.getenv("VALIDATOR_URL", "http://validator-service/api/v1/validate")
    VALIDATOR_TIMEOUT: int = int(os.getenv("VALIDATOR_TIMEOUT", 30))
    VALIDATOR_MAX_RETRIES: int = int(os.getenv("VALIDATOR_MAX_RETRIES", 3))
    
    
    # Session configuration
    MAX_SESSION_RETRIES: int = int(os.getenv("SEARCH_TIMEOUT",2))
    REQUEST_DELAY: float = float(os.getenv("SEARCH_TIMEOUT",2.0))
    
    class Config:
        case_sensitive = True
import os      
def get_settings() -> Settings:
    # Load MODE from the environment first (if available)
    mode = os.getenv("MODE", "dev")
    env_file = f".env.{mode}"
    return Settings(_env_file=env_file)

settings = Settings()