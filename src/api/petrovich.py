from typing import Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

from src.application.services import PetrovichSearchService
from src.core.config import settings

router = APIRouter()

class SearchRequest(BaseModel):
    phone: str = None
    email: str = None
    nick: str = None

@router.post("/search", response_model=Dict[str, Any])
async def search_petrovich(request: SearchRequest):
    """
    Direct Petrovich search endpoint - returns Sfera-compliant responses
    """
    search_service = PetrovichSearchService()
    
    # Convert to legacy payload format
    payload = {k: v for k, v in request.dict().items() if v is not None}
    
    # The search service now returns properly formatted Sfera responses
    result = await search_service.search(payload)
    return result

@router.get("/health")
async def health_check():
    """Health check endpoint with Sfera format"""
    from src.core.response_helper import ResponseHelper, current_utc_timestamp
    return ResponseHelper.success_response(
        data={"service": settings.SERVICE_NAME, "status": "healthy"},
        extra={"timestamp": current_utc_timestamp()}
    )