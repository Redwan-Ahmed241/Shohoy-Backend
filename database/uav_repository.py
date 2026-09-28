"""
UAV (drone) data access — ported from the ResQTech FYDP backend and joined to Shohay.

Flow: a drone sends heartbeats and detections -> coordinators watch them in the UAV
monitor -> a real person is turned into a normal Shohay rescue request -> the request
is dispatched to field volunteers like any citizen request.
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import (
    UavDroneModel, UavDetectionModel, UavRescuerAssignmentModel, UavLogModel, UserModel,
)
from .repository import RepositoryError, iso, new_id, repo

# A drone is "online" if its last heartbeat is newer than this (no background job needed).
ONLINE_WINDOW = timedelta(minutes=2)
# Per-drone limits so a faulty or hijacked drone cannot flood the system.
HEARTBEAT_MIN_INTERVAL = timedelta(seconds=2)
DETECTIONS_PER_MINUTE = 30


def hash_api_key(api_key: str) -> str:
    # Keys are 32 random bytes, so a plain SHA-256 is enough (no password-style hashing needed).
    return hashlib.sha256(api_key.encode()).hexdigest()


def _utc_naive(dt: datetime) -> datetime:
    """Stores every timestamp as naive UTC, like the rest of the database."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def drone_to_dict(d: UavDroneModel, now: Optional[datetime] = None) -> Dict[str, Any]:
    now = now or datetime.utcnow()
    return {
        "id": d.id,
        "name": d.name,
        "registrationId": d.registration_id,
        "district": d.district,
        "streamUrl": d.stream_url,
        "lastHeartbeat": iso(d.last_heartbeat),
        "isOnline": bool(d.last_heartbeat and now - d.last_heartbeat < ONLINE_WINDOW),
        "latitude": d.latitude,
        "longitude": d.longitude,
        "batteryPct": d.battery_pct,
        "createdAt": iso(d.created_at),
    }


def detection_to_dict(det: UavDetectionModel, drone_name: str = "") -> Dict[str, Any]:
    return {
        "id": det.id,
        "droneId": det.drone_id,
        "droneName": drone_name,
        "detectedAt": iso(det.detected_at),
        "latitude": det.latitude,
        "longitude": det.longitude,
        "detectionType": det.detection_type,
        "confidence": det.confidence,
        "boundingBox": det.bounding_box,
        "imageUrl": det.image_url,
        "status": det.status,
        "acknowledgedBy": det.acknowledged_by,
        "acknowledgedAt": iso(det.acknowledged_at),
        "requestId": det.request_id,
        "createdAt": iso(det.created_at),
    }


def log_to_dict(entry: UavLogModel) -> Dict[str, Any]:
    return {
        "id": entry.id,
        "eventType": entry.event_type,
        "message": entry.message,
        "actorId": entry.actor_id,
        "droneId": entry.drone_id,
        "detectionId": entry.detection_id,
        "createdAt": iso(entry.created_at),
    }


class UavRepository:
    # ── Audit log ──
    def _log(self, db: Session, event_type: str, message: str, actor_id: Optional[str] = None,
             drone_id: Optional[str] = None, detection_id: Optional[str] = None) -> None:
        db.add(UavLogModel(
            id=new_id("log"), event_type=event_type, message=message,
            actor_id=actor_id, drone_id=drone_id, detection_id=detection_id,
        ))

    def list_logs(self, db: Session, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        rows = db.query(UavLogModel).order_by(UavLogModel.created_at.desc()).offset(offset).limit(limit).all()
        return [log_to_dict(r) for r in rows]

    # ── Access scoping ──
    def _assigned_drone_ids(self, db: Session, user_id: str) -> List[str]:
        return [row[0] for row in db.query(UavRescuerAssignmentModel.drone_id)
                .filter(UavRescuerAssignmentModel.user_id == user_id).all()]

    def _visible_drone_ids(self, db: Session, user: Dict[str, Any]) -> Optional[List[str]]:
        """None means 'all drones' (coordinators); volunteers only see drones assigned to them."""
        return None if user["role"] == "admin" else self._assigned_drone_ids(db, user["id"])

    # ── Drones ──
    def register_drone(self, db: Session, data: Dict[str, Any], actor_id: str) -> Tuple[Dict[str, Any], str]:
        api_key = secrets.token_urlsafe(32)
        drone = UavDroneModel(
            id=new_id("drone"),
            name=data["name"],
            registration_id=data["registration_id"],
            api_key_hash=hash_api_key(api_key),
            district=data.get("district"),
            stream_url=data.get("stream_url"),
        )
        db.add(drone)
        self._log(db, "drone_registered", f"Drone {drone.name} ({drone.registration_id}) registered",
                  actor_id=actor_id, drone_id=drone.id)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise RepositoryError(f"A drone with registration ID '{data['registration_id']}' already exists.")
        db.refresh(drone)
        return drone_to_dict(drone), api_key

    def rotate_drone_key(self, db: Session, drone_id: str, actor_id: str) -> Optional[Tuple[Dict[str, Any], str]]:
        drone = db.get(UavDroneModel, drone_id)
        if not drone:
            return None
        api_key = secrets.token_urlsafe(32)
        drone.api_key_hash = hash_api_key(api_key)
        self._log(db, "drone_key_rotated", f"API key rotated for {drone.name}", actor_id=actor_id, drone_id=drone.id)
        db.commit()
        db.refresh(drone)
        return drone_to_dict(drone), api_key

    def update_drone(self, db: Session, drone_id: str, fields: Dict[str, Any], actor_id: str) -> Optional[Dict[str, Any]]:
        drone = db.get(UavDroneModel, drone_id)
        if not drone:
            return None
        for key in ("name", "district", "stream_url"):
            if key in fields:
                setattr(drone, key, fields[key])
        self._log(db, "drone_updated", f"Drone {drone.name} updated by coordinator", actor_id=actor_id, drone_id=drone.id)
        db.commit()
        db.refresh(drone)
        return drone_to_dict(drone)

    def list_drones(self, db: Session, user: Dict[str, Any]) -> List[Dict[str, Any]]:
        query = db.query(UavDroneModel)
        visible = self._visible_drone_ids(db, user)
        if visible is not None:
            query = query.filter(UavDroneModel.id.in_(visible))
        now = datetime.utcnow()
        return [drone_to_dict(d, now) for d in query.order_by(UavDroneModel.name).all()]

    def authenticate_drone(self, db: Session, registration_id: str, api_key: str) -> Optional[UavDroneModel]:
        drone = db.query(UavDroneModel).filter(UavDroneModel.registration_id == registration_id).first()
        if drone is None or not hmac.compare_digest(drone.api_key_hash, hash_api_key(api_key)):
            return None
        return drone

    def record_heartbeat(self, db: Session, drone: UavDroneModel, data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.utcnow()
        if drone.last_heartbeat and now - drone.last_heartbeat < HEARTBEAT_MIN_INTERVAL:
            raise RepositoryError("Heartbeat sent too often; wait 2 seconds between heartbeats.", status_code=429)
        was_offline = not drone.last_heartbeat or now - drone.last_heartbeat >= ONLINE_WINDOW
        drone.last_heartbeat = now
        for key in ("latitude", "longitude", "battery_pct"):
            if data.get(key) is not None:
                setattr(drone, key, data[key])
        if was_offline:
            # Log only the offline -> online transition, not every heartbeat.
            self._log(db, "drone_online", f"{drone.name} came online", drone_id=drone.id)
        db.commit()
        db.refresh(drone)
        return drone_to_dict(drone, now)

    def update_stream(self, db: Session, drone: UavDroneModel, stream_url: str) -> Dict[str, Any]:
        drone.stream_url = stream_url
        self._log(db, "stream_updated", f"{drone.name} updated its video stream", drone_id=drone.id)
        db.commit()
        db.refresh(drone)
        return drone_to_dict(drone)

    # ── Detections ──
    def create_detection(self, db: Session, drone: UavDroneModel, data: Dict[str, Any]) -> Dict[str, Any]:
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        recent = db.query(UavDetectionModel).filter(
            UavDetectionModel.drone_id == drone.id, UavDetectionModel.created_at >= one_minute_ago
        ).count()
        if recent >= DETECTIONS_PER_MINUTE:
            raise RepositoryError(f"Rate limit: at most {DETECTIONS_PER_MINUTE} detections per minute per drone.", status_code=429)

        det = UavDetectionModel(
            id=new_id("det"),
            drone_id=drone.id,
            detected_at=_utc_naive(data["timestamp"]),
            latitude=data["latitude"],
            longitude=data["longitude"],
            detection_type=data["detection_type"],
            confidence=data["confidence"],
            bounding_box=data.get("bounding_box"),
            image_url=data.get("image_url"),
            status="New",
        )
        db.add(det)
        self._log(db, "detection",
                  f"{drone.name} detected a {det.detection_type} ({round(det.confidence * 100)}% confidence)",
                  drone_id=drone.id, detection_id=det.id)
        db.commit()
        db.refresh(det)
        return detection_to_dict(det, drone.name)

    def list_detections(self, db: Session, user: Dict[str, Any], since: Optional[datetime] = None,
                        status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        query = db.query(UavDetectionModel, UavDroneModel.name).join(
            UavDroneModel, UavDroneModel.id == UavDetectionModel.drone_id
        )
        visible = self._visible_drone_ids(db, user)
        if visible is not None:
            query = query.filter(UavDetectionModel.drone_id.in_(visible))
        if since:
            query = query.filter(UavDetectionModel.created_at > _utc_naive(since))
        if status and status != "All":
            query = query.filter(UavDetectionModel.status == status)
        rows = query.order_by(UavDetectionModel.created_at.desc()).offset(offset).limit(limit).all()
        return [detection_to_dict(det, name) for det, name in rows]

    def _detection_for(self, db: Session, user: Dict[str, Any], detection_id: str) -> UavDetectionModel:
        det = db.get(UavDetectionModel, detection_id)
        if not det:
            raise RepositoryError("Detection not found.", status_code=404)
        visible = self._visible_drone_ids(db, user)
        if visible is not None and det.drone_id not in visible:
            raise RepositoryError("This detection belongs to a drone you are not assigned to.", status_code=403)
        return det

    def acknowledge_detection(self, db: Session, user: Dict[str, Any], detection_id: str) -> Dict[str, Any]:
        det = self._detection_for(db, user, detection_id)
        if det.status == "New":
            det.status = "Acknowledged"
            det.acknowledged_by = user["id"]
            det.acknowledged_at = datetime.utcnow()
            self._log(db, "detection_acknowledged", f"Detection acknowledged by {user.get('first_name', 'user')}",
                      actor_id=user["id"], drone_id=det.drone_id, detection_id=det.id)
            db.commit()
            db.refresh(det)
        return detection_to_dict(det, db.get(UavDroneModel, det.drone_id).name)

    def dismiss_detection(self, db: Session, user: Dict[str, Any], detection_id: str) -> Dict[str, Any]:
        det = self._detection_for(db, user, detection_id)
        if det.status == "Rescue Requested":
            raise RepositoryError("A rescue request already exists for this detection.")
        det.status = "Dismissed"
        self._log(db, "detection_dismissed", "Detection dismissed as a false alarm",
                  actor_id=user["id"], drone_id=det.drone_id, detection_id=det.id)
        db.commit()
        db.refresh(det)
        return detection_to_dict(det, db.get(UavDroneModel, det.drone_id).name)

    def create_rescue_request(self, db: Session, user: Dict[str, Any], detection_id: str) -> Dict[str, Any]:
        """Turns a detection into a normal Shohay rescue request (status Verified)."""
        det = self._detection_for(db, user, detection_id)
        if det.request_id:
            raise RepositoryError("A rescue request already exists for this detection.")
        drone = db.get(UavDroneModel, det.drone_id)
        request = repo.create_request(db, {
            "types": ["rescue"],
            "householdSize": 1,
            "vulnerableCount": {"children": 0, "elderly": 0, "pregnant": 0, "disabled": 0},
            "location": {
                "district": drone.district or "Unknown",
                "upazila": "",
                "union": "",
                "address": f"GPS {det.latitude:.5f}, {det.longitude:.5f}",
                "landmark": f"Spotted by drone {drone.name}",
                "gpsCoords": f"{det.latitude:.6f},{det.longitude:.6f}",
            },
            "contact": {"name": "UAV detection (no contact)", "phone": "N/A", "isAnonymous": False},
            "notes": (f"Created from UAV detection {det.id}: {det.detection_type} "
                      f"({round(det.confidence * 100)}% confidence) by {drone.name}."),
        })
        request = repo.update_request_status(db, request["id"], "Verified")

        det.status = "Rescue Requested"
        det.request_id = request["id"]
        if not det.acknowledged_at:
            det.acknowledged_by = user["id"]
            det.acknowledged_at = datetime.utcnow()
        self._log(db, "rescue_request_created", f"Rescue request {request['trackingId']} created from detection",
                  actor_id=user["id"], drone_id=det.drone_id, detection_id=det.id)
        db.commit()
        db.refresh(det)
        return {"detection": detection_to_dict(det, drone.name), "request": request}

    # ── Rescuer <-> drone assignments ──
    def list_rescuer_assignments(self, db: Session) -> List[Dict[str, Any]]:
        rows = (
            db.query(UavRescuerAssignmentModel, UavDroneModel.name, UserModel.first_name, UserModel.last_name)
            .join(UavDroneModel, UavDroneModel.id == UavRescuerAssignmentModel.drone_id)
            .outerjoin(UserModel, UserModel.id == UavRescuerAssignmentModel.user_id)
            .order_by(UavRescuerAssignmentModel.created_at.desc())
            .all()
        )
        return [{
            "id": a.id,
            "userId": a.user_id,
            "rescuerName": f"{first or ''} {last or ''}".strip() or a.user_id,
            "droneId": a.drone_id,
            "droneName": drone_name,
            "createdAt": iso(a.created_at),
        } for a, drone_name, first, last in rows]

    def assign_rescuer(self, db: Session, user_id: str, drone_id: str, actor_id: str) -> Dict[str, Any]:
        rescuer = db.get(UserModel, user_id)
        if not rescuer:
            raise RepositoryError("User not found.", status_code=404)
        if rescuer.role != "fieldworker":
            raise RepositoryError("Only field volunteers can be assigned to a drone.", status_code=400)
        drone = db.get(UavDroneModel, drone_id)
        if not drone:
            raise RepositoryError("Drone not found.", status_code=404)

        db.add(UavRescuerAssignmentModel(id=new_id("uavasg"), user_id=user_id, drone_id=drone_id, assigned_by=actor_id))
        self._log(db, "rescuer_assigned", f"{rescuer.first_name} {rescuer.last_name} assigned to {drone.name}",
                  actor_id=actor_id, drone_id=drone_id)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise RepositoryError("This volunteer is already assigned to that drone.")
        return next(a for a in self.list_rescuer_assignments(db) if a["userId"] == user_id and a["droneId"] == drone_id)

    def unassign_rescuer(self, db: Session, assignment_id: str, actor_id: str) -> bool:
        a = db.get(UavRescuerAssignmentModel, assignment_id)
        if not a:
            return False
        self._log(db, "rescuer_unassigned", f"Rescuer {a.user_id} removed from drone", actor_id=actor_id, drone_id=a.drone_id)
        db.delete(a)
        db.commit()
        return True


uav_repo = UavRepository()
