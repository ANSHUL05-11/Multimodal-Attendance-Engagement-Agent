"""Synthetic Media Sample Generator for Windows Laptop Testing & Demo.

Generates synthetic classroom video (with animated geometric human faces) and
audio (with alternating vocal harmonics and ambient noise) without requiring
any real student video files or webcam hardware.
"""

from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np
import soundfile as sf

from core.config import config, logger


def draw_synthetic_face(frame: np.ndarray, center_x: int, center_y: int, scale: float = 1.0) -> None:
    """Draw a realistic face oval with eyes, eyebrows, nose, and mouth on frame."""
    rad_x = int(35 * scale)
    rad_y = int(45 * scale)

    # Face contour (skin tone)
    cv2.ellipse(frame, (center_x, center_y), (rad_x, rad_y), 0, 0, 360, (190, 215, 240), -1)
    cv2.ellipse(frame, (center_x, center_y), (rad_x, rad_y), 0, 0, 360, (130, 160, 190), 2)

    # Hair / forehead arc
    cv2.ellipse(frame, (center_x, center_y - int(25 * scale)), (rad_x, int(20 * scale)), 0, 180, 360, (40, 50, 70), -1)

    # Eyes
    eye_offset_x = int(14 * scale)
    eye_offset_y = int(8 * scale)
    cv2.circle(frame, (center_x - eye_offset_x, center_y - eye_offset_y), int(5 * scale), (255, 255, 255), -1)
    cv2.circle(frame, (center_x + eye_offset_x, center_y - eye_offset_y), int(5 * scale), (255, 255, 255), -1)
    cv2.circle(frame, (center_x - eye_offset_x, center_y - eye_offset_y), int(2 * scale), (40, 30, 30), -1)
    cv2.circle(frame, (center_x + eye_offset_x, center_y - eye_offset_y), int(2 * scale), (40, 30, 30), -1)

    # Nose
    cv2.line(frame, (center_x, center_y - int(2 * scale)), (center_x, center_y + int(8 * scale)), (120, 140, 170), 2)

    # Mouth
    cv2.ellipse(frame, (center_x, center_y + int(20 * scale)), (int(10 * scale), int(4 * scale)), 0, 0, 180, (80, 90, 180), 2)


def create_demo_video(output_path: str, duration_sec: float = 10.0, fps: int = 25) -> str:
    """Create a synthetic classroom MP4 video file with simulated participants."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    width, height = 640, 480
    total_frames = int(duration_sec * fps)

    # FourCC codec - try mp4v which is universal on Windows OpenCV
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(out_file), fourcc, fps, (width, height))

    logger.info("Generating synthetic classroom video (%s, %.1fs, %d frames)...", out_file.name, duration_sec, total_frames)

    for i in range(total_frames):
        t = i / fps
        # Background: dark classroom / auditorium
        frame = np.full((height, width, 3), (30, 25, 20), dtype=np.uint8)

        # Classroom desk line
        cv2.line(frame, (0, 380), (width, 380), (70, 60, 50), 3)

        # Participant 1: Left seat, gentle breathing motion
        p1_x = int(180 + 10 * math.sin(t * 1.5))
        p1_y = int(240 + 5 * math.cos(t * 1.5))
        draw_synthetic_face(frame, p1_x, p1_y, scale=1.1)

        # Participant 2: Right seat, steady presence
        p2_x = int(460 + 8 * math.cos(t * 1.2))
        p2_y = int(250 + 4 * math.sin(t * 1.2))
        draw_synthetic_face(frame, p2_x, p2_y, scale=1.0)

        # Participant 3: Center seat, enters at t=3.0s (demonstrates entry/late arrival)
        if t >= 3.0:
            p3_x = int(320 + 6 * math.sin(t * 2.0))
            p3_y = int(280 + 3 * math.cos(t * 2.0))
            draw_synthetic_face(frame, p3_x, p3_y, scale=0.9)

        # Classroom whiteboard banner
        cv2.putText(
            frame,
            f"Classroom Simulation [T={t:.1f}s]",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 220, 255),
            2,
            cv2.LINE_AA,
        )

        out.write(frame)

    out.release()
    logger.info("Synthetic video generated at: %s", str(out_file))
    return str(out_file)


def create_demo_audio(output_path: str, duration_sec: float = 10.0, sr: int = 22050) -> str:
    """Create a synthetic classroom WAV audio file with alternating speech and ambient noise."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    num_samples = int(duration_sec * sr)
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)

    # 1. Ambient classroom background noise (air conditioning / room tone, low amplitude)
    noise = np.random.normal(0, 0.005, num_samples).astype(np.float32)

    # 2. Vocal speech bursts (harmonic fundamentals at ~300Hz, 600Hz, 900Hz)
    signal = np.zeros(num_samples, dtype=np.float32)

    # Speech interval 1: 1.0s to 4.0s
    mask1 = (t >= 1.0) & (t <= 4.0)
    speech1 = (
        0.05 * np.sin(2 * np.pi * 320 * t)
        + 0.03 * np.sin(2 * np.pi * 640 * t)
        + 0.02 * np.sin(2 * np.pi * 960 * t)
    )
    signal[mask1] += speech1[mask1]

    # Speech interval 2: 6.0s to 9.5s
    mask2 = (t >= 6.0) & (t <= 9.5)
    speech2 = (
        0.06 * np.sin(2 * np.pi * 280 * t)
        + 0.04 * np.sin(2 * np.pi * 560 * t)
        + 0.02 * np.sin(2 * np.pi * 840 * t)
    )
    signal[mask2] += speech2[mask2]

    # Combine signal and ambient noise
    audio = signal + noise
    audio = audio.astype(np.float32)

    sf.write(str(out_file), audio, sr)
    logger.info("Synthetic audio generated at: %s", str(out_file))
    return str(out_file)


if __name__ == "__main__":
    v = create_demo_video(str(config.samples_dir / "sample_classroom_video.mp4"), duration_sec=10.0)
    a = create_demo_audio(str(config.samples_dir / "sample_classroom_audio.wav"), duration_sec=10.0)
    print(f"Generated demo samples:\n- {v}\n- {a}")
