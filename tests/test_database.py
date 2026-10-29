"""Tests for database models and repository operations."""

import pytest
from database.models import AttendanceRecord, Participant, Session
from database.repository import Repository


def test_session_lifecycle(db_session):
    repo = Repository(db_session)
    s = repo.create_session("AI Lecture", "CS401", "Dr. Rao")
    assert s.id is not None
    assert s.title == "AI Lecture"
    assert s.status == "created"

    updated = repo.update_session(s.id, status="completed", duration_seconds=120.5, heuristic_score=78.5)
    assert updated.status == "completed"
    assert updated.duration_seconds == 120.5
    assert updated.heuristic_score == 78.5

    listed = repo.list_sessions()
    assert len(listed) == 1


def test_participant_and_attendance(db_session):
    repo = Repository(db_session)
    p = repo.create_participant(student_id="STU-001", name="Alice Smith", email="alice@test.edu")
    assert p.id is not None
    assert p.student_id == "STU-001"

    s = repo.create_session("Lab 1", "CS401")
    proposals = [
        {
            "track_id": 1,
            "participant_label": "Track #1",
            "proposed_status": "present",
            "first_seen_sec": 0.5,
            "last_seen_sec": 12.0,
            "total_observed_sec": 11.5,
            "presence_ratio": 0.9,
            "detection_count": 25,
            "confidence": 0.85,
            "evidence_notes": "Sustained presence",
        }
    ]
    records = repo.save_attendance_records(s.id, proposals)
    assert len(records) == 1
    assert records[0].instructor_status == "pending_review"

    # Instructor confirms and links to participant
    rec_id = records[0].id
    updated_rec = repo.update_attendance_status(
        record_id=rec_id,
        instructor_status="confirmed",
        evidence_notes="Verified by instructor",
        participant_id=p.id,
    )
    assert updated_rec.instructor_status == "confirmed"
    assert updated_rec.participant_id == p.id
    assert updated_rec.participant_label == "Alice Smith"


def test_metrics_and_summary_persistence(db_session):
    repo = Repository(db_session)
    s = repo.create_session("Seminar", "CS500")

    v_metrics = [
        {"timestamp_sec": 1.0, "face_count": 2, "active_tracks_count": 2, "avg_box_area_ratio": 0.05, "stability_score": 0.9},
        {"timestamp_sec": 2.0, "face_count": 2, "active_tracks_count": 2, "avg_box_area_ratio": 0.05, "stability_score": 1.0},
    ]
    repo.save_visual_metrics(s.id, v_metrics)
    saved_v = repo.get_visual_metrics(s.id)
    assert len(saved_v) == 2
    assert saved_v[0].face_count == 2

    summary = repo.save_summary(s.id, {
        "average_engagement_score": 82.5,
        "peak_engagement_sec": 2.0,
        "speech_activity_ratio": 0.45,
        "avg_faces_visible": 2.0,
        "total_unique_tracks": 2,
        "summary_text": "Good engagement.",
    })
    assert summary.average_engagement_score == 82.5
