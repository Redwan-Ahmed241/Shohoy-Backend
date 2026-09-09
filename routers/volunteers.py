from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from schemas.volunteers import VolunteerProfile, VolunteerAssignment
from database.connection import get_db
from database.supabase_repository import supabase_repo
from database.repository import db as mem_db

router = APIRouter(prefix="/volunteers", tags=["Volunteer Operations"])

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

@router.post("/assignments/{assignment_id}/accept", summary="Accept volunteer assignment")
def accept_assignment(assignment_id: str, db: Optional[Session] = Depends(get_db)):
    """Volunteer accepts an open deployment task."""
    if db is not None:
        success = supabase_repo.update_assignment_status(db, assignment_id, "Assigned")
    else:
        success = mem_db.update_assignment_status(assignment_id, "Assigned")

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment '{assignment_id}' not found."
        )
    return {"success": True, "assignmentId": assignment_id, "status": "Assigned"}

@router.post("/assignments/{assignment_id}/decline", summary="Decline volunteer assignment")
def decline_assignment(assignment_id: str, db: Optional[Session] = Depends(get_db)):
    """Volunteer declines an assignment."""
    if db is not None:
        supabase_repo.update_assignment_status(db, assignment_id, "Available")
    else:
        mem_db.update_assignment_status(assignment_id, "Available")
    return {"success": True, "assignmentId": assignment_id, "status": "Available"}
