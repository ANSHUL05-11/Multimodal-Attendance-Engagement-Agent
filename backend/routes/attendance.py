"""Attendance review and correction routes."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from database.database import get_db
from database.repository import Repository

router = APIRouter(prefix="/api", tags=["attendance"])


class AttendanceReviewPatch(BaseModel):
    instructor_status: str  # confirmed, corrected, rejected, pending_review
    evidence_notes: Optional[str] = None
    participant_id: Optional[int] = None


@router.get("/sessions/{session_id}/attendance")
def get_session_attendance(session_id: int, db: DBSession = Depends(get_db)):
    """Retrieve proposed attendance records for a session."""
    repo = Repository(db)
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    records = repo.get_session_attendance(session_id)
    return [r.to_dict() for r in records]


@router.patch("/attendance/{attendance_id}")
def update_attendance_status(
    attendance_id: int,
    payload: AttendanceReviewPatch,
    db: DBSession = Depends(get_db),
):
    """Instructor review endpoint to confirm, correct, or reject an attendance proposal."""
    valid_statuses = {"confirmed", "corrected", "rejected", "pending_review"}
    if payload.instructor_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid instructor status '{payload.instructor_status}'. Allowed: {list(valid_statuses)}",
        )

    repo = Repository(db)
    record = repo.update_attendance_status(
        record_id=attendance_id,
        instructor_status=payload.instructor_status,
        evidence_notes=payload.evidence_notes,
        participant_id=payload.participant_id,
    )

    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    return record.to_dict()
