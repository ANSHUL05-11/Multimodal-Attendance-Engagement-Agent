"""Multimodal Attendance & Engagement Agent - Configuration System.

Provides centralized configuration, hardware checks, and directory initialization.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

# Base workspace directory
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

# Set Matplotlib and Numba cache dirs to local writable paths
os.environ.setdefault("MPLCONFIGDIR", str(WORKSPACE_ROOT / "data" / ".cache" / "matplotlib"))
os.environ.setdefault("NUMBA_CACHE_DIR", str(WORKSPACE_ROOT / "data" / ".cache" / "numba"))


@dataclass
class AppConfig:
    """Application-wide settings with sensible defaults."""

    # General
    app_name: str = "Multimodal Attendance & Engagement Agent"
    debug: bool = False
    log_level: str = "INFO"

    # Paths
    root_dir: Path = WORKSPACE_ROOT
    data_dir: Path = WORKSPACE_ROOT / "data"
    uploads_dir: Path = WORKSPACE_ROOT / "data" / "uploads"
    samples_dir: Path = WORKSPACE_ROOT / "data" / "samples"
    database_url: str = f"sqlite:///{WORKSPACE_ROOT / 'data' / 'attendance_agent.db'}"

    # Server settings
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    streamlit_port: int = 8501

    # Vision processing
    frame_sampling_interval: int = 5  # sample every Nth frame
    min_presence_seconds: float = 10.0  # minimum cumulative seconds to qualify for attendance
    tracking_iou_threshold: float = 0.25  # IoU overlap threshold for matching tracks
    max_tracking_distance_pixels: float = 120.0  # Centroid distance threshold in pixels
    face_detection_confidence: float = 0.5
    track_max_disappeared_frames: int = 20  # allow momentary occlusion / head turn

    # Audio processing
    audio_sample_rate: int = 22050
    audio_frame_length: int = 2048
    audio_hop_length: int = 512
    vad_energy_threshold: float = 0.015  # RMS threshold for speech activity detection
    vad_zcr_threshold: float = 0.08      # Zero-crossing rate threshold
    noise_floor_percentile: float = 15.0 # Bottom percentile representing ambient background noise

    # Fusion & Engagement Indicator
    fusion_window_seconds: float = 2.0   # Temporal aggregation window
    weight_vision_presence: float = 0.40 # Weight of face presence in engagement index
    weight_vision_stability: float = 0.25 # Weight of tracking consistency
    weight_audio_speech: float = 0.20    # Weight of moderate conversational audio
    weight_audio_snr: float = 0.15       # Weight of signal-to-noise ratio

    # Privacy & Enrollment
    enable_local_recognition: bool = True
    enrolled_participants_file: Path = WORKSPACE_ROOT / "data" / "enrolled_faces.json"
    data_retention_days: int = 30

    def ensure_directories(self) -> None:
        """Create required runtime directories if they do not exist."""
        for d in [self.data_dir, self.uploads_dir, self.samples_dir, self.root_dir / "data" / ".cache"]:
            d.mkdir(parents=True, exist_ok=True)


config = AppConfig()
config.ensure_directories()


def setup_logger(name: str = "attendance_agent") -> logging.Logger:
    """Configure and return a structured logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        level = logging.DEBUG if config.debug else getattr(logging, config.log_level.upper(), logging.INFO)
        logger.setLevel(level)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


logger = setup_logger()


_CAMERA_CACHE: Optional[bool] = None


def check_camera_available(device_index: int = 0) -> bool:
    """Test if a local webcam can be opened on Windows without crashing or blocking.

    Bypasses hardware probing during automated tests or when hardware checks are disabled.
    """
    global _CAMERA_CACHE
    if _CAMERA_CACHE is not None:
        return _CAMERA_CACHE

    if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("CI") or os.environ.get("SKIP_CAMERA_CHECK") == "1":
        _CAMERA_CACHE = False
        return False

    try:
        import cv2

        backend = getattr(cv2, "CAP_DSHOW", cv2.CAP_ANY)
        cap = cv2.VideoCapture(device_index, backend)
        if not cap.isOpened():
            cap.release()
            _CAMERA_CACHE = False
            return False
        ret, frame = cap.read()
        cap.release()
        _CAMERA_CACHE = bool(ret and frame is not None and frame.size > 0)
        return _CAMERA_CACHE
    except Exception as exc:
        logger.warning("Camera check failed for device %d: %s", device_index, exc)
        _CAMERA_CACHE = False
        return False


def get_environment_info() -> dict:
    """Return diagnostic information about the runtime environment."""
    import platform
    import sys

    try:
        import cv2
        cv_ver = cv2.__version__
    except ImportError:
        cv_ver = "unavailable"

    try:
        import mediapipe
        mp_ver = getattr(mediapipe, "__version__", "available")
    except ImportError:
        mp_ver = "unavailable"

    try:
        import soundfile
        sf_ver = soundfile.__version__
    except ImportError:
        sf_ver = "unavailable"

    try:
        import librosa
        lr_ver = librosa.__version__
    except ImportError:
        lr_ver = "unavailable"

    return {
        "python_version": sys.version.split()[0],
        "os_platform": platform.platform(),
        "opencv_version": cv_ver,
        "mediapipe_version": mp_ver,
        "soundfile_version": sf_ver,
        "librosa_version": lr_ver,
        "camera_accessible": check_camera_available(0),
    }
