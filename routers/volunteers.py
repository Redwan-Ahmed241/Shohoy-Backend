from typing import List
from fastapi import APIRouter, HTTPException, status
from schemas.volunteers import VolunteerProfile, VolunteerAssignment
from database.repository import db

router = APIRouter(prefix="/volunteers", tags=["Volunteer Operations"])

@router.get("/profile", response_model=VolunteerProfile, summary="Get logged-in volunteer profile")
def get_volunteer_profile():
    """
    Fetch volunteer stats, hours logged, and active deployment assignment.
    """
    return db.get_volunteer_profile()

@router.get("/assignments", response_model=List[VolunteerAssignment], summary="List open field assignments")
def get_open_assignments():
    """
    List unassigned or available volunteer response tasks in disaster zones.
    """
    return db.get_open_assignments()

@router.post("/assignments/{assignment_id}/accept", summary="Accept volunteer assignment")
def accept_assignment(assignment_id: str):
    """
    Volunteer accepts an open deployment task.
    """
    success = db.update_assignment_status(assignment_id, "Assigned")
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment '{assignment_id}' not found"
        )
    return {"success": True, "assignmentId": assignment_id, "status": "Assigned"}

@router.post("/assignments/{assignment_id}/decline", summary="Decline volunteer assignment")
def decline_assignment(assignment_id: str):
    """
    Volunteer declines an assignment.
    """
    success = db.update_assignment_status(assignment_id, "Available")
    return {"success": True, "assignmentId": assignment_id, "status": "Available"}
