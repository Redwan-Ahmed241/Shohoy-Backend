"""
UAV (drone) monitoring API — the ResQTech FYDP backend, merged into Shohay.

Two kinds of callers:
  * Drones authenticate with headers  X-Drone-Id: <registration id>  and  X-Drone-Token: <api key>
    and send heartbeats, stream URLs and detections.
  * People authenticate with their normal Shohay sign-in. Coordinators see everything;
    field volunteers see only drones they are assigned to.

Real-time: the dashboard polls GET /uav/detections?since=<last createdAt> every few seconds.
Polling works on serverless hosting (Vercel), unlike WebSockets which need one long-lived server.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import UavDroneModel
from database.uav_repository import uav_repo
from routers.deps import get_current_drone, repository_errors, require_roles
from schemas.auth import AuthUser
from schemas.uav import (
    DetectionCreate, DetectionOut, DroneCreate, DroneHeartbeat, DroneOut, DroneStreamUpdate,
    DroneUpdate, DroneWithKey, RescueRequestOut, RescuerAssignmentCreate, RescuerAssignmentOut, UavLogOut,
)

router = APIRouter(prefix="/uav", tags=["UAV / Drone Monitoring"])

coordinator = require_roles("admin")
coordinator_or_rescuer = require_roles("admin", "fieldworker")


# ── Drone device endpoints (X-Drone-Id / X-Drone-Token) ──

@router.post("/drones/heartbeat", response_model=DroneOut, summary="[Drone] Heartbeat with GPS and battery")
def drone_heartbeat(payload: DroneHeartbeat, drone: UavDroneModel = Depends(get_current_drone), db: Session = Depends(get_db)):
    """Send every 5-30 seconds. A drone with no heartbeat for 2 minutes shows as offline."""
    with repository_errors():
        return uav_repo.record_heartbeat(db, drone, payload.model_dump())


@router.post("/drones/stream", response_model=DroneOut, summary="[Drone] Report live video stream URL")
def drone_stream(payload: DroneStreamUpdate, drone: UavDroneModel = Depends(get_current_drone), db: Session = Depends(get_db)):
    return uav_repo.update_stream(db, drone, payload.stream_url)


@router.post("/detections", response_model=DetectionOut, status_code=status.HTTP_201_CREATED,
             summary="[Drone] Publish a detection from the on-board model")
def create_detection(payload: DetectionCreate, drone: UavDroneModel = Depends(get_current_drone), db: Session = Depends(get_db)):
    """The drone runs the ML model itself (edge inference) and only sends the result here."""
    with repository_errors():
        return uav_repo.create_detection(db, drone, payload.model_dump())


# ── Drones (people) ──

@router.post("/drones", response_model=DroneWithKey, status_code=status.HTTP_201_CREATED, summary="Register a drone")
def register_drone(payload: DroneCreate, user: AuthUser = Depends(coordinator), db: Session = Depends(get_db)):
    """Returns the drone's API key ONCE. Lost keys can be replaced with rotate-key."""
    with repository_errors():
        drone, api_key = uav_repo.register_drone(db, payload.model_dump(), actor_id=user.id)
    return {**drone, "apiKey": api_key}


@router.get("/drones", response_model=List[DroneOut], summary="List drones")
def list_drones(user: AuthUser = Depends(coordinator_or_rescuer), db: Session = Depends(get_db)):
    """Coordinators get every drone; volunteers get the drones assigned to them."""
    return uav_repo.list_drones(db, user.model_dump())


@router.patch("/drones/{drone_id}", response_model=DroneOut, summary="Edit drone name, district or stream")
def update_drone(drone_id: str, payload: DroneUpdate, user: AuthUser = Depends(coordinator), db: Session = Depends(get_db)):
    drone = uav_repo.update_drone(db, drone_id, payload.model_dump(exclude_unset=True), actor_id=user.id)
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found.")
    return drone


@router.post("/drones/{drone_id}/rotate-key", response_model=DroneWithKey, summary="Issue a new drone API key")
def rotate_drone_key(drone_id: str, user: AuthUser = Depends(coordinator), db: Session = Depends(get_db)):
    """The old key stops working immediately."""
    result = uav_repo.rotate_drone_key(db, drone_id, actor_id=user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Drone not found.")
    drone, api_key = result
    return {**drone, "apiKey": api_key}


# ── Detections (people) ──

@router.get("/detections", response_model=List[DetectionOut], summary="List detections (newest first)")
def list_detections(
    since: Optional[datetime] = Query(None, description="Only detections received after this time (for polling)"),
    status_filter: Optional[str] = Query(None, alias="status", description="New, Acknowledged, Rescue Requested, Dismissed"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: AuthUser = Depends(coordinator_or_rescuer),
    db: Session = Depends(get_db),
):
    return uav_repo.list_detections(db, user.model_dump(), since=since, status=status_filter, limit=limit, offset=offset)


@router.post("/detections/{detection_id}/acknowledge", response_model=DetectionOut, summary="Acknowledge a detection")
def acknowledge_detection(detection_id: str, user: AuthUser = Depends(coordinator_or_rescuer), db: Session = Depends(get_db)):
    """'I have seen this and am responding.' Volunteers can only acknowledge their drones' detections."""
    with repository_errors():
        return uav_repo.acknowledge_detection(db, user.model_dump(), detection_id)


@router.post("/detections/{detection_id}/dismiss", response_model=DetectionOut, summary="Dismiss a false alarm")
def dismiss_detection(detection_id: str, user: AuthUser = Depends(coordinator), db: Session = Depends(get_db)):
    with repository_errors():
        return uav_repo.dismiss_detection(db, user.model_dump(), detection_id)


@router.post("/detections/{detection_id}/rescue-request", response_model=RescueRequestOut,
             summary="Create a Shohay rescue request from a detection")
def create_rescue_request(detection_id: str, user: AuthUser = Depends(coordinator), db: Session = Depends(get_db)):
    """Adds a Verified rescue request at the detection's GPS location, ready to dispatch to volunteers."""
    with repository_errors():
        return uav_repo.create_rescue_request(db, user.model_dump(), detection_id)


# ── Rescuer assignments & audit log (coordinators) ──

@router.get("/assignments", response_model=List[RescuerAssignmentOut], summary="Which volunteers follow which drones",
            dependencies=[Depends(coordinator)])
def list_rescuer_assignments(db: Session = Depends(get_db)):
    return uav_repo.list_rescuer_assignments(db)


@router.post("/assignments", response_model=RescuerAssignmentOut, status_code=status.HTTP_201_CREATED,
             summary="Assign a field volunteer to a drone")
def assign_rescuer(payload: RescuerAssignmentCreate, user: AuthUser = Depends(coordinator), db: Session = Depends(get_db)):
    with repository_errors():
        return uav_repo.assign_rescuer(db, payload.user_id, payload.drone_id, actor_id=user.id)


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove a volunteer from a drone")
def unassign_rescuer(assignment_id: str, user: AuthUser = Depends(coordinator), db: Session = Depends(get_db)):
    if not uav_repo.unassign_rescuer(db, assignment_id, actor_id=user.id):
        raise HTTPException(status_code=404, detail="Assignment not found.")


@router.get("/logs", response_model=List[UavLogOut], summary="UAV audit log", dependencies=[Depends(coordinator)])
def list_logs(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    return uav_repo.list_logs(db, limit=limit, offset=offset)
