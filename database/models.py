"""
SQLAlchemy ORM models mirroring Supabase PostgreSQL tables and Pydantic schemas.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, Text, DateTime, JSON
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
    __tablename__ = "volunteer_profiles"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    join_date: Mapped[str] = mapped_column(String(50), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    hours_logged: Mapped[int] = mapped_column(Integer, default=0)
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    current_assignment: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
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
    status: Mapped[str] = mapped_column(String(20), index=True, default="Available")
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
    role: Mapped[str] = mapped_column(String(20), index=True, default="public")  # "public" or "fieldworker"
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

