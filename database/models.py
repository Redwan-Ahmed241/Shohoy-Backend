"""
SQLAlchemy ORM models mirroring Supabase PostgreSQL tables and Pydantic schemas.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, Text, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .connection import Base


class AlertModel(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    severity: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    affected_areas: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    issued_at: Mapped[str] = mapped_column(String(50), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(50), default="Unverified")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ShelterModel(Base):
    __tablename__ = "shelters"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    upazila: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    occupancy: Mapped[int] = mapped_column(Integer, default=0)
    capacity: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), index=True, default="Open")
    route_status: Mapped[str] = mapped_column(String(20), default="Route OK")
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    amenities: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CampaignModel(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    organization: Mapped[str] = mapped_column(String(255), nullable=False)
    district: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    coverage_areas: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    target_amount: Mapped[float] = mapped_column(Float, default=0.0)
    raised_amount: Mapped[float] = mapped_column(Float, default=0.0)
    households_target: Mapped[int] = mapped_column(Integer, default=0)
    households_reached: Mapped[int] = mapped_column(Integer, default=0)
    verification_status: Mapped[str] = mapped_column(String(50), default="Unverified")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DonationModel(Base):
    __tablename__ = "donations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(50), ForeignKey("campaigns.id"), index=True, nullable=False)
    tran_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="BDT")
    donor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    donor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    donor_phone: Mapped[str] = mapped_column(String(50), nullable=False)
    return_origin: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="Pending", index=True)  # Pending, Success, Failed, Cancelled
    val_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_tran_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    card_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ContactModel(Base):
    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    availability: Mapped[str] = mapped_column(String(50), nullable=False)
    is_toll_free: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_verified: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AssistanceRequestModel(Base):
    __tablename__ = "assistance_requests"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tracking_id: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    types: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    household_size: Mapped[int] = mapped_column(Integer, nullable=False)
    vulnerable_count: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    location: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    contact: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), index=True, default="Pending")
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)


class VolunteerProfileModel(Base):
    """One row per field volunteer. The id is the same as users.id."""
    __tablename__ = "volunteer_profiles"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    join_date: Mapped[str] = mapped_column(String(50), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    hours_logged: Mapped[float] = mapped_column(Float, default=0.0)
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    current_assignment: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # "Off Duty" | "On Duty" | "Paused"; hours are added from checked_in_at when duty stops
    duty_status: Mapped[str] = mapped_column(String(20), default="Off Duty")
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    declined_assignment_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class VolunteerAssignmentModel(Base):
    __tablename__ = "volunteer_assignments"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    district: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    duration_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    team_size: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    # "Available" -> "In Progress" (accepted) -> "Completed"; "Cancelled" by a coordinator
    status: Mapped[str] = mapped_column(String(20), index=True, default="Available")
    assigned_volunteer_id: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    # Citizen request this task was dispatched for (if any)
    request_id: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WarehouseItemModel(Base):
    __tablename__ = "warehouse_items"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    sku: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    available_count: Mapped[int] = mapped_column(Integer, default=0)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    reserved_count: Mapped[int] = mapped_column(Integer, default=0)
    min_stock_threshold: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), index=True, default="OK")
    expiry_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    warehouse_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_count_date: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    role: Mapped[str] = mapped_column(String(20), index=True, default="public")  # "public", "fieldworker" or "admin"
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    avatar: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    equipment: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    
    # Fieldworker-specific personal verification fields
    nid_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    dob: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    experience_certificate: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="Pending")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WarehouseMovementModel(Base):
    """Stock received into or dispatched out of a warehouse item."""
    __tablename__ = "warehouse_movements"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    item_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    movement_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "INBOUND" | "DISPATCH"
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    from_to: Mapped[str] = mapped_column(String(255), nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actor_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)


# ── UAV (drone) module, ported from the ResQTech FYDP backend ──

class UavDroneModel(Base):
    __tablename__ = "uav_drones"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    registration_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    # SHA-256 of the drone's API key; the key itself is shown only once
    api_key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    stream_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    battery_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UavDetectionModel(Base):
    """A person or animal the drone's on-board model detected."""
    __tablename__ = "uav_detections"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    drone_id: Mapped[str] = mapped_column(String(50), ForeignKey("uav_drones.id", ondelete="CASCADE"), index=True, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    detection_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "human" | "animal"
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    bounding_box: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # "New" -> "Acknowledged" -> "Rescue Requested"; or "Dismissed" (false alarm)
    status: Mapped[str] = mapped_column(String(30), index=True, default="New")
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)


class UavRescuerAssignmentModel(Base):
    """Which field volunteers receive a drone's detections."""
    __tablename__ = "uav_rescuer_assignments"
    __table_args__ = (UniqueConstraint("user_id", "drone_id", name="uq_uav_rescuer_drone"),)

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    drone_id: Mapped[str] = mapped_column(String(50), ForeignKey("uav_drones.id", ondelete="CASCADE"), index=True, nullable=False)
    assigned_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UavLogModel(Base):
    """Audit trail for drone, detection and coordinator actions."""
    __tablename__ = "uav_logs"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    drone_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    detection_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)

