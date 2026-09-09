from fastapi import APIRouter, HTTPException, status
from schemas.requests import AssistanceRequestPayload, AssistanceRequestRecord
from database.repository import db

router = APIRouter(prefix="/requests", tags=["Assistance Requests"])

@router.post("", response_model=AssistanceRequestRecord, status_code=status.HTTP_201_CREATED, summary="Submit emergency assistance request")
def submit_assistance_request(payload: AssistanceRequestPayload):
    """
    Citizen multi-step assistance request submission.
    Generates a unique tracking ID (e.g. SHY-2024-XXXXX) for status lookups.
    """
    return db.create_request(payload.model_dump())

@router.get("/track/{tracking_id}", response_model=AssistanceRequestRecord, summary="Track assistance request status")
def track_assistance_request(tracking_id: str):
    """
    Query the real-time status of an emergency request using its unique tracking code.
    """
    record = db.get_request_by_tracking_id(tracking_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assistance request with tracking ID '{tracking_id}' not found."
        )
    return record
