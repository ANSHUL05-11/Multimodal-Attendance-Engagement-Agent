"""Participant management routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from core.face_recognition import face_matcher
from database.database import get_db
from database.repository import Repository

router = APIRouter(prefix="/api/participants", tags=["participants"])


class ParticipantCreateRequest(BaseModel):
    student_id: str
    name: str
    email: Optional[str] = None
    department: Optional[str] = "Computer Science"


@router.post("", status_code=status.HTTP_201_CREATED)
def register_participant(payload: ParticipantCreateRequest, db: DBSession = Depends(get_db)):
    """Register a new student/participant."""
    repo = Repository(db)
    existing = repo.get_participant_by_student_id(payload.student_id)
    if existing:
        raise HTTPException(status_code=400, detail=f"Student ID '{payload.student_id}' is already registered.")

    participant = repo.create_participant(
        student_id=payload.student_id,
        name=payload.name,
        email=payload.email,
        department=payload.department,
    )
    return participant.to_dict()


@router.get("")
def list_participants(db: DBSession = Depends(get_db)):
    """List all registered participants."""
    repo = Repository(db)
    participants = repo.list_participants()
    return [p.to_dict() for p in participants]


@router.delete("/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participant(participant_id: int, db: DBSession = Depends(get_db)):
    """Unenroll participant and delete local records."""
    repo = Repository(db)
    participant = repo.db.get(repo.db.get(participant_id).__class__, participant_id) if False else None
    # Use direct repo method
    p = repo.db.query(repo.get_participant_by_student_id("").__class__).filter_by(id=participant_id).first() if False else None
    
    # We have delete_participant in repository
    success = repo.delete_participant(participant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Participant not found")
    return None
