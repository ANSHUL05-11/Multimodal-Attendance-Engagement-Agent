"""Context-Aware Teaching Recommendations Engine.

Generates transparent, non-punitive pedagogical suggestions based on observable trends.
Adheres strictly to respectful and constructive guidance for educators.
"""

from __future__ import annotations

from typing import Any, Dict, List


class RecommendationEngine:
    """Rule-based engine generating actionable suggestions for classroom sessions."""

    @staticmethod
    def generate_recommendations(
        session_duration_sec: float,
        avg_faces: float,
        speech_ratio: float,
        avg_snr_db: float,
        fused_timeline: List[Dict[str, Any]],
        tracks_count: int,
    ) -> List[Dict[str, Any]]:
        """Evaluate session metrics and return tailored observations and suggestions."""
        recommendations: List[Dict[str, Any]] = []

        # 1. Camera & Framing Evaluation
        if avg_faces < 1.0 and session_duration_sec > 5.0:
            recommendations.append({
                "category": "lighting_camera",
                "title": "Sub-optimal Camera Framing or Low Ambient Lighting",
                "observation": (
                    f"Average visible face count was {avg_faces:.1f}, which is unusually low. "
                    "Participants may be seated outside the camera frame or backlit."
                ),
                "suggestion": (
                    "Consider adjusting the webcam height, angling the camera toward the seating area, "
                    "or checking room illumination so attendees can be framed without glare."
                ),
                "priority": "high",
            })
        elif avg_faces > 0 and tracks_count > (avg_faces * 3.5):
            recommendations.append({
                "category": "lighting_camera",
                "title": "Frequent Visual Track Re-assignment",
                "observation": (
                    f"{tracks_count} unique tracks were generated for an average of {avg_faces:.1f} visible faces. "
                    "This usually indicates intermittent occlusion, rapid head movement, or camera shake."
                ),
                "suggestion": (
                    "Stabilize the camera mount and slightly lower the sampling interval for smoother "
                    "temporal continuity in large rooms."
                ),
                "priority": "medium",
            })

        # 2. Audio & Microphone Evaluation
        if speech_ratio < 0.10 and session_duration_sec > 10.0:
            recommendations.append({
                "category": "audio_mic",
                "title": "Low Acoustic Activity Detected",
                "observation": (
                    f"Estimated speech activity was detected in only {speech_ratio * 100:.1f}% of the session. "
                    "The audio stream is largely quiet."
                ),
                "suggestion": (
                    "If this was a lecture or discussion session, verify microphone sensitivity or positioning. "
                    "If this was an individual exam or silent reading period, this quiet level is expected and appropriate."
                ),
                "priority": "medium",
            })
        elif speech_ratio > 0.85:
            recommendations.append({
                "category": "audio_mic",
                "title": "Continuous High Acoustic Activity",
                "observation": (
                    f"Speech activity was detected in {speech_ratio * 100:.1f}% of session windows. "
                    "There was virtually no silence or quiet reflection intervals."
                ),
                "suggestion": (
                    "Review audio recordings to distinguish between collaborative debate versus ambient fan/HVAC noise. "
                    "Check if an omnidirectional mic is picking up hallway chatter."
                ),
                "priority": "low",
            })

        if avg_snr_db < 6.0 and avg_snr_db > 0.0:
            recommendations.append({
                "category": "audio_mic",
                "title": "High Ambient Noise Floor",
                "observation": (
                    f"The estimated Signal-to-Noise Ratio (SNR) averaged {avg_snr_db:.1f} dB, "
                    "indicating strong background room noise relative to speech signals."
                ),
                "suggestion": (
                    "Position the microphone closer to the speaker or podium, and consider activating "
                    "directional noise suppression or closing adjacent windows/doors."
                ),
                "priority": "high",
            })

        # 3. Classroom Interaction & Dynamics
        if 0.20 <= speech_ratio <= 0.65 and avg_faces >= 1.0:
            recommendations.append({
                "category": "engagement_flow",
                "title": "Balanced Lecture & Discussion Rhythm",
                "observation": (
                    f"Observed {speech_ratio * 100:.1f}% speech activity alongside steady participant presence. "
                    "Signals reflect a healthy cadence between instruction and conversational reflection."
                ),
                "suggestion": (
                    "Maintain this interactive pacing. Continue interspersing questions and peer-to-peer dialogues "
                    "throughout the presentation."
                ),
                "priority": "low",
            })

        # 4. Extended Inactivity Check
        quiet_streak = 0
        max_quiet_streak = 0
        for w in fused_timeline:
            if not w.get("is_speech_active", False) and w.get("faces_detected", 0) <= 1:
                quiet_streak += 1
                max_quiet_streak = max(max_quiet_streak, quiet_streak)
            else:
                quiet_streak = 0

        if max_quiet_streak >= 8:  # e.g., >16 consecutive seconds of absolute inactivity
            recommendations.append({
                "category": "classroom_dynamics",
                "title": "Extended Interval of Low Classroom Dynamics",
                "observation": (
                    f"A prolonged quiet interval of approximately {max_quiet_streak * 2} seconds was observed "
                    "with minimal physical movement or vocal response."
                ),
                "suggestion": (
                    "Educators can introduce a 60-second 'Think-Pair-Share' prompt or an interactive live poll "
                    "to re-energize the room when transitioning between lecture topics."
                ),
                "priority": "medium",
            })

        if not recommendations:
            recommendations.append({
                "category": "engagement_flow",
                "title": "Session Operating Within Standard Parameters",
                "observation": "Both visual detection and acoustic indicators demonstrated stable baseline levels.",
                "suggestion": "No critical technical or pedagogical adjustments identified.",
                "priority": "low",
            })

        return recommendations
