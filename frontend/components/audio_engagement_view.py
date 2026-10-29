"""Audio Signal Analysis and Multimodal Engagement View Component."""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from core.agent import MultimodalFusionAgent
from database.database import get_db_context
from database.repository import Repository


def render_audio_engagement_view() -> None:
    """Render Section D: Synchronized audio and visual timelines, fusion charts, and transparent explanations."""
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 2rem; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">
                Audio & Multimodal Engagement Analysis
            </h1>
            <p style="color: #94a3b8; font-size: 0.95rem;">
                Time-synchronized acoustic energy, speech activity intervals, and rule-based multimodal signal fusion.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current_session_id = st.session_state.get("selected_session_id")
    if not current_session_id:
        st.warning("Please select a session from the sidebar.")
        return

    with get_db_context() as db:
        repo = Repository(db)
        session = repo.get_session(current_session_id)
        if not session:
            st.error("Session not found.")
            return

        v_metrics = [m.to_dict() for m in repo.get_visual_metrics(current_session_id)]
        a_metrics = [m.to_dict() for m in repo.get_audio_metrics(current_session_id)]
        summary = repo.get_summary(current_session_id)

    if not v_metrics and not a_metrics:
        st.info("No timeline metrics recorded for this session yet. Please run the analysis in '📹 Session Workspace'.")
        return

    # Fuse signals to generate synchronized timeline
    fusion_agent = MultimodalFusionAgent()
    fused_res = fusion_agent.fuse_signals(
        visual_metrics=v_metrics,
        audio_metrics=a_metrics,
        session_duration_sec=session.duration_seconds,
    )
    timeline = fused_res.get("fused_timeline", [])

    # Overview Metrics Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Heuristic Score", f"{fused_res['overall_heuristic_score']:.1f}/100")
    with c2:
        st.metric("Peak Activity Time", f"{fused_res['peak_engagement_sec']:.1f}s")
    with c3:
        st.metric("Visual Metrics Sampled", len(v_metrics))
    with c4:
        st.metric("Audio Windows Sampled", len(a_metrics))

    st.markdown("<br>", unsafe_allow_html=True)

    # Plotly Subplots for Synchronized Signals
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=(
            "1. Multimodal Heuristic Activity Index (0-100 Scale)",
            "2. Visual Signal: Face Count & Active Tracking Continuity",
            "3. Audio Signal: RMS Energy & Speech Activity Intervals",
        ),
    )

    # Subplot 1: Heuristic Index
    if timeline:
        x_times = [w["timestamp_sec"] for w in timeline]
        y_scores = [w["heuristic_score"] for w in timeline]
        fig.add_trace(
            go.Scatter(
                x=x_times,
                y=y_scores,
                mode="lines+markers",
                name="Heuristic Score",
                line=dict(color="#38bdf8", width=3),
                marker=dict(size=6, color="#0284c7"),
                fill="tozeroy",
                fillcolor="rgba(56, 189, 248, 0.15)",
            ),
            row=1,
            col=1,
        )

    # Subplot 2: Faces & Tracking
    if v_metrics:
        v_times = [m["timestamp_sec"] for m in v_metrics]
        v_faces = [m["face_count"] for m in v_metrics]
        v_stab = [m["stability_score"] * 5 for m in v_metrics]  # scaled for display
        fig.add_trace(
            go.Scatter(
                x=v_times,
                y=v_faces,
                mode="lines+markers",
                name="Detected Faces",
                line=dict(color="#10b981", width=2),
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=v_times,
                y=v_stab,
                mode="lines",
                name="Tracking Stability",
                line=dict(color="#a78bfa", width=1.5, dash="dot"),
            ),
            row=2,
            col=1,
        )

    # Subplot 3: Audio RMS and Speech Active
    if a_metrics:
        a_times = [m["timestamp_sec"] for m in a_metrics]
        a_rms = [m["rms_energy"] for m in a_metrics]
        a_speech = [1 if m["is_speech_active"] else 0 for m in a_metrics]
        fig.add_trace(
            go.Scatter(
                x=a_times,
                y=a_rms,
                mode="lines",
                name="RMS Energy",
                line=dict(color="#f59e0b", width=2),
            ),
            row=3,
            col=1,
        )
        fig.add_trace(
            go.Bar(
                x=a_times,
                y=[v * (max(a_rms) if a_rms else 0.05) for v in a_speech],
                name="Speech Active",
                marker_color="rgba(244, 63, 94, 0.4)",
            ),
            row=3,
            col=1,
        )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0b1120",
        height=680,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(title_text="Session Elapsed Time (seconds)", row=3, col=1)

    st.plotly_chart(fig, use_container_width=True)

    # Transparent Reasoning & Limitations Section
    st.markdown("### 💡 Transparent Heuristic Explanation")

    col_expl, col_weights = st.columns([2, 1])
    with col_expl:
        st.markdown(
            f"""
            <div class="rec-card">
                <div class="rec-title">Observation Summary</div>
                <div style="font-size: 0.95rem; color: #e2e8f0; line-height: 1.5; margin-bottom: 12px;">
                    {fused_res.get('explanation', 'Analysis in progress.')}
                </div>
                <div style="font-size: 0.85rem; color: #94a3b8;">
                    <b>Modality Execution Mode:</b> <span class="badge-confirmed">{fused_res.get('modality_mode', 'multimodal').upper()}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 14px 18px; margin-top: 10px;">
                <div style="font-weight: 700; color: #f87171; font-size: 0.9rem; margin-bottom: 4px;">⚠️ Scientific Limitation Disclaimer</div>
                <div style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.4;">
                    {fused_res.get('limitations', '')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_weights:
        st.markdown(
            """
            <div class="rec-card">
                <div class="rec-title">Fusion Weights</div>
                <div style="font-size: 0.85rem; color: #94a3b8; line-height: 1.8;">
                    <div>• <b>Face Presence:</b> 40%</div>
                    <div>• <b>Tracking Stability:</b> 25%</div>
                    <div>• <b>Vocal Speech Activity:</b> 20%</div>
                    <div>• <b>Signal-to-Noise (SNR):</b> 15%</div>
                </div>
                <div style="font-size: 0.75rem; color: #64748b; margin-top: 10px;">
                    Calculated over 2.0-second sliding temporal windows with boundary normalization.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
