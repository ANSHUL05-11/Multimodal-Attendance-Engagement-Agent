"""Pytest Test Configuration and Fixtures."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session as DBSession, sessionmaker

from core.config import config
from database.models import Base
from generate_samples import create_demo_audio, create_demo_video


@pytest.fixture(scope="session")
def test_dirs() -> Generator[dict, None, None]:
    """Provide temporary test directories for media generation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        v_path = tmp_path / "test_video.mp4"
        a_path = tmp_path / "test_audio.wav"
        silent_a_path = tmp_path / "silent_audio.wav"

        # Generate synthetic video and audio
        create_demo_video(str(v_path), duration_sec=4.0, fps=15)
        create_demo_audio(str(a_path), duration_sec=4.0)

        # Generate silent audio
        import soundfile as sf
        sf.write(str(silent_a_path), np.zeros(22050 * 3, dtype=np.float32), 22050)

        yield {
            "root": tmp_path,
            "video_path": str(v_path),
            "audio_path": str(a_path),
            "silent_audio_path": str(silent_a_path),
        }


@pytest.fixture
def db_session() -> Generator[DBSession, None, None]:
    """Create an isolated in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
