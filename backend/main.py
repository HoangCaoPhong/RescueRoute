import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import settings

app = FastAPI(
    title="RescueRoute API",
    description="Backend API for RescueRoute application",
    version="1.0.0"
)

# Parse CORS origins
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    env: str
    version: str
    latency_ms: float

@app.get("/api/v1/health", response_model=HealthResponse)
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to ping the server and measure basic latency.
    """
    start_time = time.perf_counter()
    # Simulate minimal processing
    latency_ms = (time.perf_counter() - start_time) * 1000
    
    return HealthResponse(
        status="ok",
        env=settings.APP_ENV,
        version="1.0.0",
        latency_ms=round(latency_ms, 2)
    )
