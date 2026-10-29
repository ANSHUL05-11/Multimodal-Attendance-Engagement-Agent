"""Seed realistic demonstration session and participant data."""

from __future__ import annotations

from pathlib import Path
from core.config import config, logger
from database.database import init_db, get_db_context
from database.repository import Repository
from core.vision import VisionProcessor
from core.audio_analysis import AudioProcessor
from core.agent import MultimodalFusionAgent
from core.analytics import SessionAnalytics
from core.recommendations import RecommendationEngine


def seed():
    init_db()
    logger.info("Seeding demonstration data...")

    with get_db_context() as db:
        repo = Repository(db)

        # 1. Enrolled Participants
        p1 = repo.get_participant_by_student_id("CS-2026-001")
        if not p1:
            p1 = repo.create_participant("CS-2026-001", "Aarav Sharma", "aarav.s@college.edu", "AI & Data Science")
        p2 = repo.get_participant_by_student_id("CS-2026-002")
        if not p2:
            p2 = repo.create_participant("CS-2026-002", "Diya Patel", "diya.p@college.edu", "AI & Data Science")
        p3 = repo.get_participant_by_student_id("CS-2026-003")
        if not p3:
            p3 = repo.create_participant("CS-2026-003", "Rohan Mehta", "rohan.m@college.edu", "Computer Engineering")

        # 2. Ensure rich demo session exists
        existing_sessions = repo.list_sessions()
        has_lecture_14 = any(s.title.startswith("Lecture 14") for s in existing_sessions)
        if not has_lecture_14:
            v_path = config.samples_dir / "sample_classroom_video.mp4"
            a_path = config.samples_dir / "sample_classroom_audio.wav"

            s = repo.create_session(
                title="Lecture 14: Multimodal Attention Architectures",
                course_code="AIDS-401",
                instructor_name="Prof. V. Raman",
                video_path=str(v_path),
                audio_path=str(a_path),
            )

            # Run analysis pipeline on demo files
            v_proc = VisionProcessor(sampling_interval=3, min_presence_sec=3.0)
            v_res = v_proc.process_video_file(str(v_path))
            repo.save_visual_metrics(s.id, v_res["visual_metrics"])
            created_records = repo.save_attendance_records(s.id, v_res["attendance_proposals"])

            # Link first 2 records to enrolled participants
            if len(created_records) >= 1:
                repo.update_attendance_status(created_records[0].id, "confirmed", "Verified by professor", p1.id)
            if len(created_records) >= 2:
                repo.update_attendance_status(created_records[1].id, "confirmed", "Verified by professor", p2.id)

            a_proc = AudioProcessor()
            a_res = a_proc.analyze_audio_file(str(a_path))
            repo.save_audio_metrics(s.id, a_res["audio_metrics"])

            fusion_agent = MultimodalFusionAgent()
            fused = fusion_agent.fuse_signals(
                visual_metrics=v_res["visual_metrics"],
                audio_metrics=a_res["audio_metrics"],
                session_duration_sec=v_res["duration_seconds"],
            )

            summary = SessionAnalytics.compute_summary_stats(
                session_duration_sec=v_res["duration_seconds"],
                visual_metrics=v_res["visual_metrics"],
                audio_metrics=a_res["audio_metrics"],
                tracks=v_res["tracks"],
                fused_result=fused,
            )
            repo.save_summary(s.id, summary)

            recs = RecommendationEngine.generate_recommendations(
                session_duration_sec=v_res["duration_seconds"],
                avg_faces=summary["avg_faces_visible"],
                speech_ratio=summary["speech_activity_ratio"],
                avg_snr_db=summary["avg_snr_db"],
                fused_timeline=fused.get("fused_timeline", []),
                tracks_count=len(v_res["tracks"]),
            )
            repo.save_recommendations(s.id, recs)

            repo.update_session(
                s.id,
                status="completed",
                duration_seconds=v_res["duration_seconds"],
                total_frames_sampled=v_res["sampled_frames"],
                heuristic_score=fused["overall_heuristic_score"],
            )
            logger.info("Seeded Demo Session #%d successfully!", s.id)


if __name__ == "__main__":
    seed()
