from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from schemas.alerts import FloodAlert, FloodAlertCreate
from database.repository import db

router = APIRouter(prefix="/alerts", tags=["Flood Alerts"])

@router.get("", response_model=List[FloodAlert], summary="Get all flood alerts with optional filtering")
def get_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity level e.g. CRITICAL, HIGH, MEDIUM, LOW, ALL CLEAR"),
    search: Optional[str] = Query(None, description="Search query matching title, description or affected areas")
):
    """
    Fetch active disaster/flood alerts.
    Supports filtering by severity level and free-text search across titles and districts.
    """
    return db.get_alerts(severity=severity, search=search)

@router.get("/{alert_id}", response_model=FloodAlert, summary="Get single alert by ID")
def get_alert_by_id(alert_id: str):
    """
    Fetch details of a specific alert by its ID (e.g., 'alert-1').
    """
    alert = db.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID '{alert_id}' was not found"
        )
    return alert

@router.post("", response_model=FloodAlert, status_code=status.HTTP_201_CREATED, summary="Create a new emergency alert")
def create_alert(payload: FloodAlertCreate):
    """
    Publish a new flood alert (admin or emergency authority action).
    """
    return db.create_alert(payload.model_dump())
