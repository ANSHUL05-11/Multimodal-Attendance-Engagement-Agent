"""Session management and analysis routes."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from core.agent import MultimodalFusionAgent
from core.analytics import SessionAnalytics
from core.audio_analysis import AudioProcessor
from core.config import config, logger
from core.recommendations import RecommendationEngine
from core.vision import VisionProcessor
from database.database import get_db
from database.repository import Repository

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SessionCreateRequest(BaseModel):
    title: str
    course_code: Optional[str] = "CS401"
    instructor_name: Optional[str] = "Instructor"


class AnalyzeRequest(BaseModel):
    video_path: Optional[str] = None
    audio_path: Optional[str] = None
    sampling_interval: Optional[int] = None
    min_presence_sec: Optional[float] = None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreateRequest, db: DBSession = Depends(get_db)):
    """Create a new classroom observation session record."""
    repo = Repository(db)
    session = repo.create_session(
        title=payload.title,
        course_code=payload.course_code or "CS401",
        instructor_name=payload.instructor_name or "Instructor",
    )
    return session.to_dict()


@router.get("")
def list_sessions(limit: int = 50, db: DBSession = Depends(get_db)):
    """List recent classroom observation sessions."""
    repo = Repository(db)
    sessions = repo.list_sessions(limit=limit)
    return [s.to_dict() for s in sessions]


@router.get("/{session_id}")
def get_session(session_id: int, db: DBSession = Depends(get_db)):
    """Retrieve metadata for a specific session."""
    repo = Repository(db)
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@router.post("/upload")
async def upload_session_media(
    session_id: int = Form(...),
    file: UploadFile = File(...),
    media_type: str = Form(...),  # "video" or "audio"
    db: DBSession = Depends(get_db),
):
    """Upload media file for a session."""
    repo = Repository(db)
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    allowed_exts = {
        "video": {".mp4", ".avi", ".mov", ".mkv", ".webm"},
        "audio": {".wav", ".mp3", ".ogg", ".flac", ".m4a"},
    }

    ext = Path(file.filename).suffix.lower()
    if media_type not in allowed_exts or ext not in allowed_exts[media_type]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid extension '{ext}' for {media_type}. Allowed: {list(allowed_exts.get(media_type, []))}",
        )

    dest_filename = f"session_{session_id}_{media_type}{ext}"
    dest_path = config.uploads_dir / dest_filename

    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {exc}")

    if media_type == "video":
        repo.update_session(session_id, video_path=str(dest_path))
    else:
        repo.update_session(session_id, audio_path=str(dest_path))

    return {"message": "File uploaded successfully", "path": str(dest_path), "media_type": media_type}


@router.post("/{session_id}/analyze")
def analyze_session(
    session_id: int,
    payload: Optional[AnalyzeRequest] = None,
    db: DBSession = Depends(get_db),
):
    """Run multimodal vision and audio analysis pipeline for the session."""
    repo = Repository(db)
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    video_path = (payload.video_path if payload and payload.video_path else session.video_path)
    audio_path = (payload.audio_path if payload and payload.audio_path else session.audio_path)

    if not video_path and not audio_path:
        raise HTTPException(
            status_code=400,
            detail="Session has no attached video or audio file. Please upload media first.",
        )

    sampling_interval = (payload.sampling_interval if payload and payload.sampling_interval else config.frame_sampling_interval)
    min_presence = (payload.min_presence_sec if payload and payload.min_presence_sec else config.min_presence_seconds)

    repo.update_session(session_id, status="processing")

    try:
        visual_metrics = []
        tracks = []
        proposals = []
        duration_v = 0.0
        sampled_frames = 0

        # 1. Vision Analysis if video present
        if video_path and Path(video_path).is_file():
            v_proc = VisionProcessor(sampling_interval=sampling_interval, min_presence_sec=min_presence)
            v_result = v_proc.process_video_file(video_path)
            visual_metrics = v_result["visual_metrics"]
            tracks = v_result["tracks"]
            proposals = v_result["attendance_proposals"]
            duration_v = v_result["duration_seconds"]
            sampled_frames = v_result["sampled_frames"]
            repo.save_visual_metrics(session_id, visual_metrics)
            repo.save_attendance_records(session_id, proposals)

        # 2. Audio Analysis if audio present
        audio_metrics = []
        duration_a = 0.0
        if audio_path and Path(audio_path).is_file():
            a_proc = AudioProcessor()
            a_result = a_proc.analyze_audio_file(audio_path)
            audio_metrics = a_result["audio_metrics"]
            duration_a = a_result["duration_seconds"]
            repo.save_audio_metrics(session_id, audio_metrics)

        effective_duration = max(duration_v, duration_a, 1.0)

        # 3. Multimodal Signal Fusion
        fusion_agent = MultimodalFusionAgent()
        fused = fusion_agent.fuse_signals(
            visual_metrics=visual_metrics,
            audio_metrics=audio_metrics,
            session_duration_sec=effective_duration,
        )

        # 4. Analytics Summary
        summary_stats = SessionAnalytics.compute_summary_stats(
            session_duration_sec=effective_duration,
            visual_metrics=visual_metrics,
            audio_metrics=audio_metrics,
            tracks=tracks,
            fused_result=fused,
        )
        repo.save_summary(session_id, summary_stats)

        # 5. Teaching Recommendations
        recs = RecommendationEngine.generate_recommendations(
            session_duration_sec=effective_duration,
            avg_faces=summary_stats["avg_faces_visible"],
            speech_ratio=summary_stats["speech_activity_ratio"],
            avg_snr_db=summary_stats["avg_snr_db"],
            fused_timeline=fused.get("fused_timeline", []),
            tracks_count=len(tracks),
        )
        repo.save_recommendations(session_id, recs)

        repo.update_session(
            session_id,
            status="completed",
            duration_seconds=effective_duration,
            total_frames_sampled=sampled_frames,
            heuristic_score=fused.get("overall_heuristic_score", 0.0),
        )

        return {
            "status": "completed",
            "session_id": session_id,
            "duration_seconds": round(effective_duration, 2),
            "heuristic_score": fused.get("overall_heuristic_score", 0.0),
            "proposals_count": len(proposals),
            "recommendations_count": len(recs),
        }

    except Exception as exc:
        logger.error("Error analyzing session %d: %s", session_id, exc)
        repo.update_session(session_id, status="error")
        raise HTTPException(status_code=500, detail=f"Analysis pipeline failed: {exc}")


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, db: DBSession = Depends(get_db)):
    """Delete a session and all its associated records."""
    repo = Repository(db)
    success = repo.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return None
