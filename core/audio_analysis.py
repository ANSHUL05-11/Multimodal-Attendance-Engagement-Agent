"""Audio Signal Analysis and Voice Activity Detection (VAD) Module.

Provides acoustic feature extraction (RMS energy, short-time energy variance,
zero-crossing rate, spectral centroid, SNR) and transparent speech activity heuristics.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import soundfile as sf

from core.config import config, logger


class AudioProcessor:
    """Robust local audio analyzer using SoundFile, Scipy, and Librosa with pure NumPy fallbacks."""

    def __init__(
        self,
        frame_length: int = config.audio_frame_length,
        hop_length: int = config.audio_hop_length,
        vad_energy_threshold: float = config.vad_energy_threshold,
        vad_zcr_threshold: float = config.vad_zcr_threshold,
        window_sec: float = 1.0,
    ) -> None:
        self.frame_length = frame_length
        self.hop_length = hop_length
        self.vad_energy_threshold = vad_energy_threshold
        self.vad_zcr_threshold = vad_zcr_threshold
        self.window_sec = window_sec

    def load_audio(self, audio_path: str, target_sr: int = config.audio_sample_rate) -> Tuple[np.ndarray, int]:
        """Safely load an audio file into a 1D float32 waveform and sample rate."""
        path = Path(audio_path)
        if not path.is_file():
            raise FileNotFoundError(f"Audio file does not exist: {audio_path}")

        try:
            # 1. Try SoundFile first (very fast for WAV, FLAC, OGG)
            data, sr = sf.read(str(path), dtype="float32")
            if data.ndim > 1:
                # Convert stereo/multichannel to mono
                data = np.mean(data, axis=1)
            return data, sr
        except Exception as sf_exc:
            logger.debug("SoundFile load failed (%s), trying Librosa.", sf_exc)

        try:
            import librosa
            data, sr = librosa.load(str(path), sr=target_sr, mono=True)
            return data.astype(np.float32), sr
        except Exception as lr_exc:
            raise ValueError(f"Could not decode audio file: {audio_path}. Reason: {lr_exc}")

    def compute_rms(self, y: np.ndarray) -> np.ndarray:
        """Compute frame-level Root Mean Square energy."""
        if len(y) == 0:
            return np.array([0.0], dtype=np.float32)

        # Pad signal to frame multiple
        pad_len = self.frame_length - (len(y) % self.hop_length)
        if pad_len > 0:
            y = np.pad(y, (0, pad_len), mode="constant")

        num_frames = 1 + (len(y) - self.frame_length) // self.hop_length
        rms = np.zeros(num_frames, dtype=np.float32)

        for i in range(num_frames):
            start = i * self.hop_length
            end = start + self.frame_length
            frame = y[start:end]
            rms[i] = np.sqrt(np.mean(frame**2))

        return rms

    def compute_zcr(self, y: np.ndarray) -> np.ndarray:
        """Compute frame-level Zero-Crossing Rate."""
        if len(y) < 2:
            return np.array([0.0], dtype=np.float32)

        num_frames = 1 + max(0, (len(y) - self.frame_length) // self.hop_length)
        zcr = np.zeros(num_frames, dtype=np.float32)

        for i in range(num_frames):
            start = i * self.hop_length
            end = start + self.frame_length
            frame = y[start:end]
            signs = np.sign(frame)
            crossings = np.sum(np.abs(np.diff(signs)) > 0)
            zcr[i] = crossings / (2.0 * len(frame))

        return zcr

    def compute_spectral_centroid(self, y: np.ndarray, sr: int) -> np.ndarray:
        """Compute spectral centroid using FFT for each frame."""
        if len(y) < self.frame_length:
            return np.array([0.0], dtype=np.float32)

        # Try Librosa if available
        try:
            import librosa
            sc = librosa.feature.spectral_centroid(
                y=y, sr=sr, n_fft=self.frame_length, hop_length=self.hop_length
            )
            return sc.flatten().astype(np.float32)
        except Exception:
            pass

        # Fallback pure NumPy FFT
        num_frames = 1 + (len(y) - self.frame_length) // self.hop_length
        freqs = np.fft.rfftfreq(self.frame_length, 1.0 / sr)
        centroids = np.zeros(num_frames, dtype=np.float32)

        window = np.hanning(self.frame_length)
        for i in range(num_frames):
            start = i * self.hop_length
            end = start + self.frame_length
            frame = y[start:end] * window
            mag = np.abs(np.fft.rfft(frame))
            mag_sum = np.sum(mag)
            if mag_sum > 1e-6:
                centroids[i] = float(np.sum(freqs * mag) / mag_sum)
            else:
                centroids[i] = 0.0

        return centroids

    def analyze_audio_file(
        self,
        audio_path: str,
        max_duration_sec: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Analyze an audio file and return timestamped acoustic metrics and session summary."""
        y, sr = self.load_audio(audio_path)

        if max_duration_sec is not None:
            max_samples = int(max_duration_sec * sr)
            y = y[:max_samples]

        duration_sec = len(y) / float(sr) if sr > 0 else 0.0

        # Edge case: silent or empty audio
        if len(y) == 0 or np.all(np.abs(y) < 1e-6):
            logger.info("Audio file is completely silent or empty.")
            return {
                "duration_seconds": duration_sec,
                "audio_metrics": [{
                    "timestamp_sec": 0.0,
                    "rms_energy": 0.0,
                    "zcr": 0.0,
                    "spectral_centroid": 0.0,
                    "is_speech_active": False,
                    "background_noise_level": 0.0,
                    "snr_estimate": 0.0,
                }],
                "speech_ratio": 0.0,
                "avg_rms": 0.0,
                "background_noise_floor": 0.0,
            }

        # Frame-level acoustic features
        rms_frames = self.compute_rms(y)
        zcr_frames = self.compute_zcr(y)
        centroid_frames = self.compute_spectral_centroid(y, sr)

        # Min frame count
        min_len = min(len(rms_frames), len(zcr_frames), len(centroid_frames))
        rms_frames = rms_frames[:min_len]
        zcr_frames = zcr_frames[:min_len]
        centroid_frames = centroid_frames[:min_len]

        # Estimate background noise floor (15th percentile of RMS)
        noise_floor = float(np.percentile(rms_frames, config.noise_floor_percentile))
        noise_floor = max(0.001, noise_floor)

        # Aggregate into uniform temporal windows (e.g., 1.0 second intervals)
        frames_per_sec = float(sr) / float(self.hop_length)
        window_size_frames = max(1, int(round(self.window_sec * frames_per_sec)))

        audio_metrics: List[Dict[str, Any]] = []
        speech_active_intervals = 0
        total_windows = max(1, int(math.ceil(min_len / window_size_frames)))

        for w_idx in range(total_windows):
            start_f = w_idx * window_size_frames
            end_f = min(min_len, start_f + window_size_frames)
            if start_f >= min_len:
                break

            w_rms = rms_frames[start_f:end_f]
            w_zcr = zcr_frames[start_f:end_f]
            w_centroid = centroid_frames[start_f:end_f]

            mean_rms = float(np.mean(w_rms))
            mean_zcr = float(np.mean(w_zcr))
            mean_centroid = float(np.mean(w_centroid))

            # Speech activity heuristic:
            # 1. RMS exceeds noise floor by significant margin
            # 2. RMS exceeds absolute threshold
            # 3. ZCR is in conversational speech range (typically 0.02 - 0.25)
            # 4. Spectral centroid is within human speech vocal frequencies (~300Hz - 3500Hz)
            is_speech = bool(
                (mean_rms > self.vad_energy_threshold)
                and (mean_rms > 1.8 * noise_floor)
                and (0.02 <= mean_zcr <= 0.35)
                and (250.0 <= mean_centroid <= 4500.0)
            )

            if is_speech:
                speech_active_intervals += 1

            # Estimate SNR in dB
            snr_db = 20.0 * math.log10(max(1e-4, mean_rms) / noise_floor)
            timestamp_sec = float(w_idx * self.window_sec)

            audio_metrics.append({
                "timestamp_sec": timestamp_sec,
                "rms_energy": mean_rms,
                "zcr": mean_zcr,
                "spectral_centroid": mean_centroid,
                "is_speech_active": is_speech,
                "background_noise_level": noise_floor,
                "snr_estimate": float(max(0.0, snr_db)),
            })

        speech_ratio = float(speech_active_intervals / max(1, len(audio_metrics)))
        avg_rms = float(np.mean(rms_frames))

        return {
            "duration_seconds": duration_sec,
            "audio_metrics": audio_metrics,
            "speech_ratio": speech_ratio,
            "avg_rms": avg_rms,
            "background_noise_floor": noise_floor,
        }
