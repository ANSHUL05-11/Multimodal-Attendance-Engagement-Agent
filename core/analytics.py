"""Session Analytics and Export Engine.

Processes timeseries metrics, compiles statistical summaries, and generates CSV exports.
"""

from __future__ import annotations

import csv
import io
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


class SessionAnalytics:
    """Computes session-level statistical aggregations and creates tabular export data."""

    @staticmethod
    def compute_summary_stats(
        session_duration_sec: float,
        visual_metrics: List[Dict[str, Any]],
        audio_metrics: List[Dict[str, Any]],
        tracks: List[Any],
        fused_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Aggregate all metrics into a clean session summary."""
        avg_faces = 0.0
        if visual_metrics:
            face_counts = [m.get("face_count", 0) for m in visual_metrics]
            avg_faces = float(np.mean(face_counts)) if face_counts else 0.0

        speech_ratio = 0.0
        avg_snr = 0.0
        if audio_metrics:
            speech_frames = [1 if m.get("is_speech_active", False) else 0 for m in audio_metrics]
            speech_ratio = float(np.mean(speech_frames)) if speech_frames else 0.0
            snr_values = [m.get("snr_estimate", 0.0) for m in audio_metrics]
            avg_snr = float(np.mean(snr_values)) if snr_values else 0.0

        heuristic_score = fused_result.get("overall_heuristic_score", 0.0)
        peak_time = fused_result.get("peak_engagement_sec", 0.0)
        total_tracks = len(tracks)

        summary_text = (
            f"Classroom session analyzed across {session_duration_sec:.1f}s. "
            f"Average visible participants: {avg_faces:.1f}. "
            f"Speech activity ratio: {speech_ratio * 100:.1f}%. "
            f"Average estimated SNR: {avg_snr:.1f} dB. "
            f"Heuristic activity score: {heuristic_score:.1f}/100."
        )

        return {
            "session_duration_sec": round(session_duration_sec, 2),
            "average_engagement_score": round(heuristic_score, 1),
            "peak_engagement_sec": round(peak_time, 2),
            "speech_activity_ratio": round(speech_ratio, 3),
            "avg_faces_visible": round(avg_faces, 2),
            "total_unique_tracks": total_tracks,
            "avg_snr_db": round(avg_snr, 1),
            "summary_text": summary_text,
        }

    @staticmethod
    def export_attendance_csv(attendance_records: List[Dict[str, Any]]) -> str:
        """Generate formatted CSV string for attendance records."""
        output = io.StringIO()
        fieldnames = [
            "track_id",
            "participant_label",
            "proposed_status",
            "instructor_status",
            "first_seen_sec",
            "last_seen_sec",
            "total_observed_sec",
            "presence_ratio_pct",
            "detection_count",
            "confidence",
            "evidence_notes",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for rec in attendance_records:
            writer.writerow({
                "track_id": rec.get("track_id", ""),
                "participant_label": rec.get("participant_label", ""),
                "proposed_status": rec.get("proposed_status", ""),
                "instructor_status": rec.get("instructor_status", "pending_review"),
                "first_seen_sec": f"{rec.get('first_seen_sec', 0.0):.2f}",
                "last_seen_sec": f"{rec.get('last_seen_sec', 0.0):.2f}",
                "total_observed_sec": f"{rec.get('total_observed_sec', 0.0):.2f}",
                "presence_ratio_pct": f"{rec.get('presence_ratio', 0.0) * 100:.1f}%",
                "detection_count": rec.get("detection_count", 0),
                "confidence": f"{rec.get('confidence', 0.0):.2f}",
                "evidence_notes": rec.get("evidence_notes", ""),
            })

        return output.getvalue()

    @staticmethod
    def export_session_metrics_csv(fused_timeline: List[Dict[str, Any]]) -> str:
        """Generate formatted CSV string for timeseries analytics."""
        output = io.StringIO()
        fieldnames = [
            "timestamp_sec",
            "heuristic_score",
            "faces_detected",
            "active_tracks",
            "stability",
            "is_speech_active",
            "rms_energy",
            "snr_db",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for row in fused_timeline:
            writer.writerow({
                "timestamp_sec": row.get("timestamp_sec", 0.0),
                "heuristic_score": row.get("heuristic_score", 0.0),
                "faces_detected": row.get("faces_detected", 0),
                "active_tracks": row.get("active_tracks", 0),
                "stability": row.get("stability", 0.0),
                "is_speech_active": "Yes" if row.get("is_speech_active") else "No",
                "rms_energy": f"{row.get('rms_energy', 0.0):.4f}",
                "snr_db": f"{row.get('snr_db', 0.0):.1f}",
            })

        return output.getvalue()
