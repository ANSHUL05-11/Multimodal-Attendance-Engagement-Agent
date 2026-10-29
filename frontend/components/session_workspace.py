"""Live Session and Media Processing Workspace Component."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import cv2
import streamlit as st

from core.agent import MultimodalFusionAgent
from core.analytics import SessionAnalytics
from core.audio_analysis import AudioProcessor
from core.config import check_camera_available, config, logger
from core.recommendations import RecommendationEngine
from core.vision import VisionProcessor
from database.database import get_db_context
from database.repository import Repository


def render_session_workspace() -> None:
    """Render Section B: Session workspace with upload, synthetic generator, and processing triggers."""
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 2rem; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">
                Session Workspace & Media Processing
            </h1>
            <p style="color: #94a3b8; font-size: 0.95rem;">
                Ingest classroom video and audio streams, configure temporal sampling parameters, and execute multimodal analysis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    t1, t2 = st.tabs(["🚀 Process & Ingest Media", "➕ Create New Session"])

    # TAB 2: Create New Session
    with t2:
        st.markdown("#### Create Classroom Session")
        with st.form("new_session_form"):
            c_title = st.text_input("Session Title", value="CS401 Lecture 12: Multimodal Systems")
            col_a, col_b = st.columns(2)
            with col_a:
                c_course = st.text_input("Course Code", value="CS401")
            with col_b:
                c_instructor = st.text_input("Instructor Name", value="Dr. A. Sharma")
            submitted = st.form_submit_button("Create Session")

            if submitted and c_title:
                with get_db_context() as db:
                    repo = Repository(db)
                    new_s = repo.create_session(
                        title=c_title,
                        course_code=c_course,
                        instructor_name=c_instructor,
                    )
                    st.session_state["selected_session_id"] = new_s.id
                st.success(f"Session #{new_s.id} created successfully! Switched active session.")
                st.rerun()

    # TAB 1: Process Active Session Media
    with t1:
        current_session_id = st.session_state.get("selected_session_id")
        if not current_session_id:
            st.warning("Please create or select a session from the sidebar first.")
            return

        with get_db_context() as db:
            repo = Repository(db)
            session = repo.get_session(current_session_id)

        if not session:
            st.error("Selected session not found.")
            return

        st.markdown(
            f"""
            <div class="accent-card">
                <b>Active Session:</b> #{session.id} - {session.title} ({session.course_code}) | <b>Status:</b> {session.status.upper()}
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown("### 📥 Media Input")

            # Option A: Synthetic Sample Generator for Demo
            with st.expander("🧪 Demo Fixtures (1-Click Sample Generator)", expanded=True):
                st.caption(
                    "Generate synthetic classroom video (with geometric animated faces) and audio (speech/tones/noise) "
                    "for immediate demonstration on any Windows laptop without requiring personal recordings."
                )
                if st.button("Generate & Attach Demo Sample Files"):
                    with st.spinner("Generating synthetic classroom media..."):
                        from generate_samples import create_demo_audio, create_demo_video

                        v_path = config.samples_dir / "sample_classroom_video.mp4"
                        a_path = config.samples_dir / "sample_classroom_audio.wav"

                        create_demo_video(str(v_path), duration_sec=12.0)
                        create_demo_audio(str(a_path), duration_sec=12.0)

                        with get_db_context() as db:
                            repo = Repository(db)
                            repo.update_session(
                                session.id,
                                video_path=str(v_path),
                                audio_path=str(a_path),
                            )
                    st.success("Attached demo video & audio to active session!")
                    st.rerun()

            # Option B: File Uploaders
            uploaded_video = st.file_uploader("Upload Classroom Video (MP4, AVI, MOV)", type=["mp4", "avi", "mov"])
            if uploaded_video:
                v_dest = config.uploads_dir / f"session_{session.id}_video_{uploaded_video.name}"
                with open(v_dest, "wb") as f:
                    f.write(uploaded_video.getbuffer())
                with get_db_context() as db:
                    Repository(db).update_session(session.id, video_path=str(v_dest))
                st.success(f"Video uploaded: {uploaded_video.name}")

            uploaded_audio = st.file_uploader("Upload Classroom Audio (WAV, MP3, OGG)", type=["wav", "mp3", "ogg", "flac"])
            if uploaded_audio:
                a_dest = config.uploads_dir / f"session_{session.id}_audio_{uploaded_audio.name}"
                with open(a_dest, "wb") as f:
                    f.write(uploaded_audio.getbuffer())
                with get_db_context() as db:
                    Repository(db).update_session(session.id, audio_path=str(a_dest))
                st.success(f"Audio uploaded: {uploaded_audio.name}")

            # Option C: Webcam Snapshot / Capture if supported
            cam_ready = check_camera_available(0)
            with st.expander(f"📷 Local Webcam Mode ({'Ready' if cam_ready else 'Unavailable'})", expanded=False):
                if cam_ready:
                    cam_img = st.camera_input("Capture Classroom Webcam Snapshot")
                    if cam_img:
                        snap_path = config.uploads_dir / f"session_{session.id}_snapshot.jpg"
                        with open(snap_path, "wb") as f:
                            f.write(cam_img.getbuffer())
                        st.info(f"Captured snapshot saved to {snap_path.name}")
                else:
                    st.info(
                        "No direct physical webcam detected. Upload recorded videos above or use "
                        "the 1-click Demo Fixture generator for laptop demonstrations."
                    )

        with col_right:
            st.markdown("### ⚙️ Analysis Parameters")

            sampling_interval = st.slider(
                "Video Frame Sampling Interval (Skip frames)",
                min_value=1,
                max_value=15,
                value=config.frame_sampling_interval,
                help="Higher interval reduces CPU load by sampling every Nth frame.",
            )

            min_presence = st.slider(
                "Minimum Presence Duration (seconds)",
                min_value=2.0,
                max_value=30.0,
                value=config.min_presence_seconds,
                step=1.0,
                help="Threshold required before a participant track is proposed as 'present'.",
            )

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 🎬 Execution")

            has_video_file = bool(session.video_path and Path(session.video_path).is_file())
            has_audio_file = bool(session.audio_path and Path(session.audio_path).is_file())

            st.markdown(
                f"""
                <div style="background: #0f172a; padding: 12px; border-radius: 8px; margin-bottom: 12px; font-size: 0.85rem;">
                    <div><b>Attached Video:</b> {'✅ ' + Path(session.video_path).name if has_video_file else '❌ None'}</div>
                    <div><b>Attached Audio:</b> {'✅ ' + Path(session.audio_path).name if has_audio_file else '❌ None'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            run_analysis = st.button("🚀 Run Multimodal Analysis Pipeline", disabled=not (has_video_file or has_audio_file))

            if run_analysis:
                with st.spinner("Processing visual and acoustic signals..."):
                    progress_bar = st.progress(10)

                    # Update status
                    with get_db_context() as db:
                        Repository(db).update_session(session.id, status="processing")

                    visual_metrics = []
                    tracks = []
                    proposals = []
                    duration_v = 0.0
                    preview_frame = None

                    # Step 1: Vision
                    if has_video_file:
                        v_proc = VisionProcessor(sampling_interval=sampling_interval, min_presence_sec=min_presence)
                        v_res = v_proc.process_video_file(session.video_path)
                        visual_metrics = v_res["visual_metrics"]
                        tracks = v_res["tracks"]
                        proposals = v_res["attendance_proposals"]
                        duration_v = v_res["duration_seconds"]
                        preview_frame = v_res["preview_frame"]

                        with get_db_context() as db:
                            repo = Repository(db)
                            repo.save_visual_metrics(session.id, visual_metrics)
                            repo.save_attendance_records(session.id, proposals)

                    progress_bar.progress(50)

                    # Step 2: Audio
                    audio_metrics = []
                    duration_a = 0.0
                    if has_audio_file:
                        a_proc = AudioProcessor()
                        a_res = a_proc.analyze_audio_file(session.audio_path)
                        audio_metrics = a_res["audio_metrics"]
                        duration_a = a_res["duration_seconds"]

                        with get_db_context() as db:
                            repo = Repository(db)
                            repo.save_audio_metrics(session.id, audio_metrics)

                    progress_bar.progress(75)

                    # Step 3: Multimodal Fusion
                    effective_duration = max(duration_v, duration_a, 1.0)
                    fusion_agent = MultimodalFusionAgent()
                    fused = fusion_agent.fuse_signals(
                        visual_metrics=visual_metrics,
                        audio_metrics=audio_metrics,
                        session_duration_sec=effective_duration,
                    )

                    # Step 4: Summary & Recommendations
                    summary_stats = SessionAnalytics.compute_summary_stats(
                        session_duration_sec=effective_duration,
                        visual_metrics=visual_metrics,
                        audio_metrics=audio_metrics,
                        tracks=tracks,
                        fused_result=fused,
                    )

                    recs = RecommendationEngine.generate_recommendations(
                        session_duration_sec=effective_duration,
                        avg_faces=summary_stats["avg_faces_visible"],
                        speech_ratio=summary_stats["speech_activity_ratio"],
                        avg_snr_db=summary_stats["avg_snr_db"],
                        fused_timeline=fused.get("fused_timeline", []),
                        tracks_count=len(tracks),
                    )

                    with get_db_context() as db:
                        repo = Repository(db)
                        repo.save_summary(session.id, summary_stats)
                        repo.save_recommendations(session.id, recs)
                        repo.update_session(
                            session.id,
                            status="completed",
                            duration_seconds=effective_duration,
                            total_frames_sampled=len(visual_metrics),
                            heuristic_score=fused.get("overall_heuristic_score", 0.0),
                        )

                    progress_bar.progress(100)

                    # Save preview image if exists
                    if preview_frame is not None:
                        preview_path = config.uploads_dir / f"session_{session.id}_preview.jpg"
                        cv2.imwrite(str(preview_path), preview_frame)
                        st.session_state[f"preview_{session.id}"] = str(preview_path)

                st.success("Multimodal analysis pipeline finished successfully!")
                st.rerun()

        # Display Frame Preview if available
        preview_key = f"preview_{session.id}"
        preview_file = config.uploads_dir / f"session_{session.id}_preview.jpg"
        if preview_file.exists():
            st.markdown("### 🖼️ Sample Visual Detection Preview")
            st.image(str(preview_file), caption=f"Session #{session.id} Annotated Frame Detection with Track IDs", use_column_width=True)
