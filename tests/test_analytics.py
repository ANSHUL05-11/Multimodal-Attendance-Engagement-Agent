"""Tests for session analytics and CSV exports."""

import pytest
from core.analytics import SessionAnalytics


def test_export_attendance_csv():
    records = [
        {
            "track_id": 1,
            "participant_label": "John Smith",
            "proposed_status": "present",
            "instructor_status": "confirmed",
            "first_seen_sec": 1.0,
            "last_seen_sec": 15.0,
            "total_observed_sec": 14.0,
            "presence_ratio": 0.93,
            "detection_count": 30,
            "confidence": 0.9,
            "evidence_notes": "Continuous presence",
        }
    ]
    csv_str = SessionAnalytics.export_attendance_csv(records)
    assert "track_id,participant_label" in csv_str
    assert "John Smith" in csv_str
    assert "present" in csv_str


def test_export_metrics_csv():
    timeline = [
        {
            "timestamp_sec": 1.0,
            "heuristic_score": 75.0,
            "faces_detected": 3,
            "active_tracks": 3,
            "stability": 0.95,
            "is_speech_active": True,
            "rms_energy": 0.025,
            "snr_db": 14.2,
        }
    ]
    csv_str = SessionAnalytics.export_session_metrics_csv(timeline)
    assert "timestamp_sec,heuristic_score" in csv_str
    assert "75.0" in csv_str
    assert "Yes" in csv_str
