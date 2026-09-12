from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from schemas.requests import AssistanceRequestPayload, AssistanceRequestRecord
from database.connection import get_db
from database.supabase_repository import supabase_repo
from database.repository import db as mem_db

router = APIRouter(prefix="/requests", tags=["Assistance Requests"])

class RequestStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None
    assigned_volunteer_id: Optional[str] = None

@router.get("", response_model=List[AssistanceRequestRecord], summary="List all assistance requests")
def list_assistance_requests(
    status: Optional[str] = None,
    district: Optional[str] = None,
    db: Optional[Session] = Depends(get_db)
):
    """Admin endpoint to view and filter all citizen assistance requests."""
    if db is not None:
        return supabase_repo.get_all_requests(db, status=status, district=district)
    return mem_db.get_all_requests(status=status, district=district)

@router.post("", response_model=AssistanceRequestRecord, status_code=status.HTTP_201_CREATED, summary="Submit emergency assistance request")
def submit_assistance_request(payload: AssistanceRequestPayload, db: Optional[Session] = Depends(get_db)):
    """Citizen multi-step assistance request submission."""
    if db is not None:
        return supabase_repo.create_request(db, payload.model_dump())
    return mem_db.create_request(payload.model_dump())

@router.get("/track/{tracking_id}", response_model=AssistanceRequestRecord, summary="Track assistance request status")
def track_assistance_request(tracking_id: str, db: Optional[Session] = Depends(get_db)):
    """Query the real-time status of an emergency request using its unique tracking code."""
    if db is not None:
        record = supabase_repo.get_request_by_tracking_id(db, tracking_id)
    else:
        record = mem_db.get_request_by_tracking_id(tracking_id)

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assistance request with tracking ID '{tracking_id}' not found."
        )
    return record

@router.patch("/{request_id}/status", response_model=AssistanceRequestRecord, summary="Update assistance request status")
def update_request_status(request_id: str, update: RequestStatusUpdate, db: Optional[Session] = Depends(get_db)):
    """Admin updates the status of an emergency request (e.g. Verified, Assigned, In Progress, Resolved)."""
    if db is not None:
        updated = supabase_repo.update_request_status(db, request_id, update.status, notes=update.notes)
    else:
        updated = mem_db.update_request_status(request_id, update.status, notes=update.notes)

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assistance request '{request_id}' not found."
        )
    return updated
