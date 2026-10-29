"""Core algorithms and processing modules."""

from core.agent import MultimodalFusionAgent
from core.analytics import SessionAnalytics
from core.audio_analysis import AudioProcessor
from core.config import AppConfig, check_camera_available, config, get_environment_info, logger, setup_logger
from core.face_recognition import LocalFaceMatcher, face_matcher
from core.recommendations import RecommendationEngine
from core.vision import DetectionBox, FaceDetector, ParticipantTrack, ParticipantTracker, VisionProcessor

__all__ = [
    "config",
    "AppConfig",
    "logger",
    "setup_logger",
    "check_camera_available",
    "get_environment_info",
    "DetectionBox",
    "ParticipantTrack",
    "FaceDetector",
    "ParticipantTracker",
    "VisionProcessor",
    "LocalFaceMatcher",
    "face_matcher",
    "AudioProcessor",
    "MultimodalFusionAgent",
    "SessionAnalytics",
    "RecommendationEngine",
]
