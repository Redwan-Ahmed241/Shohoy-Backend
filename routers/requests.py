from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from schemas.requests import (
    AssistanceRequestPayload,
    AssistanceRequestRecord,
    AssistanceRequestAdminRecord,
    AssistanceRequestTracking,
    RequestStatusUpdate,
    DispatchPayload,
)
from database.connection import get_db
from database.repository import repo
from routers.deps import require_roles, repository_errors

router = APIRouter(prefix="/requests", tags=["Assistance Requests"])

coordinator_only = [Depends(require_roles("admin"))]


@router.post("", response_model=AssistanceRequestRecord, status_code=status.HTTP_201_CREATED, summary="Submit emergency assistance request")
def submit_assistance_request(payload: AssistanceRequestPayload, db: Session = Depends(get_db)):
    """Citizen multi-step assistance request submission. No account needed."""
    return repo.create_request(db, payload.model_dump())


@router.get("/track/{tracking_id}", response_model=AssistanceRequestTracking, summary="Track assistance request status")
def track_assistance_request(tracking_id: str, db: Session = Depends(get_db)):
    """Public progress of a request by tracking code. Names, phones and addresses are not returned."""
    record = repo.get_request_by_tracking_id(db, tracking_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assistance request with tracking ID '{tracking_id}' not found."
        )
    return record


@router.get("", response_model=List[AssistanceRequestAdminRecord], summary="List all assistance requests", dependencies=coordinator_only)
def list_assistance_requests(
    status: Optional[str] = None,
    district: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Coordinator view of every citizen request, with the volunteer task dispatched for it."""
    return repo.get_all_requests(db, status=status, district=district)


@router.patch("/{request_id}/status", response_model=AssistanceRequestAdminRecord, summary="Update assistance request status", dependencies=coordinator_only)
def update_request_status(request_id: str, update: RequestStatusUpdate, db: Session = Depends(get_db)):
    """Coordinator updates the status of an emergency request (e.g. Verified, Resolved)."""
    updated = repo.update_request_status(db, request_id, update.status, notes=update.notes)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assistance request '{request_id}' not found."
        )
    return updated


@router.post("/{request_id}/dispatch", response_model=AssistanceRequestAdminRecord, summary="Dispatch a request to field volunteers", dependencies=coordinator_only)
def dispatch_request(request_id: str, payload: DispatchPayload, db: Session = Depends(get_db)):
    """
    Creates an open volunteer task linked to this request and marks it "Assigned".
    When a volunteer accepts the task the request becomes "In Progress", and when they
    complete it the request becomes "Resolved" automatically.
    """
    with repository_errors():
        updated = repo.dispatch_request(db, request_id, payload.model_dump())
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assistance request '{request_id}' not found."
        )
    return updated
