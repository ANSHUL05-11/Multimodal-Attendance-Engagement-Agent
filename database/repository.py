"""Repository pattern data access layer.

Provides reusable database operations for both FastAPI backend routes and Streamlit frontend.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session as DBSession

from database.models import (
    AttendanceRecord,
    AudioMetric,
    Participant,
    Recommendation,
    Session,
    SessionSummary,
    VisualMetric,
)


class Repository:
    """Unified repository for classroom intelligence records."""

    def __init__(self, db: DBSession) -> None:
        self.db = db

    # -------------------------------------------------------------
    # Session Operations
    # -------------------------------------------------------------
    def create_session(
        self,
        title: str,
        course_code: str = "CS401",
        instructor_name: str = "Instructor",
        video_path: Optional[str] = None,
        audio_path: Optional[str] = None,
    ) -> Session:
        session = Session(
            title=title,
            course_code=course_code,
            instructor_name=instructor_name,
            video_path=video_path,
            audio_path=audio_path,
            status="created",
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: int) -> Optional[Session]:
        return self.db.get(Session, session_id)

    def list_sessions(self, limit: int = 50) -> List[Session]:
        stmt = select(Session).order_by(desc(Session.created_at)).limit(limit)
        return list(self.db.scalars(stmt).all())

    def update_session(self, session_id: int, **kwargs: Any) -> Optional[Session]:
        session = self.get_session(session_id)
        if not session:
            return None
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        self.db.commit()
        self.db.refresh(session)
        return session

    def delete_session(self, session_id: int) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False
        self.db.delete(session)
        self.db.commit()
        return True

    # -------------------------------------------------------------
    # Participant Operations
    # -------------------------------------------------------------
    def create_participant(
        self,
        student_id: str,
        name: str,
        email: Optional[str] = None,
        department: Optional[str] = "Computer Science",
        face_encoding: Optional[str] = None,
    ) -> Participant:
        participant = Participant(
            student_id=student_id,
            name=name,
            email=email,
            department=department,
            face_encoding=face_encoding,
            is_enrolled=True,
        )
        self.db.add(participant)
        self.db.commit()
        self.db.refresh(participant)
        return participant

    def get_participant_by_student_id(self, student_id: str) -> Optional[Participant]:
        stmt = select(Participant).where(Participant.student_id == student_id)
        return self.db.scalars(stmt).first()

    def list_participants(self) -> List[Participant]:
        stmt = select(Participant).order_by(Participant.name)
        return list(self.db.scalars(stmt).all())

    def delete_participant(self, participant_id: int) -> bool:
        participant = self.db.get(Participant, participant_id)
        if not participant:
            return False
        self.db.delete(participant)
        self.db.commit()
        return True

    # -------------------------------------------------------------
    # Attendance Operations
    # -------------------------------------------------------------
    def save_attendance_records(
        self, session_id: int, records_data: List[Dict[str, Any]]
    ) -> List[AttendanceRecord]:
        created_records = []
        for item in records_data:
            rec = AttendanceRecord(
                session_id=session_id,
                participant_id=item.get("participant_id"),
                track_id=item.get("track_id", 0),
                participant_label=item.get("participant_label", f"Track #{item.get('track_id', 0)}"),
                proposed_status=item.get("proposed_status", "uncertain"),
                instructor_status="pending_review",
                first_seen_sec=item.get("first_seen_sec", 0.0),
                last_seen_sec=item.get("last_seen_sec", 0.0),
                total_observed_sec=item.get("total_observed_sec", 0.0),
                presence_ratio=item.get("presence_ratio", 0.0),
                detection_count=item.get("detection_count", 0),
                confidence=item.get("confidence", 0.5),
                evidence_notes=item.get("evidence_notes", ""),
            )
            self.db.add(rec)
            created_records.append(rec)
        self.db.commit()
        return created_records

    def get_session_attendance(self, session_id: int) -> List[AttendanceRecord]:
        stmt = select(AttendanceRecord).where(AttendanceRecord.session_id == session_id).order_by(AttendanceRecord.track_id)
        return list(self.db.scalars(stmt).all())

    def update_attendance_status(
        self,
        record_id: int,
        instructor_status: str,
        evidence_notes: Optional[str] = None,
        participant_id: Optional[int] = None,
    ) -> Optional[AttendanceRecord]:
        record = self.db.get(AttendanceRecord, record_id)
        if not record:
            return None
        record.instructor_status = instructor_status
        record.reviewed_at = datetime.now(timezone.utc)
        if evidence_notes is not None:
            record.evidence_notes = evidence_notes
        if participant_id is not None:
            record.participant_id = participant_id
            part = self.db.get(Participant, participant_id)
            if part:
                record.participant_label = part.name
        self.db.commit()
        self.db.refresh(record)
        return record

    # -------------------------------------------------------------
    # Metrics Operations
    # -------------------------------------------------------------
    def save_visual_metrics(self, session_id: int, metrics: List[Dict[str, Any]]) -> None:
        objs = [
            VisualMetric(
                session_id=session_id,
                timestamp_sec=m["timestamp_sec"],
                face_count=m.get("face_count", 0),
                active_tracks_count=m.get("active_tracks_count", 0),
                avg_box_area_ratio=m.get("avg_box_area_ratio", 0.0),
                stability_score=m.get("stability_score", 0.0),
            )
            for m in metrics
        ]
        self.db.bulk_save_objects(objs)
        self.db.commit()

    def get_visual_metrics(self, session_id: int) -> List[VisualMetric]:
        stmt = select(VisualMetric).where(VisualMetric.session_id == session_id).order_by(VisualMetric.timestamp_sec)
        return list(self.db.scalars(stmt).all())

    def save_audio_metrics(self, session_id: int, metrics: List[Dict[str, Any]]) -> None:
        objs = [
            AudioMetric(
                session_id=session_id,
                timestamp_sec=m["timestamp_sec"],
                rms_energy=m.get("rms_energy", 0.0),
                zcr=m.get("zcr", 0.0),
                spectral_centroid=m.get("spectral_centroid", 0.0),
                is_speech_active=m.get("is_speech_active", False),
                background_noise_level=m.get("background_noise_level", 0.0),
                snr_estimate=m.get("snr_estimate", 0.0),
            )
            for m in metrics
        ]
        self.db.bulk_save_objects(objs)
        self.db.commit()

    def get_audio_metrics(self, session_id: int) -> List[AudioMetric]:
        stmt = select(AudioMetric).where(AudioMetric.session_id == session_id).order_by(AudioMetric.timestamp_sec)
        return list(self.db.scalars(stmt).all())

    # -------------------------------------------------------------
    # Summary & Recommendations
    # -------------------------------------------------------------
    def save_summary(self, session_id: int, summary_data: Dict[str, Any]) -> SessionSummary:
        existing = self.db.scalars(select(SessionSummary).where(SessionSummary.session_id == session_id)).first()
        if existing:
            for k, v in summary_data.items():
                if hasattr(existing, k):
                    setattr(existing, k, v)
            self.db.commit()
            return existing

        summary = SessionSummary(
            session_id=session_id,
            average_engagement_score=summary_data.get("average_engagement_score", 0.0),
            peak_engagement_sec=summary_data.get("peak_engagement_sec", 0.0),
            speech_activity_ratio=summary_data.get("speech_activity_ratio", 0.0),
            avg_faces_visible=summary_data.get("avg_faces_visible", 0.0),
            total_unique_tracks=summary_data.get("total_unique_tracks", 0),
            summary_text=summary_data.get("summary_text", "Session processed successfully."),
        )
        self.db.add(summary)
        self.db.commit()
        self.db.refresh(summary)
        return summary

    def get_summary(self, session_id: int) -> Optional[SessionSummary]:
        stmt = select(SessionSummary).where(SessionSummary.session_id == session_id)
        return self.db.scalars(stmt).first()

    def save_recommendations(self, session_id: int, recs_data: List[Dict[str, Any]]) -> List[Recommendation]:
        created = []
        for r in recs_data:
            rec = Recommendation(
                session_id=session_id,
                category=r.get("category", "classroom_dynamics"),
                title=r.get("title", "Observation"),
                observation=r.get("observation", ""),
                suggestion=r.get("suggestion", ""),
                priority=r.get("priority", "medium"),
            )
            self.db.add(rec)
            created.append(rec)
        self.db.commit()
        return created

    def get_recommendations(self, session_id: int) -> List[Recommendation]:
        stmt = select(Recommendation).where(Recommendation.session_id == session_id).order_by(Recommendation.id)
        return list(self.db.scalars(stmt).all())
