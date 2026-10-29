"""Multimodal Agent for Signal Fusion and Interpretable Engagement Heuristics.

Combines visual presence signals and acoustic activity metrics across timestamped
windows into an interpretable 0-100 experimental index. Works gracefully with video-only,
audio-only, both, or neither modality.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from core.config import config, logger


class MultimodalFusionAgent:
    """Agent that aligns multimodal signals and applies transparent rule-based reasoning."""

    def __init__(
        self,
        window_sec: float = config.fusion_window_seconds,
        weight_presence: float = config.weight_vision_presence,
        weight_stability: float = config.weight_vision_stability,
        weight_speech: float = config.weight_audio_speech,
        weight_snr: float = config.weight_audio_snr,
    ) -> None:
        self.window_sec = window_sec
        self.w_presence = weight_presence
        self.w_stability = weight_stability
        self.w_speech = weight_speech
        self.w_snr = weight_snr

    def fuse_signals(
        self,
        visual_metrics: Optional[List[Dict[str, Any]]] = None,
        audio_metrics: Optional[List[Dict[str, Any]]] = None,
        session_duration_sec: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Align vision and audio metrics into synchronized temporal fusion windows.

        Calculates an experimental engagement heuristic (0-100) and transparent explanations.
        """
        has_video = bool(visual_metrics and len(visual_metrics) > 0)
        has_audio = bool(audio_metrics and len(audio_metrics) > 0)

        # Neither modality available
        if not has_video and not has_audio:
            return {
                "status": "empty",
                "overall_heuristic_score": 0.0,
                "modality_mode": "none",
                "fused_timeline": [],
                "explanation": "No visual or acoustic signal data was supplied for fusion.",
                "limitations": "Analysis requires at least one valid video or audio stream.",
            }

        # Determine effective duration
        max_v_time = max([m["timestamp_sec"] for m in visual_metrics]) if has_video else 0.0
        max_a_time = max([m["timestamp_sec"] for m in audio_metrics]) if has_audio else 0.0
        duration = session_duration_sec or max(max_v_time, max_a_time, 1.0)

        num_windows = max(1, int(math.ceil(duration / self.window_sec)))
        fused_timeline: List[Dict[str, Any]] = []

        window_scores: List[float] = []

        for w_idx in range(num_windows):
            t_start = w_idx * self.window_sec
            t_end = t_start + self.window_sec
            t_center = t_start + (self.window_sec / 2.0)

            # 1. Visual metrics in this window
            v_in_window = [m for m in visual_metrics if t_start <= m["timestamp_sec"] < t_end] if has_video else []
            if v_in_window:
                avg_faces = float(np.mean([m.get("face_count", 0) for m in v_in_window]))
                avg_stability = float(np.mean([m.get("stability_score", 0.0) for m in v_in_window]))
                active_tracks = int(max([m.get("active_tracks_count", 0) for m in v_in_window]))
            else:
                avg_faces = 0.0
                avg_stability = 0.0
                active_tracks = 0

            # 2. Audio metrics in this window
            a_in_window = [m for m in audio_metrics if t_start <= m["timestamp_sec"] < t_end] if has_audio else []
            if a_in_window:
                avg_rms = float(np.mean([m.get("rms_energy", 0.0) for m in a_in_window]))
                any_speech = any(m.get("is_speech_active", False) for m in a_in_window)
                avg_snr = float(np.mean([m.get("snr_estimate", 0.0) for m in a_in_window]))
            else:
                avg_rms = 0.0
                any_speech = False
                avg_snr = 0.0

            # 3. Transparent Heuristic Calculation
            # Presence component (0 - 100): 1-4 visible faces is typical good attendance framing
            if has_video:
                presence_score = min(100.0, avg_faces * 30.0)
                stability_score = avg_stability * 100.0
            else:
                presence_score = 50.0  # neutral placeholder when modality missing
                stability_score = 50.0

            # Acoustic component (0 - 100)
            if has_audio:
                speech_score = 80.0 if any_speech else 35.0
                snr_score = min(100.0, max(0.0, avg_snr * 4.0))  # 25dB SNR maps to ~100
            else:
                speech_score = 50.0
                snr_score = 50.0

            # Weighted combination depending on available modalities
            if has_video and has_audio:
                mode = "multimodal"
                score = (
                    self.w_presence * presence_score
                    + self.w_stability * stability_score
                    + self.w_speech * speech_score
                    + self.w_snr * snr_score
                )
            elif has_video:
                mode = "video_only"
                # Renormalize weights for vision alone
                norm = self.w_presence + self.w_stability
                score = (self.w_presence * presence_score + self.w_stability * stability_score) / norm
            else:
                mode = "audio_only"
                norm = self.w_speech + self.w_snr
                score = (self.w_speech * speech_score + self.w_snr * snr_score) / norm

            score = float(max(0.0, min(100.0, score)))
            window_scores.append(score)

            fused_timeline.append({
                "timestamp_sec": round(t_center, 2),
                "heuristic_score": round(score, 1),
                "faces_detected": round(avg_faces, 1),
                "active_tracks": active_tracks,
                "stability": round(avg_stability, 2),
                "is_speech_active": any_speech,
                "rms_energy": round(avg_rms, 4),
                "snr_db": round(avg_snr, 1),
            })

        mean_heuristic = float(np.mean(window_scores)) if window_scores else 0.0
        peak_time = (
            fused_timeline[int(np.argmax(window_scores))]["timestamp_sec"]
            if window_scores
            else 0.0
        )

        explanation, limitations = self._generate_transparent_explanation(
            mode=mode,
            mean_score=mean_heuristic,
            has_video=has_video,
            has_audio=has_audio,
            fused_timeline=fused_timeline,
        )

        return {
            "status": "success",
            "modality_mode": mode,
            "overall_heuristic_score": round(mean_heuristic, 1),
            "peak_engagement_sec": peak_time,
            "fused_timeline": fused_timeline,
            "explanation": explanation,
            "limitations": limitations,
        }

    def _generate_transparent_explanation(
        self,
        mode: str,
        mean_score: float,
        has_video: bool,
        has_audio: bool,
        fused_timeline: List[Dict[str, Any]],
    ) -> Tuple[str, str]:
        """Produce clear, educational explanations and explicit scientific disclaimers."""
        reasons = []

        if mode == "multimodal":
            reasons.append("Both video and audio feeds were integrated across time-synchronized windows.")
        elif mode == "video_only":
            reasons.append("Operating in visual-only mode. Acoustic indicators were omitted without penalizing attendance.")
        elif mode == "audio_only":
            reasons.append("Operating in audio-only mode. Visual presence and tracking metrics were unavailable.")

        if has_video:
            face_counts = [w["faces_detected"] for w in fused_timeline]
            avg_faces = np.mean(face_counts) if face_counts else 0.0
            reasons.append(f"Visual presence averaged {avg_faces:.1f} visible faces per window.")

        if has_audio:
            speech_windows = sum(1 for w in fused_timeline if w["is_speech_active"])
            speech_pct = (speech_windows / max(1, len(fused_timeline))) * 100.0
            reasons.append(f"Estimated speech activity was detected in {speech_pct:.1f}% of acoustic windows.")

        if mean_score >= 70.0:
            reasons.append("Signals indicate sustained participant visibility and balanced conversational vocal dynamics.")
        elif mean_score >= 40.0:
            reasons.append("Signals reflect moderate activity with intermittent quiet intervals or variable participant framing.")
        else:
            reasons.append("Signals reflect low detection rates or sustained classroom silence.")

        explanation = " ".join(reasons)

        limitations = (
            "IMPORTANT NOTICE: The calculated heuristic score (0–100) is an experimental proxy "
            "based purely on physical presence and acoustic energy. It is NOT a scientifically "
            "validated measurement of cognitive attention, emotional engagement, comprehension, "
            "or student effort. A quiet classroom or brief camera occlusion must not be interpreted as disengagement."
        )

        return explanation, limitations
