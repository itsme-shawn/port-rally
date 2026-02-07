"""FastAPI application for AI Advisor service."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from advisor.api.router import router
from advisor.config import settings
from advisor.db.postgres import close_pool, get_pool

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting AI Advisor service...")
    logger.info(f"Using model: {settings.gemini_model}")

    # Initialize database pool
    await get_pool()
    logger.info("Database connection pool initialized")

    yield

    # Shutdown
    logger.info("Shutting down AI Advisor service...")
    await close_pool()
    logger.info("Database connection pool closed")


# Create FastAPI app
app = FastAPI(
    title="AI Advisor Service",
    description="Portfolio and Asset Analysis using AI",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "ai-advisor",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "advisor.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
