"""Tests for audio signal analysis, RMS energy, and VAD heuristics."""

import numpy as np
import pytest

from core.audio_analysis import AudioProcessor


def test_audio_analysis_on_synthetic_speech(test_dirs):
    proc = AudioProcessor()
    res = proc.analyze_audio_file(test_dirs["audio_path"])

    assert res["duration_seconds"] > 0
    assert len(res["audio_metrics"]) > 0
    assert res["speech_ratio"] >= 0.0

    # First metric check
    m0 = res["audio_metrics"][0]
    assert "rms_energy" in m0
    assert "zcr" in m0
    assert "spectral_centroid" in m0
    assert "is_speech_active" in m0
    assert "snr_estimate" in m0


def test_silent_audio_handling(test_dirs):
    proc = AudioProcessor()
    res = proc.analyze_audio_file(test_dirs["silent_audio_path"])

    assert res["speech_ratio"] == 0.0
    assert res["avg_rms"] == 0.0
    for m in res["audio_metrics"]:
        assert not m["is_speech_active"]


def test_invalid_audio_path():
    proc = AudioProcessor()
    with pytest.raises(FileNotFoundError):
        proc.analyze_audio_file("invalid_audio_path_xyz.wav")
