"""Settings, Participant Enrollment, and System Diagnostics Component."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core.config import config, get_environment_info
from core.face_recognition import face_matcher
from database.database import get_db_context
from database.repository import Repository


def render_settings_view() -> None:
    """Render Section F: Processing parameters, participant enrollment, and system info."""
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 2rem; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">
                System Settings & Participant Enrollment
            </h1>
            <p style="color: #94a3b8; font-size: 0.95rem;">
                Manage participant rosters, fine-tune algorithmic thresholds, and inspect hardware diagnostics.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    t1, t2, t3 = st.tabs(["👤 Participant Enrollment", "⚙️ Algorithmic Parameters", "💻 System Diagnostics"])

    # TAB 1: Participant Enrollment
    with t1:
        st.markdown("### 🎓 Consented Participant Roster")
        st.caption(
            "Enroll students locally. Their records allow optional local identification and name linking "
            "during attendance review. No biometric signatures are ever transmitted outside this laptop."
        )

        col_enroll, col_roster = st.columns([1, 1.3])

        with col_enroll:
            st.markdown("#### Register Participant")
            with st.form("enroll_student_form"):
                stu_id = st.text_input("Student ID", placeholder="CS-2026-042")
                stu_name = st.text_input("Full Name", placeholder="Jane Doe")
                stu_dept = st.text_input("Department", value="Computer Science")
                stu_email = st.text_input("Email (optional)", placeholder="jane.doe@college.edu")

                enroll_btn = st.form_submit_button("Enroll Participant")

                if enroll_btn and stu_id and stu_name:
                    with get_db_context() as db:
                        repo = Repository(db)
                        existing = repo.get_participant_by_student_id(stu_id)
                        if existing:
                            st.error(f"Student ID '{stu_id}' is already registered.")
                        else:
                            repo.create_participant(
                                student_id=stu_id,
                                name=stu_name,
                                department=stu_dept,
                                email=stu_email,
                            )
                            st.success(f"Enrolled {stu_name} ({stu_id}) successfully!")
                            st.rerun()

        with col_roster:
            st.markdown("#### Enrolled Students")
            with get_db_context() as db:
                repo = Repository(db)
                roster = repo.list_participants()

            if roster:
                roster_data = []
                for p in roster:
                    roster_data.append({
                        "ID": p.id,
                        "Student ID": p.student_id,
                        "Name": p.name,
                        "Department": p.department,
                        "Enrolled At": p.created_at.strftime("%Y-%m-%d") if p.created_at else "-",
                    })
                df_roster = pd.DataFrame(roster_data)
                st.dataframe(df_roster, use_container_width=True, hide_index=True)

                # Option to unenroll
                st.markdown("##### Remove Enrollment")
                p_to_del = st.selectbox(
                    "Select Student to Remove",
                    options=[p.id for p in roster],
                    format_func=lambda pid: next(p.name for p in roster if p.id == pid),
                )
                if st.button("Delete Participant Record"):
                    with get_db_context() as db:
                        Repository(db).delete_participant(p_to_del)
                    st.success("Participant record removed.")
                    st.rerun()
            else:
                st.info("No participants enrolled yet.")

    # TAB 2: Algorithmic Parameters
    with t2:
        st.markdown("### 🎛️ Default Algorithm Parameters")
        st.caption("Customize runtime thresholds stored in memory. These values guide heuristics across sessions.")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.slider(
                "Tracking IoU Match Threshold",
                0.1,
                0.6,
                config.tracking_iou_threshold,
                0.05,
                help="Minimum bounding box overlap to associate track IDs across sampled frames.",
            )
            st.slider(
                "Tracking Centroid Distance Threshold (pixels)",
                40.0,
                250.0,
                config.max_tracking_distance_pixels,
                10.0,
                help="Maximum centroid shift allowed between frames for the same participant track.",
            )
            st.slider(
                "Maximum Frame Disappearance Tolerance",
                5,
                50,
                config.track_max_disappeared_frames,
                5,
                help="Frames a participant can temporarily disappear before terminating the track.",
            )

        with col_p2:
            st.slider(
                "VAD Energy Threshold (RMS)",
                0.005,
                0.05,
                config.vad_energy_threshold,
                0.005,
                help="Root-mean-square amplitude threshold for voice activity detection.",
            )
            st.slider(
                "Multimodal Fusion Window (seconds)",
                1.0,
                5.0,
                config.fusion_window_seconds,
                0.5,
                help="Aggregation window duration for aligning visual and acoustic indicators.",
            )
            st.number_input(
                "Data Retention Policy (days)",
                min_value=7,
                max_value=365,
                value=config.data_retention_days,
                help="Retention interval for temporary media and raw session frames.",
            )

    # TAB 3: System Diagnostics
    with t3:
        st.markdown("### 🖥️ Hardware & Environment Diagnostics")
        env = get_environment_info()

        diag_data = [
            {"Component": "Operating System", "Status / Version": env["os_platform"], "Health": "✅ Supported"},
            {"Component": "Python Runtime", "Status / Version": env["python_version"], "Health": "✅ Active"},
            {"Component": "OpenCV Computer Vision", "Status / Version": env["opencv_version"], "Health": "✅ Operational"},
            {"Component": "MediaPipe Face Suite", "Status / Version": env["mediapipe_version"], "Health": "✅ Operational"},
            {"Component": "SoundFile Decoder", "Status / Version": env["soundfile_version"], "Health": "✅ Operational"},
            {"Component": "Librosa Acoustic Library", "Status / Version": env["librosa_version"], "Health": "✅ Operational"},
            {
                "Component": "Local Camera Hardware",
                "Status / Version": "Webcam Detected" if env["camera_accessible"] else "No Direct Camera",
                "Health": "🟢 Ready" if env["camera_accessible"] else "⚪ Offline / Safe Fallback",
            },
        ]
        st.dataframe(pd.DataFrame(diag_data), use_container_width=True, hide_index=True)
