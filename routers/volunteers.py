from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from schemas.volunteers import VolunteerProfile, VolunteerAssignment
from database.connection import get_db
from database.supabase_repository import supabase_repo
from database.repository import db as mem_db

router = APIRouter(prefix="/volunteers", tags=["Volunteer Operations"])

class AssignmentCreatePayload(BaseModel):
    title: str
    location: str
    district: str
    durationHours: int = 4
    teamSize: int = 4
    priority: str = "high"

class CheckInPayload(BaseModel):
    status: str = "Checked In"
    hours: int = 1

@router.get("", summary="List all registered field volunteers")
def list_volunteers(db: Optional[Session] = Depends(get_db)):
    """Fetches all registered volunteers with their status, contact details, and skills for Admin."""
    if db is not None:
        volunteers = supabase_repo.get_all_volunteers(db)
    else:
        volunteers = mem_db.get_all_volunteers()
    return {
        "count": len(volunteers),
        "volunteers": volunteers
    }

@router.get("/profile", response_model=VolunteerProfile, summary="Get logged-in volunteer profile")
def get_volunteer_profile(db: Optional[Session] = Depends(get_db)):
    """Fetch volunteer stats, hours logged, and active deployment assignment."""
    if db is not None:
        return supabase_repo.get_volunteer_profile(db)
    return mem_db.get_volunteer_profile()

@router.get("/assignments", response_model=List[VolunteerAssignment], summary="List open field assignments")
def get_open_assignments(db: Optional[Session] = Depends(get_db)):
    """List unassigned or available volunteer response tasks in disaster zones."""
    if db is not None:
        return supabase_repo.get_open_assignments(db)
    return mem_db.get_open_assignments()

@router.post("/assignments", response_model=VolunteerAssignment, status_code=status.HTTP_201_CREATED, summary="Create new field assignment")
def create_field_assignment(payload: AssignmentCreatePayload, db: Optional[Session] = Depends(get_db)):
    """Admin dispatches a new response assignment."""
    if db is not None:
        return supabase_repo.create_assignment(db, payload.model_dump())
    return mem_db.create_assignment(payload.model_dump())

@router.post("/assignments/{assignment_id}/accept", summary="Accept volunteer assignment")
def accept_assignment(assignment_id: str, db: Optional[Session] = Depends(get_db)):
    """Volunteer accepts an open deployment task."""
    if db is not None:
        assignment = supabase_repo.accept_assignment(db, assignment_id)
    else:
        assignment = mem_db.accept_assignment(assignment_id)

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment '{assignment_id}' not found."
        )
    return {"success": True, "assignment": assignment, "status": "In Progress"}

@router.post("/assignments/{assignment_id}/decline", summary="Decline volunteer assignment")
def decline_assignment(assignment_id: str, db: Optional[Session] = Depends(get_db)):
    """Volunteer declines an assignment."""
    if db is not None:
        success = supabase_repo.decline_assignment(db, assignment_id)
    else:
        success = mem_db.decline_assignment(assignment_id)
    return {"success": True, "assignmentId": assignment_id, "status": "Declined"}

@router.post("/checkin", summary="Volunteer check-in and duty hours tracking")
def volunteer_checkin(payload: CheckInPayload, db: Optional[Session] = Depends(get_db)):
    """Records on-duty check-in or completion and logs active volunteer hours."""
    if db is not None:
        return supabase_repo.checkin_volunteer(db, status=payload.status, hours=payload.hours)
    return mem_db.checkin_volunteer(status=payload.status, hours=payload.hours)
