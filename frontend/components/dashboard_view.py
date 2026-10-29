"""Dashboard / Home Overview Component."""

from __future__ import annotations

import streamlit as st
from sqlalchemy import func, select

from database.database import get_db_context
from database.models import AttendanceRecord, Session
from database.repository import Repository
from frontend.styles import render_stat_card


def render_dashboard_view() -> None:
    """Render Section A: Dashboard overview with KPI cards and recent session activity."""
    st.markdown(
        """
        <div style="margin-bottom: 24px;">
            <h1 style="font-size: 2rem; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">
                Classroom Intelligence Dashboard
            </h1>
            <p style="color: #94a3b8; font-size: 0.95rem; margin: 0;">
                Multimodal observation overview combining computer vision and acoustic speech activity heuristics.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with get_db_context() as db:
        repo = Repository(db)
        sessions = [s.to_dict() for s in repo.list_sessions(limit=50)]

        # Aggregate counts
        total_sessions = len(sessions)
        all_attendance = [r.to_dict() for r in db.scalars(select(AttendanceRecord)).all()]
        total_records = len(all_attendance)
        pending_review_count = sum(1 for r in all_attendance if r["instructor_status"] == "pending_review")

        # Mean heuristic
        completed_sessions = [s for s in sessions if s.get("heuristic_score") is not None and s["heuristic_score"] > 0]
        avg_score = (
            sum(s["heuristic_score"] for s in completed_sessions) / len(completed_sessions)
            if completed_sessions
            else 0.0
        )

    # 4 Stat Cards in Columns
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(render_stat_card("Total Sessions", str(total_sessions), "Recorded classroom runs"), unsafe_allow_html=True)
    with c2:
        st.markdown(render_stat_card("Pending Reviews", str(pending_review_count), "Instructor verification needed"), unsafe_allow_html=True)
    with c3:
        st.markdown(render_stat_card("Attendance Records", str(total_records), "Total visual track proposals"), unsafe_allow_html=True)
    with c4:
        st.markdown(render_stat_card("Avg Heuristic Score", f"{avg_score:.1f}/100", "Experimental signal fusion"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Latest Session Spotlight & Actions
    if sessions:
        latest = sessions[0]
        st.markdown(
            f"""
            <div class="accent-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 0.8rem; font-weight: 600; color: #38bdf8; text-transform: uppercase;">LATEST CLASSROOM SESSION</div>
                        <div style="font-size: 1.3rem; font-weight: 700; color: #f8fafc;">#{latest['id']} - {latest['title']}</div>
                        <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px;">
                            Course: <b>{latest['course_code']}</b> | Instructor: <b>{latest['instructor_name']}</b> | Duration: <b>{latest['duration_seconds']:.1f}s</b> | Status: <b>{latest['status'].upper()}</b>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.8rem; font-weight: 700; color: #38bdf8;">
                            {f"{latest['heuristic_score']:.1f}" if latest.get('heuristic_score') is not None else "--"}
                        </div>
                        <div style="font-size: 0.75rem; color: #94a3b8;">Heuristic Index</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Recent Sessions Table
    st.markdown("### 📋 Recent Observation Sessions")
    if sessions:
        import pandas as pd

        table_data = []
        for s in sessions[:10]:
            h_str = f"{s['heuristic_score']:.1f}" if s.get("heuristic_score") is not None else "Pending"
            table_data.append({
                "Session ID": s["id"],
                "Title": s["title"],
                "Course": s["course_code"],
                "Instructor": s["instructor_name"],
                "Duration (s)": f"{s['duration_seconds']:.1f}",
                "Status": s["status"].upper(),
                "Heuristic (0-100)": h_str,
                "Sampled Frames": s["total_frames_sampled"],
                "Created At": s["created_at"][:16] if s.get("created_at") else "-",
            })
        df = pd.DataFrame(table_data)
        st.dataframe(df, hide_index=True)
    else:
        st.info("No classroom sessions available yet. Switch to '📹 Session Workspace' to create or analyze your first session!")
