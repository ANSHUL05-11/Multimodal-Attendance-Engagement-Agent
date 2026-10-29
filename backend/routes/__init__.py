"""Backend routes initialization."""

from backend.routes.analytics import router as analytics_router
from backend.routes.attendance import router as attendance_router
from backend.routes.participants import router as participants_router
from backend.routes.sessions import router as sessions_router

__all__ = ["sessions_router", "attendance_router", "analytics_router", "participants_router"]
