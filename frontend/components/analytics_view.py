"""Analytics, Historical Comparisons, and Report Export Component."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.analytics import SessionAnalytics
from database.database import get_db_context
from database.repository import Repository


def render_analytics_view() -> None:
    """Render Section E: Analytics charts, historical comparisons, recommendations, and CSV exports."""
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 2rem; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">
                Session Analytics & Teaching Insights
            </h1>
            <p style="color: #94a3b8; font-size: 0.95rem;">
                Historical trends, pedagogical suggestions, and certified CSV data exports.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current_session_id = st.session_state.get("selected_session_id")

    with get_db_context() as db:
        repo = Repository(db)
        sessions = repo.list_sessions(limit=50)

        session = repo.get_session(current_session_id) if current_session_id else None
        recs = repo.get_recommendations(current_session_id) if current_session_id else []
        attendance_records = [r.to_dict() for r in repo.get_session_attendance(current_session_id)] if current_session_id else []
        v_metrics = [m.to_dict() for m in repo.get_visual_metrics(current_session_id)] if current_session_id else []
        a_metrics = [m.to_dict() for m in repo.get_audio_metrics(current_session_id)] if current_session_id else []

    t1, t2 = st.tabs(["💡 Teaching Recommendations", "📊 Historical Session Comparisons"])

    with t1:
        if not session:
            st.warning("Please select a session from the sidebar.")
        else:
            st.markdown(f"### 📋 Pedagogical Recommendations for Session #{session.id}")
            st.caption("Transparent suggestions generated from observed classroom signals. Descriptively worded for educators.")

            if recs:
                for r in recs:
                    priority_color = "#ef4444" if r.priority == "high" else ("#f59e0b" if r.priority == "medium" else "#10b981")
                    st.markdown(
                        f"""
                        <div class="rec-card">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                <div class="rec-title">{r.title}</div>
                                <span style="background: rgba(255,255,255,0.05); color: {priority_color}; border: 1px solid {priority_color}; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">
                                    {r.priority.upper()} PRIORITY
                                </span>
                            </div>
                            <div class="rec-obs"><b>Observation:</b> {r.observation}</div>
                            <div class="rec-sug"><b>Recommendation:</b> {r.suggestion}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No recommendations generated yet for this session. Run the analysis in the workspace.")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 📥 Download Session Reports")

            c_exp1, c_exp2 = st.columns(2)
            with c_exp1:
                if attendance_records:
                    att_csv = SessionAnalytics.export_attendance_csv(attendance_records)
                    st.download_button(
                        label="📄 Download Attendance Report (CSV)",
                        data=att_csv,
                        file_name=f"attendance_session_{session.id}.csv",
                        mime="text/csv",
                    )
                else:
                    st.button("📄 Download Attendance Report (CSV)", disabled=True)

            with c_exp2:
                if v_metrics or a_metrics:
                    from core.agent import MultimodalFusionAgent
                    fused = MultimodalFusionAgent().fuse_signals(
                        visual_metrics=v_metrics,
                        audio_metrics=a_metrics,
                        session_duration_sec=session.duration_seconds,
                    )
                    metrics_csv = SessionAnalytics.export_session_metrics_csv(fused.get("fused_timeline", []))
                    st.download_button(
                        label="📈 Download Timeseries Metrics (CSV)",
                        data=metrics_csv,
                        file_name=f"metrics_session_{session.id}.csv",
                        mime="text/csv",
                    )
                else:
                    st.button("📈 Download Timeseries Metrics (CSV)", disabled=True)

    with t2:
        st.markdown("### 📈 Cross-Session Trend Analysis")
        completed = [s for s in sessions if s.heuristic_score is not None and s.heuristic_score > 0]

        if len(completed) >= 2:
            hist_data = []
            for s in completed:
                hist_data.append({
                    "Session": f"#{s.id} ({s.course_code})",
                    "Heuristic Score": s.heuristic_score,
                    "Duration (s)": s.duration_seconds,
                    "Sampled Frames": s.total_frames_sampled,
                })
            df_hist = pd.DataFrame(hist_data)

            fig_comp = px.bar(
                df_hist,
                x="Session",
                y="Heuristic Score",
                color="Heuristic Score",
                color_continuous_scale="Viridis",
                title="Classroom Session Activity Heuristic Comparison",
                template="plotly_dark",
            )
            fig_comp.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0b1120")
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("Run multimodal analysis on at least two classroom sessions to view comparative trends here.")
