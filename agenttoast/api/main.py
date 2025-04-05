"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agenttoast.core.config import get_settings
from agenttoast.core.logger import logger

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="AgentToast API",
    description="API for AgentToast news digest service",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "environment": settings.app_env}

# Import and include routers
# from .routes import users, digests
# app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
# app.include_router(digests.router, prefix="/api/v1/digests", tags=["digests"])

@app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    logger.info("Starting AgentToast API", extra={"event": "startup"})

@app.on_event("shutdown")
async def shutdown_event():
    """Run shutdown tasks."""
    logger.info("Shutting down AgentToast API", extra={"event": "shutdown"}) 