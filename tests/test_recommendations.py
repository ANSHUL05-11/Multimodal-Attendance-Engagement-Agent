"""Tests for transparent teaching recommendation rules."""

import pytest
from core.recommendations import RecommendationEngine


def test_low_faces_triggers_camera_suggestion():
    recs = RecommendationEngine.generate_recommendations(
        session_duration_sec=30.0,
        avg_faces=0.3,  # very low
        speech_ratio=0.3,
        avg_snr_db=15.0,
        fused_timeline=[],
        tracks_count=1,
    )
    categories = [r["category"] for r in recs]
    assert "lighting_camera" in categories
    assert any("Framing" in r["title"] or "Lighting" in r["title"] for r in recs)


def test_low_speech_triggers_audio_suggestion():
    recs = RecommendationEngine.generate_recommendations(
        session_duration_sec=30.0,
        avg_faces=2.0,
        speech_ratio=0.03,  # almost completely silent
        avg_snr_db=15.0,
        fused_timeline=[],
        tracks_count=2,
    )
    categories = [r["category"] for r in recs]
    assert "audio_mic" in categories


def test_balanced_classroom_positive_suggestion():
    recs = RecommendationEngine.generate_recommendations(
        session_duration_sec=30.0,
        avg_faces=2.5,
        speech_ratio=0.35,  # balanced speech
        avg_snr_db=18.0,
        fused_timeline=[],
        tracks_count=3,
    )
    assert any("Balanced" in r["title"] for r in recs)
