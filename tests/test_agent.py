"""Tests for multimodal agent signal fusion across modalities."""

import pytest
from core.agent import MultimodalFusionAgent


def test_fusion_both_modalities():
    agent = MultimodalFusionAgent(window_sec=1.0)
    v_metrics = [
        {"timestamp_sec": 0.5, "face_count": 2, "active_tracks_count": 2, "avg_box_area_ratio": 0.05, "stability_score": 0.9},
        {"timestamp_sec": 1.5, "face_count": 2, "active_tracks_count": 2, "avg_box_area_ratio": 0.05, "stability_score": 1.0},
    ]
    a_metrics = [
        {"timestamp_sec": 0.5, "rms_energy": 0.03, "is_speech_active": True, "snr_estimate": 15.0},
        {"timestamp_sec": 1.5, "rms_energy": 0.01, "is_speech_active": False, "snr_estimate": 8.0},
    ]

    res = agent.fuse_signals(visual_metrics=v_metrics, audio_metrics=a_metrics, session_duration_sec=2.0)
    assert res["status"] == "success"
    assert res["modality_mode"] == "multimodal"
    assert 0.0 <= res["overall_heuristic_score"] <= 100.0
    assert len(res["fused_timeline"]) > 0
    assert "explanation" in res
    assert "limitations" in res


def test_fusion_video_only():
    agent = MultimodalFusionAgent(window_sec=1.0)
    v_metrics = [
        {"timestamp_sec": 0.5, "face_count": 3, "active_tracks_count": 3, "avg_box_area_ratio": 0.06, "stability_score": 0.8},
    ]
    res = agent.fuse_signals(visual_metrics=v_metrics, audio_metrics=None, session_duration_sec=1.0)
    assert res["status"] == "success"
    assert res["modality_mode"] == "video_only"
    assert res["overall_heuristic_score"] > 0


def test_fusion_audio_only():
    agent = MultimodalFusionAgent(window_sec=1.0)
    a_metrics = [
        {"timestamp_sec": 0.5, "rms_energy": 0.04, "is_speech_active": True, "snr_estimate": 18.0},
    ]
    res = agent.fuse_signals(visual_metrics=None, audio_metrics=a_metrics, session_duration_sec=1.0)
    assert res["status"] == "success"
    assert res["modality_mode"] == "audio_only"
    assert res["overall_heuristic_score"] > 0


def test_fusion_neither_modality():
    agent = MultimodalFusionAgent()
    res = agent.fuse_signals(visual_metrics=None, audio_metrics=None)
    assert res["status"] == "empty"
    assert res["modality_mode"] == "none"
    assert res["overall_heuristic_score"] == 0.0
