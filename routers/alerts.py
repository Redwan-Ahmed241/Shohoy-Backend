from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status, Depends
from sqlalchemy.orm import Session
from schemas.alerts import FloodAlert, FloodAlertCreate
from database.connection import get_db
from database.repository import repo
from routers.deps import require_roles

router = APIRouter(prefix="/alerts", tags=["Flood Alerts"])

@router.get("", response_model=List[FloodAlert], summary="Get all flood alerts")
def get_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity e.g. CRITICAL, HIGH, MEDIUM, LOW, ALL CLEAR"),
    search: Optional[str] = Query(None, description="Search keyword in title, description, or affected areas"),
    db: Session = Depends(get_db)
):
    """Retrieve active flood and severe weather warnings (public)."""
    return repo.get_alerts(db, severity=severity, search=search)

@router.get("/{alert_id}", response_model=FloodAlert, summary="Get alert by ID")
def get_alert_by_id(alert_id: str, db: Session = Depends(get_db)):
    """Fetch single alert details by unique identifier (public)."""
    alert = repo.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID '{alert_id}' not found."
        )
    return alert

@router.post(
    "",
    response_model=FloodAlert,
    status_code=status.HTTP_201_CREATED,
    summary="Create new flood alert (coordinators)",
    dependencies=[Depends(require_roles("admin"))],
)
def create_alert(payload: FloodAlertCreate, db: Session = Depends(get_db)):
    """Publish a verified flood warning or hazard alert."""
    return repo.create_alert(db, payload.model_dump())
