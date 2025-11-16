from fastapi import FastAPI
from src.api.common import router as common_router
from src.api.petrovich import router as petrovich_router
import logging
from src.core.config import settings


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title= settings.SERVICE_NAME,
    description="Petrovich search service with DDD architecture",
    version=settings.VERSION_NO
)
version_no = settings.VERSION_NO_VALUE
# Include routers
app.include_router(common_router, prefix=f"/api/{version_no}", tags=["Common Controller"])
app.include_router(petrovich_router, prefix=f"/api/{version_no}", tags=["Petrovich Service"])

@app.get("/")
async def root():
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION_NO,
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "direct_search": f"/api/{version_no}/search",
            "bulk_search": f"/api/{version_no}/batch-search",
            "health": "/health",
            "validation": f"/api/{version_no}/search/validate",
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": f"{settings.VERSION_NO}"
    }
logger = logging.getLogger(__name__) 
@app.on_event("startup")
async def startup_event():
    """Actions to perform on startup"""
    logger.info(f"{settings.SERVICE_NAME} starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    """Actions to perform on shutdown"""
    logger.info(f"{settings.SERVICE_NAME} shutting down...")
    
import uvicorn   
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload in development
        log_level="info"
    )