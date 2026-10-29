"""Sidebar navigation component."""

from __future__ import annotations

from typing import List, Optional

import streamlit as st
from sqlalchemy.orm import Session as DBSession

from core.config import config, get_environment_info
from database.database import get_db_context
from database.repository import Repository


def render_sidebar() -> str:
    """Render sidebar navigation, session switcher, and return selected tab."""
    with st.sidebar:
        # Branding Header
        st.markdown(
            """
            <div style="padding: 10px 0 20px 0; border-bottom: 1px solid #334155;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 2rem;">🎓</span>
                    <div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #38bdf8;">Multimodal Agent</div>
                        <div style="font-size: 0.75rem; color: #94a3b8;">Classroom Vision & Audio</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Main Navigation
        options = [
            "📊 Dashboard",
            "📹 Session Workspace",
            "📋 Attendance",
            "🎙️ Audio & Engagement",
            "📈 Analytics & Reports",
            "⚙️ Settings",
        ]

        choice = st.radio(
            "Navigation",
            options,
            label_visibility="collapsed",
            index=0,
        )

        st.markdown("---")

        # Global Session Selector
        with get_db_context() as db:
            repo = Repository(db)
            sessions_data = [s.to_dict() for s in repo.list_sessions(limit=25)]

        st.markdown("<div style='font-size: 0.85rem; font-weight: 600; color: #94a3b8;'>ACTIVE SESSION</div>", unsafe_allow_html=True)
        if sessions_data:
            session_options = {s["id"]: f"#{s['id']} - {s['title']} ({s['course_code']})" for s in sessions_data}
            session_ids = list(session_options.keys())

            # Store selected session id in state
            current_id = st.session_state.get("selected_session_id", session_ids[0])
            if current_id not in session_ids:
                current_id = session_ids[0]

            selected_id = st.selectbox(
                "Choose Session",
                options=session_ids,
                format_func=lambda sid: session_options[sid],
                index=session_ids.index(current_id),
                label_visibility="collapsed",
            )
            st.session_state["selected_session_id"] = selected_id
        else:
            st.info("No sessions created yet.")
            st.session_state["selected_session_id"] = None

        st.markdown("<br>", unsafe_allow_html=True)

        # System Diagnostics status footer
        env = get_environment_info()
        cam_icon = "🟢" if env["camera_accessible"] else "⚪"
        cam_text = "Available" if env["camera_accessible"] else "Offline"

        st.markdown(
            f"""
            <div style="padding: 12px; background: #0b1120; border-radius: 8px; border: 1px solid #1e293b; font-size: 0.75rem; color: #64748b;">
                <div><b>Local Camera:</b> {cam_icon} {cam_text}</div>
                <div><b>OpenCV:</b> {env['opencv_version']}</div>
                <div><b>Platform:</b> {env['os_platform'].split('-')[0]}</div>
                <div style="margin-top: 6px; color: #38bdf8; font-weight: 600;">Offline-First Architecture</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        return choice
