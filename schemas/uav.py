"""Request/response models for the UAV (drone) module."""
from datetime import datetime
from typing import List, Literal, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

STREAM_SCHEMES = {"http", "https", "rtsp", "rtmp", "ws", "wss"}


def _check_url(value: Optional[str], schemes: set) -> Optional[str]:
    if value is None or value == "":
        return None
    parsed = urlparse(value)
    if parsed.scheme not in schemes or not parsed.netloc:
        raise ValueError(f"must be a URL starting with one of: {', '.join(sorted(schemes))}")
    return value


# ── Coordinator input ──

class DroneCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    registration_id: str = Field(..., min_length=3, max_length=100, pattern=r"^[A-Za-z0-9_-]+$",
                                 description="Printed on the drone, e.g. SYL-UAV-07")
    district: Optional[str] = Field(None, max_length=100)
    stream_url: Optional[str] = Field(None, max_length=500)

    @field_validator("stream_url")
    @classmethod
    def valid_stream(cls, v):
        return _check_url(v, STREAM_SCHEMES)


class DroneUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    district: Optional[str] = Field(None, max_length=100)
    stream_url: Optional[str] = Field(None, max_length=500)

    @field_validator("stream_url")
    @classmethod
    def valid_stream(cls, v):
        return _check_url(v, STREAM_SCHEMES)


class RescuerAssignmentCreate(BaseModel):
    user_id: str
    drone_id: str


# ── Drone (device) input — same field names as the ResQTech edge client ──

class DroneHeartbeat(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    battery_pct: Optional[float] = Field(None, ge=0, le=100)


class DroneStreamUpdate(BaseModel):
    stream_url: str = Field(..., max_length=500)

    @field_validator("stream_url")
    @classmethod
    def valid_stream(cls, v):
        return _check_url(v, STREAM_SCHEMES)


class BoundingBox(BaseModel):
    """Normalised box (0-1) around the detected person or animal in the video frame."""
    x: float = Field(..., ge=0, le=1)
    y: float = Field(..., ge=0, le=1)
    w: float = Field(..., ge=0, le=1)
    h: float = Field(..., ge=0, le=1)


class DetectionCreate(BaseModel):
    timestamp: datetime
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    detection_type: Literal["human", "animal"]
    confidence: float = Field(..., ge=0, le=1)
    bounding_box: Optional[BoundingBox] = None
    image_url: Optional[str] = Field(None, max_length=500, description="Snapshot of the frame as evidence")

    @field_validator("image_url")
    @classmethod
    def valid_image(cls, v):
        return _check_url(v, {"http", "https"})


# ── Responses ──

class DroneOut(BaseModel):
    id: str
    name: str
    registrationId: str
    district: Optional[str] = None
    streamUrl: Optional[str] = None
    lastHeartbeat: Optional[str] = None
    isOnline: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    batteryPct: Optional[float] = None
    createdAt: Optional[str] = None


class DroneWithKey(DroneOut):
    apiKey: str = Field(..., description="Shown only once. Store it on the drone.")


class DetectionOut(BaseModel):
    id: str
    droneId: str
    droneName: str
    detectedAt: Optional[str] = None
    latitude: float
    longitude: float
    detectionType: str
    confidence: float
    boundingBox: Optional[dict] = None
    imageUrl: Optional[str] = None
    status: str
    acknowledgedBy: Optional[str] = None
    acknowledgedAt: Optional[str] = None
    requestId: Optional[str] = None
    createdAt: Optional[str] = None


class RescueRequestOut(BaseModel):
    detection: DetectionOut
    request: dict


class RescuerAssignmentOut(BaseModel):
    id: str
    userId: str
    rescuerName: str
    droneId: str
    droneName: str
    createdAt: Optional[str] = None


class UavLogOut(BaseModel):
    id: str
    eventType: str
    message: str
    actorId: Optional[str] = None
    droneId: Optional[str] = None
    detectionId: Optional[str] = None
    createdAt: Optional[str] = None


DetectionList = List[DetectionOut]
