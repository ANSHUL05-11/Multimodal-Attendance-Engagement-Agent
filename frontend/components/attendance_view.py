"""Attendance Review and Manual Verification Component."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from database.database import get_db_context
from database.repository import Repository


def render_attendance_view() -> None:
    """Render Section C: Attendance Proposals and Instructor Verification Interface."""
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 2rem; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">
                Attendance Assistance & Instructor Review
            </h1>
            <p style="color: #94a3b8; font-size: 0.95rem;">
                Review automated visual presence proposals, inspect temporal evidence, and confirm or correct attendance status.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current_session_id = st.session_state.get("selected_session_id")
    if not current_session_id:
        st.warning("Please select an active session from the sidebar.")
        return

    with get_db_context() as db:
        repo = Repository(db)
        session = repo.get_session(current_session_id)
        if not session:
            st.error("Session not found.")
            return

        records = repo.get_session_attendance(current_session_id)
        participants = repo.list_participants()

    if not records:
        st.info(
            f"No attendance records for Session #{session.id}. "
            "Go to '📹 Session Workspace' and run the analysis pipeline first."
        )
        return

    # Metrics Summary
    present_count = sum(1 for r in records if r.proposed_status == "present")
    partial_count = sum(1 for r in records if r.proposed_status == "partial")
    uncertain_count = sum(1 for r in records if r.proposed_status == "uncertain")
    confirmed_count = sum(1 for r in records if r.instructor_status in ["confirmed", "corrected"])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Proposed Present", present_count)
    with c2:
        st.metric("Proposed Partial", partial_count)
    with c3:
        st.metric("Needs Review (Uncertain)", uncertain_count)
    with c4:
        st.metric("Instructor Verified", f"{confirmed_count}/{len(records)}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Attendance Records Table
    st.markdown("### 📋 Proposed Attendance Roster")
    table_rows = []
    for r in records:
        table_rows.append({
            "Record ID": r.id,
            "Track": f"#{r.track_id}",
            "Participant / Label": r.participant_label,
            "Proposed Status": r.proposed_status.upper(),
            "Instructor Decision": r.instructor_status.upper(),
            "First Seen": f"{r.first_seen_sec:.1f}s",
            "Last Seen": f"{r.last_seen_sec:.1f}s",
            "Observed Duration": f"{r.total_observed_sec:.1f}s",
            "Presence Ratio": f"{r.presence_ratio * 100:.1f}%",
            "Detections": r.detection_count,
            "Confidence": f"{r.confidence:.2f}",
            "Evidence / Notes": r.evidence_notes or "-",
        })

    df = pd.DataFrame(table_rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Instructor Verification Controls
    col_review, col_batch = st.columns([2, 1])

    with col_review:
        st.markdown("### ✍️ Manual Instructor Review & Correction")
        with st.form("attendance_review_form"):
            record_options = {r.id: f"Record #{r.id} ({r.participant_label} - Proposed: {r.proposed_status})" for r in records}
            selected_rec_id = st.selectbox(
                "Select Record to Review",
                options=list(record_options.keys()),
                format_func=lambda rid: record_options[rid],
            )

            col_act, col_link = st.columns(2)
            with col_act:
                new_status = st.selectbox(
                    "Instructor Decision",
                    ["confirmed", "corrected", "rejected", "pending_review"],
                    index=0,
                )
            with col_link:
                # Option to link to an enrolled participant
                participant_opts = {0: "None / Anonymous Track"}
                for p in participants:
                    participant_opts[p.id] = f"{p.name} ({p.student_id})"

                selected_pid = st.selectbox(
                    "Link to Enrolled Student Profile",
                    options=list(participant_opts.keys()),
                    format_func=lambda pid: participant_opts[pid],
                )

            instructor_note = st.text_input("Instructor Review Note", value="Verified presence in lecture recording.")
            save_decision = st.form_submit_button("Save Attendance Decision")

            if save_decision:
                with get_db_context() as db:
                    repo = Repository(db)
                    pid = selected_pid if selected_pid != 0 else None
                    repo.update_attendance_status(
                        record_id=selected_rec_id,
                        instructor_status=new_status,
                        evidence_notes=instructor_note,
                        participant_id=pid,
                    )
                st.success(f"Updated Record #{selected_rec_id} to '{new_status}'.")
                st.rerun()

    with col_batch:
        st.markdown("### ⚡ Quick Batch Actions")
        st.caption("Confirm all proposals meeting high-confidence presence thresholds with a single click.")
        if st.button("Batch Confirm High-Confidence ('Present') Records"):
            with get_db_context() as db:
                repo = Repository(db)
                count = 0
                for r in records:
                    if r.proposed_status == "present" and r.instructor_status == "pending_review":
                        repo.update_attendance_status(
                            record_id=r.id,
                            instructor_status="confirmed",
                            evidence_notes="Batch approved: High-confidence presence threshold met.",
                        )
                        count += 1
            st.success(f"Batch approved {count} records!")
            st.rerun()

    # Ethical Disclaimer Callout
    st.markdown(
        """
        <div style="background: #111827; border: 1px solid #374151; border-radius: 8px; padding: 12px 16px; margin-top: 20px; font-size: 0.85rem; color: #9ca3af;">
            <b>Ethical Notice:</b> Face detection does not constitute biometric identity proof. Visual tracking IDs
            can switch when individuals move, look away, or are momentarily occluded. Final attendance decisions must
            always be validated and submitted by an authorized human educator.
        </div>
        """,
        unsafe_allow_html=True,
    )
