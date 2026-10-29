"""Multimodal Attendance & Engagement Agent - Streamlit Application Entrypoint.

Provides a unified, offline-first dashboard for classroom computer vision,
speech acoustic analysis, presence-based attendance verification, and transparent AI reasoning.
"""

from __future__ import annotations

import streamlit as st

from core.config import config
from database.database import init_db
from frontend.components import (
    render_analytics_view,
    render_attendance_view,
    render_audio_engagement_view,
    render_dashboard_view,
    render_session_workspace,
    render_settings_view,
    render_sidebar,
)
from frontend.styles import apply_custom_theme

# Configure Streamlit page
st.set_page_config(
    page_title=config.app_name,
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Ensure database tables exist
init_db()

# Apply modern dark navy theme styling
apply_custom_theme()

# Render Navigation Sidebar
active_tab = render_sidebar()

# Route to active view
if active_tab == "📊 Dashboard":
    render_dashboard_view()
elif active_tab == "📹 Session Workspace":
    render_session_workspace()
elif active_tab == "📋 Attendance":
    render_attendance_view()
elif active_tab == "🎙️ Audio & Engagement":
    render_audio_engagement_view()
elif active_tab == "📈 Analytics & Reports":
    render_analytics_view()
elif active_tab == "⚙️ Settings":
    render_settings_view()
