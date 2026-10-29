"""FastAPI Backend Application Entrypoint.

Provides local REST API endpoints for session processing, attendance review,
analytics retrieval, and health diagnostics.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import (
    analytics_router,
    attendance_router,
    participants_router,
    sessions_router,
)
from core.config import config, get_environment_info, logger
from database.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info("Initializing database tables...")
    init_db()
    logger.info("FastAPI backend started on http://%s:%d", config.api_host, config.api_port)
    yield
    logger.info("FastAPI backend shutting down cleanly.")


app = FastAPI(
    title="Multimodal Attendance & Engagement Agent API",
    description="Offline-first classroom multimodal visual & audio analytics backend.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(sessions_router)
app.include_router(attendance_router)
app.include_router(analytics_router)
app.include_router(participants_router)


@app.get("/health", tags=["system"])
def health_check():
    """System health check and diagnostic information."""
    return {
        "status": "healthy",
        "service": config.app_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": get_environment_info(),
    }


@app.get("/", tags=["system"])
def root():
    """API welcome and documentation link."""
    return {
        "message": f"Welcome to {config.app_name} API",
        "docs_url": "/docs",
        "health_check": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host=config.api_host, port=config.api_port, reload=False)
