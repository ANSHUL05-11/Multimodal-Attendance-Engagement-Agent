"""Session analytics retrieval and export routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session as DBSession

from core.analytics import SessionAnalytics
from database.database import get_db
from database.repository import Repository

router = APIRouter(prefix="/api/sessions", tags=["analytics"])


@router.get("/{session_id}/analytics")
def get_session_analytics(session_id: int, db: DBSession = Depends(get_db)):
    """Retrieve all visual metrics, audio metrics, summary, and recommendations for a session."""
    repo = Repository(db)
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    v_metrics = [m.to_dict() for m in repo.get_visual_metrics(session_id)]
    a_metrics = [m.to_dict() for m in repo.get_audio_metrics(session_id)]
    summary = repo.get_summary(session_id)
    recommendations = [r.to_dict() for r in repo.get_recommendations(session_id)]

    return {
        "session": session.to_dict(),
        "summary": summary.to_dict() if summary else None,
        "recommendations": recommendations,
        "visual_metrics_count": len(v_metrics),
        "audio_metrics_count": len(a_metrics),
        "visual_metrics": v_metrics,
        "audio_metrics": a_metrics,
    }


@router.get("/{session_id}/export")
def export_session_data(
    session_id: int,
    export_type: str = Query("attendance", pattern="^(attendance|metrics)$"),
    db: DBSession = Depends(get_db),
):
    """Export attendance records or timeline metrics as a downloadable CSV."""
    repo = Repository(db)
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if export_type == "attendance":
        records = [r.to_dict() for r in repo.get_session_attendance(session_id)]
        csv_content = SessionAnalytics.export_attendance_csv(records)
        filename = f"attendance_session_{session_id}.csv"
    else:
        v_metrics = [m.to_dict() for m in repo.get_visual_metrics(session_id)]
        a_metrics = [m.to_dict() for m in repo.get_audio_metrics(session_id)]

        # Align into simple timeline
        from core.agent import MultimodalFusionAgent
        fused = MultimodalFusionAgent().fuse_signals(
            visual_metrics=v_metrics,
            audio_metrics=a_metrics,
            session_duration_sec=session.duration_seconds,
        )
        csv_content = SessionAnalytics.export_session_metrics_csv(fused.get("fused_timeline", []))
        filename = f"metrics_session_{session_id}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
