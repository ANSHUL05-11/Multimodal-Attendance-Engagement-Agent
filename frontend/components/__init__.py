"""Frontend components package."""

from frontend.components.analytics_view import render_analytics_view
from frontend.components.attendance_view import render_attendance_view
from frontend.components.audio_engagement_view import render_audio_engagement_view
from frontend.components.dashboard_view import render_dashboard_view
from frontend.components.nav import render_sidebar
from frontend.components.session_workspace import render_session_workspace
from frontend.components.settings_view import render_settings_view

__all__ = [
    "render_sidebar",
    "render_dashboard_view",
    "render_session_workspace",
    "render_attendance_view",
    "render_audio_engagement_view",
    "render_analytics_view",
    "render_settings_view",
]
