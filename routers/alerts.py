from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status, Depends
from sqlalchemy.orm import Session
from schemas.alerts import FloodAlert, FloodAlertCreate
from database.connection import get_db
from database.supabase_repository import supabase_repo
from database.repository import db as mem_db

router = APIRouter(prefix="/alerts", tags=["Flood Alerts"])

@router.get("", response_model=List[FloodAlert], summary="Get all flood alerts")
def get_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity e.g. CRITICAL, HIGH, MEDIUM, LOW, ALL CLEAR"),
    search: Optional[str] = Query(None, description="Search keyword in title, description, or affected areas"),
    db: Optional[Session] = Depends(get_db)
):
    """Retrieve active flood and severe weather warnings."""
    if db is not None:
        return supabase_repo.get_alerts(db, severity=severity, search=search)
    return mem_db.get_alerts(severity=severity, search=search)

@router.get("/{alert_id}", response_model=FloodAlert, summary="Get alert by ID")
def get_alert_by_id(alert_id: str, db: Optional[Session] = Depends(get_db)):
    """Fetch single alert details by unique identifier."""
    if db is not None:
        alert = supabase_repo.get_alert_by_id(db, alert_id)
    else:
        alert = mem_db.get_alert_by_id(alert_id)

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID '{alert_id}' not found."
        )
    return alert

@router.post("", response_model=FloodAlert, status_code=status.HTTP_201_CREATED, summary="Create new flood alert")
def create_alert(payload: FloodAlertCreate, db: Optional[Session] = Depends(get_db)):
    """Publish a verified flood warning or hazard alert."""
    if db is not None:
        return supabase_repo.create_alert(db, payload.model_dump())
    return mem_db.create_alert(payload.model_dump())
