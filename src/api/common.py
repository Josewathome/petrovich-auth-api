# In src/api/common.py
import asyncio
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.application.services import PetrovichSearchService
from src.core.response_helper import ResponseHelper
from src.infrastructure.validator_client import ValidatorHTTPClient
from src.domain.exceptions import ServiceUnavailableError, ValidationError

router = APIRouter()
response_helper = ResponseHelper()
logger = logging.getLogger(__name__)

class ValidationRequest(BaseModel):
    query: List[str]

class CommonSearchRequest(BaseModel):
    data: List[Dict[str, Any]]

@router.post("/search/validate", response_model=List[Dict[str, Any]])
async def validate_and_search(request: ValidationRequest):
    """
    Common controller endpoint that validates input using Validator IS
    and routes to appropriate services
    """
    search_service = PetrovichSearchService()
    results = []
    
    if not request.query:
        return []
    
    try:
        # Step 1: Validate all queries with Validator IS
        validated_payloads = await _validate_with_validator_is(request.query)
        
        # Step 2: Process each validated payload
        for i, payload in enumerate(validated_payloads):
            try:
                query = request.query[i]  # Original query for error context
                result = await search_service.search(payload)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Search failed for query '{query}': {e}")
                error_response = response_helper.error_response(
                    exception=e,
                    extra={
                        "original_query": query,
                        "validated_payload": payload,
                        "query_index": i
                    }
                )
                results.append(error_response)
                
    except (ServiceUnavailableError, ValidationError) as e:
        # Validator IS failed, use fallback for all queries
        logger.warning(f"Validator IS unavailable, using fallback validation: {e}")
        results = await _process_with_fallback_validation(request.query, search_service)
    
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error in validate_and_search: {e}")
        error_response = response_helper.error_response(
            exception=e,
            extra={"original_queries": request.query}
        )
        # Return error for all queries to maintain consistent response format
        results = [error_response] * len(request.query)
    
    return results

@router.post("/batch-search", response_model=List[Dict[str, Any]])
async def batch_search(request: CommonSearchRequest):
    """
    Batch search endpoint for multiple payloads (direct payload input)
    """
    search_service = PetrovichSearchService()
    results = []
    
    for i, payload in enumerate(request.data):
        try:
            result = await search_service.search(payload)
            results.append(result)
        except Exception as e:
            error_response = response_helper.error_response(
                exception=e,
                extra={
                    "payload": payload,
                    "payload_index": i
                }
            )
            results.append(error_response)
    
    return results

async def _validate_with_validator_is(queries: List[str]) -> List[Dict[str, Any]]:
    """Integrate with Validator IS - follows Sfera guidelines"""
    async with ValidatorHTTPClient() as validator_client:
        return await validator_client.validate_queries(queries)

async def _process_with_fallback_validation(queries: List[str], search_service: PetrovichSearchService) -> List[Dict[str, Any]]:
    """Process queries using fallback validation when Validator IS is unavailable"""
    results = []
    validator_client = ValidatorHTTPClient()
    
    for query in queries:
        try:
            # Use the fallback detection from the validator client
            fallback_payload = validator_client._fallback_payload_detection(query)
            result = await search_service.search(fallback_payload)
            results.append(result)
            
        except Exception as e:
            logger.error(f"Fallback search failed for query '{query}': {e}")
            error_response = response_helper.error_response(
                exception=e,
                extra={
                    "original_query": query,
                    "fallback_used": True,
                    "validator_failed": True
                }
            )
            results.append(error_response)
    
    return results

# Health check endpoint for Validator IS integration
@router.get("/validator-health")
async def validator_health_check():
    """Health check for Validator IS integration"""
    try:
        async with ValidatorHTTPClient() as validator_client:
            # Test with a simple query
            test_queries = ["test@example.com"]
            results = await validator_client.validate_queries(test_queries)
            
            return response_helper.success_response(
                data={
                    "validator_status": "healthy",
                    "test_query_processed": True,
                    "results_count": len(results)
                },
                extra={"timestamp": "2024-01-01T00:00:00Z"}  # Use actual timestamp in production
            )
            
    except Exception as e:
        return response_helper.error_response(
            exception=e,
            extra={"health_check": "validator_connectivity"}
        )