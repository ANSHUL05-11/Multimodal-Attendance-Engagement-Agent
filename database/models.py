"""Database Models for Multimodal Attendance & Engagement Agent.

Defines relational entities for participants, classroom sessions, attendance
proposals, visual and audio timeseries metrics, and teaching recommendations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    """Return timezone-aware current UTC time."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Participant(Base):
    """Enrolled participant / student profile."""

    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, default="Computer Science")
    is_enrolled: Mapped[bool] = mapped_column(Boolean, default=True)
    face_encoding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-serialized local feature vector
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    attendance_records: Mapped[List["AttendanceRecord"]] = relationship(
        "AttendanceRecord", back_populates="participant", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "name": self.name,
            "email": self.email,
            "department": self.department,
            "is_enrolled": self.is_enrolled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Session(Base):
    """Classroom or laboratory observation session metadata."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    course_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, default="CS401")
    instructor_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, default="Instructor")
    start_time: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    video_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    audio_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="created")  # created, processing, completed, error
    total_frames_sampled: Mapped[int] = mapped_column(Integer, default=0)
    heuristic_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    attendance_records: Mapped[List["AttendanceRecord"]] = relationship(
        "AttendanceRecord", back_populates="session", cascade="all, delete-orphan"
    )
    visual_metrics: Mapped[List["VisualMetric"]] = relationship(
        "VisualMetric", back_populates="session", cascade="all, delete-orphan"
    )
    audio_metrics: Mapped[List["AudioMetric"]] = relationship(
        "AudioMetric", back_populates="session", cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation", back_populates="session", cascade="all, delete-orphan"
    )
    summary: Mapped[Optional["SessionSummary"]] = relationship(
        "SessionSummary", back_populates="session", uselist=False, cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "course_code": self.course_code,
            "instructor_name": self.instructor_name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration_seconds, 2),
            "video_path": self.video_path,
            "audio_path": self.audio_path,
            "status": self.status,
            "total_frames_sampled": self.total_frames_sampled,
            "heuristic_score": round(self.heuristic_score, 1) if self.heuristic_score is not None else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AttendanceRecord(Base):
    """Attendance proposal for a participant or tracked visual entity."""

    __tablename__ = "attendance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), index=True)
    participant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("participants.id"), nullable=True, index=True)
    track_id: Mapped[int] = mapped_column(Integer, nullable=False)
    participant_label: Mapped[str] = mapped_column(String(128), default="Unassigned Track")

    # Status
    proposed_status: Mapped[str] = mapped_column(String(32), default="uncertain")  # present, absent, partial, uncertain
    instructor_status: Mapped[str] = mapped_column(String(32), default="pending_review")  # pending_review, confirmed, corrected, rejected

    # Observation evidence
    first_seen_sec: Mapped[float] = mapped_column(Float, default=0.0)
    last_seen_sec: Mapped[float] = mapped_column(Float, default=0.0)
    total_observed_sec: Mapped[float] = mapped_column(Float, default=0.0)
    presence_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    detection_count: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="attendance_records")
    participant: Mapped[Optional["Participant"]] = relationship("Participant", back_populates="attendance_records")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "track_id": self.track_id,
            "participant_label": self.participant_label,
            "proposed_status": self.proposed_status,
            "instructor_status": self.instructor_status,
            "first_seen_sec": round(self.first_seen_sec, 2),
            "last_seen_sec": round(self.last_seen_sec, 2),
            "total_observed_sec": round(self.total_observed_sec, 2),
            "presence_ratio": round(self.presence_ratio, 3),
            "detection_count": self.detection_count,
            "confidence": round(self.confidence, 2),
            "evidence_notes": self.evidence_notes,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }


class VisualMetric(Base):
    """Timestamped visual features extracted from sampled video frames."""

    __tablename__ = "visual_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), index=True)
    timestamp_sec: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    face_count: Mapped[int] = mapped_column(Integer, default=0)
    active_tracks_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_box_area_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    stability_score: Mapped[float] = mapped_column(Float, default=0.0)  # tracking continuity metric

    session: Mapped["Session"] = relationship("Session", back_populates="visual_metrics")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "timestamp_sec": round(self.timestamp_sec, 2),
            "face_count": self.face_count,
            "active_tracks_count": self.active_tracks_count,
            "avg_box_area_ratio": round(self.avg_box_area_ratio, 4),
            "stability_score": round(self.stability_score, 3),
        }


class AudioMetric(Base):
    """Timestamped acoustic features extracted from audio windows."""

    __tablename__ = "audio_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), index=True)
    timestamp_sec: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    rms_energy: Mapped[float] = mapped_column(Float, default=0.0)
    zcr: Mapped[float] = mapped_column(Float, default=0.0)
    spectral_centroid: Mapped[float] = mapped_column(Float, default=0.0)
    is_speech_active: Mapped[bool] = mapped_column(Boolean, default=False)
    background_noise_level: Mapped[float] = mapped_column(Float, default=0.0)
    snr_estimate: Mapped[float] = mapped_column(Float, default=0.0)

    session: Mapped["Session"] = relationship("Session", back_populates="audio_metrics")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "timestamp_sec": round(self.timestamp_sec, 2),
            "rms_energy": round(self.rms_energy, 4),
            "zcr": round(self.zcr, 4),
            "spectral_centroid": round(self.spectral_centroid, 1),
            "is_speech_active": self.is_speech_active,
            "background_noise_level": round(self.background_noise_level, 4),
            "snr_estimate": round(self.snr_estimate, 2),
        }


class SessionSummary(Base):
    """Aggregate session-level analytical summaries."""

    __tablename__ = "session_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), unique=True, index=True)
    average_engagement_score: Mapped[float] = mapped_column(Float, default=0.0)
    peak_engagement_sec: Mapped[float] = mapped_column(Float, default=0.0)
    speech_activity_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    avg_faces_visible: Mapped[float] = mapped_column(Float, default=0.0)
    total_unique_tracks: Mapped[int] = mapped_column(Integer, default=0)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)

    session: Mapped["Session"] = relationship("Session", back_populates="summary")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "average_engagement_score": round(self.average_engagement_score, 1),
            "peak_engagement_sec": round(self.peak_engagement_sec, 2),
            "speech_activity_ratio": round(self.speech_activity_ratio, 3),
            "avg_faces_visible": round(self.avg_faces_visible, 2),
            "total_unique_tracks": self.total_unique_tracks,
            "summary_text": self.summary_text,
        }


class Recommendation(Base):
    """Pedagogical context-aware teaching suggestion."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), index=True)
    category: Mapped[str] = mapped_column(String(64), default="classroom_dynamics")
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    observation: Mapped[str] = mapped_column(Text, nullable=False)
    suggestion: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(32), default="medium")  # low, medium, high
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    session: Mapped["Session"] = relationship("Session", back_populates="recommendations")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "category": self.category,
            "title": self.title,
            "observation": self.observation,
            "suggestion": self.suggestion,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
