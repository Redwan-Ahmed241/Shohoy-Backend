from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from schemas.auth import AuthUser
from schemas.volunteers import (
    VolunteerProfile,
    VolunteerAssignment,
    AssignmentCreatePayload,
    CheckInPayload,
    AvailabilityPayload,
    VerificationUpdatePayload,
)
from database.connection import get_db
from database.repository import repo
from routers.deps import require_roles, repository_errors

router = APIRouter(prefix="/volunteers", tags=["Volunteer Operations"])

# Field volunteers act on their own profile; coordinators may use the dashboard too.
volunteer = require_roles("fieldworker", "admin")
coordinator = require_roles("admin")


def _not_found(assignment_id: str):
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assignment '{assignment_id}' not found.")


# ── Coordinator endpoints ──

@router.get("", summary="List all registered field volunteers", dependencies=[Depends(coordinator)])
def list_volunteers(db: Session = Depends(get_db)):
    """Every field volunteer with contact details, skills, duty status and current task."""
    volunteers = repo.get_all_volunteers(db)
    return {"count": len(volunteers), "volunteers": volunteers}


@router.post("/assignments", response_model=VolunteerAssignment, status_code=status.HTTP_201_CREATED,
             summary="Create new field assignment", dependencies=[Depends(coordinator)])
def create_field_assignment(payload: AssignmentCreatePayload, db: Session = Depends(get_db)):
    """Coordinator posts a new open task to every volunteer dashboard."""
    return repo.create_assignment(db, payload.model_dump())


@router.get("/assignments/all", response_model=List[VolunteerAssignment],
            summary="All tasks with their assigned volunteer", dependencies=[Depends(coordinator)])
def list_all_assignments(status: Optional[str] = None, db: Session = Depends(get_db)):
    return repo.get_all_assignments(db, status=status)


@router.patch("/{user_id}/verification", summary="Approve, reject, or reset a volunteer's verification",
              dependencies=[Depends(coordinator)])
def set_volunteer_verification(user_id: str, payload: VerificationUpdatePayload, db: Session = Depends(get_db)):
    """A newly-registered field volunteer starts 'Pending' until a coordinator reviews and verifies them."""
    updated = repo.update_user(db, user_id, {"verification_status": payload.status})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Volunteer '{user_id}' not found.")
    return updated


@router.post("/assignments/{assignment_id}/cancel", response_model=VolunteerAssignment,
             summary="Cancel a task", dependencies=[Depends(coordinator)])
def cancel_assignment(assignment_id: str, db: Session = Depends(get_db)):
    """Withdraws an open or in-progress task; its citizen request returns to Verified."""
    with repository_errors():
        cancelled = repo.cancel_assignment(db, assignment_id)
    if not cancelled:
        raise _not_found(assignment_id)
    return cancelled


# ── Volunteer endpoints (always act on the signed-in volunteer) ──

@router.get("/profile", response_model=VolunteerProfile, summary="Get my volunteer profile")
def get_volunteer_profile(user: AuthUser = Depends(volunteer), db: Session = Depends(get_db)):
    """Hours, completed tasks, duty status and current task. Created on first visit."""
    return repo.get_volunteer_profile(db, user.model_dump())


@router.get("/assignments", response_model=List[VolunteerAssignment], summary="List open field assignments")
def get_open_assignments(user: AuthUser = Depends(volunteer), db: Session = Depends(get_db)):
    """Open tasks I haven't declined, tasks in my district first."""
    return repo.get_open_assignments(db, user.model_dump())


@router.post("/assignments/{assignment_id}/accept", summary="Accept a task")
def accept_assignment(assignment_id: str, user: AuthUser = Depends(volunteer), db: Session = Depends(get_db)):
    """Claims an open task. Returns 409 if someone else took it first or I already have one."""
    with repository_errors():
        assignment = repo.accept_assignment(db, user.model_dump(), assignment_id)
    if not assignment:
        raise _not_found(assignment_id)
    return {"success": True, "assignment": assignment, "status": "In Progress"}


@router.post("/assignments/{assignment_id}/decline", response_model=VolunteerProfile, summary="Decline or drop a task")
def decline_assignment(assignment_id: str, user: AuthUser = Depends(volunteer), db: Session = Depends(get_db)):
    """Hides an open task from my list, or hands my current task back to the open pool."""
    profile = repo.decline_assignment(db, user.model_dump(), assignment_id)
    if not profile:
        raise _not_found(assignment_id)
    return profile


@router.post("/checkin", response_model=VolunteerProfile, summary="Start, pause or complete duty")
def volunteer_checkin(payload: CheckInPayload, user: AuthUser = Depends(volunteer), db: Session = Depends(get_db)):
    """
    "Checked In" starts the duty clock, "Paused" stops it and adds the hours worked,
    "Completed" also finishes my current task and resolves its citizen request.
    """
    with repository_errors():
        return repo.checkin_volunteer(db, user.model_dump(), payload.status)


@router.post("/availability", response_model=VolunteerProfile, summary="Set whether I can take new tasks")
def set_availability(payload: AvailabilityPayload, user: AuthUser = Depends(volunteer), db: Session = Depends(get_db)):
    return repo.set_volunteer_availability(db, user.model_dump(), payload.isAvailable)
