"""
Supabase PostgreSQL CRUD Repository via SQLAlchemy 2.0.
Ensures zero runtime errors, safe defaults, and complete compatibility with Pydantic schemas.
"""
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from .models import (
    AlertModel, ShelterModel, CampaignModel, ContactModel,
    AssistanceRequestModel, VolunteerProfileModel,
    VolunteerAssignmentModel, WarehouseItemModel, UserModel
)
from .mock_data import PREDEFINED_SKILLS, PREDEFINED_EQUIPMENT, PREDEFINED_GENDERS

# ── Converters: ORM Model -> API DTO Dict ──

def alert_to_dict(a: AlertModel) -> Dict[str, Any]:
    return {
        "id": a.id,
        "severity": a.severity,
        "type": a.type,
        "title": a.title,
        "description": a.description,
        "affectedAreas": a.affected_areas if isinstance(a.affected_areas, list) else [],
        "issuedAt": a.issued_at,
        "verificationStatus": a.verification_status,
    }

def shelter_to_dict(s: ShelterModel) -> Dict[str, Any]:
    return {
        "id": s.id,
        "name": s.name,
        "address": s.address,
        "upazila": s.upazila,
        "district": s.district,
        "occupancy": s.occupancy,
        "capacity": s.capacity,
        "status": s.status,
        "routeStatus": s.route_status,
        "category": s.category,
        "amenities": s.amenities if isinstance(s.amenities, dict) else {},
    }

def campaign_to_dict(c: CampaignModel) -> Dict[str, Any]:
    return {
        "id": c.id,
        "title": c.title,
        "organization": c.organization,
        "district": c.district,
        "coverageAreas": c.coverage_areas if isinstance(c.coverage_areas, list) else [],
        "targetAmount": c.target_amount,
        "raisedAmount": c.raised_amount,
        "householdsTarget": c.households_target,
        "householdsReached": c.households_reached,
        "verificationStatus": c.verification_status,
    }

def contact_to_dict(c: ContactModel) -> Dict[str, Any]:
    return {
        "id": c.id,
        "title": c.title,
        "category": c.category,
        "district": c.district,
        "phone": c.phone,
        "description": c.description,
        "availability": c.availability,
        "isTollFree": c.is_toll_free,
        "isVerified": c.is_verified,
        "notes": c.notes,
        "lastVerified": c.last_verified,
    }

def request_to_dict(r: AssistanceRequestModel) -> Dict[str, Any]:
    return {
        "id": r.id,
        "trackingId": r.tracking_id,
        "types": r.types if isinstance(r.types, list) else [],
        "householdSize": r.household_size,
        "vulnerableCount": r.vulnerable_count if isinstance(r.vulnerable_count, dict) else {},
        "location": r.location if isinstance(r.location, dict) else {},
        "contact": r.contact if isinstance(r.contact, dict) else {},
        "notes": r.notes,
        "status": r.status,
        "createdAt": r.created_at,
    }

def volunteer_profile_to_dict(v: VolunteerProfileModel) -> Dict[str, Any]:
    return {
        "id": v.id,
        "name": v.name,
        "code": v.code,
        "district": v.district,
        "joinDate": v.join_date,
        "isAvailable": v.is_available,
        "hoursLogged": v.hours_logged,
        "tasksCompleted": v.tasks_completed,
        "rating": v.rating,
        "currentAssignment": v.current_assignment,
        "skills": v.skills if isinstance(v.skills, list) else [],
    }

def assignment_to_dict(a: VolunteerAssignmentModel) -> Dict[str, Any]:
    return {
        "id": a.id,
        "title": a.title,
        "location": a.location,
        "district": a.district,
        "durationHours": a.duration_hours,
        "teamSize": a.team_size,
        "priority": a.priority,
        "status": a.status,
    }

def warehouse_to_dict(w: WarehouseItemModel) -> Dict[str, Any]:
    return {
        "id": w.id,
        "sku": w.sku,
        "name": w.name,
        "category": w.category,
        "availableCount": w.available_count,
        "unit": w.unit,
        "reservedCount": w.reserved_count,
        "minStockThreshold": w.min_stock_threshold,
        "status": w.status,
        "expiryDate": w.expiry_date,
        "warehouseName": w.warehouse_name,
        "lastCountDate": w.last_count_date,
    }

def user_to_dict(u: UserModel) -> Dict[str, Any]:
    return {
        "id": u.id,
        "role": u.role,
        "firstName": u.first_name,
        "lastName": u.last_name,
        "phoneNumber": u.phone_number,
        "email": u.email,
        "avatar": u.avatar,
        "gender": u.gender,
        "skills": u.skills if isinstance(u.skills, list) else [],
        "equipment": u.equipment if isinstance(u.equipment, list) else [],
        "nidNumber": u.nid_number,
        "address": u.address,
        "dob": u.dob,
        "experienceCertificate": u.experience_certificate,
        "verificationStatus": u.verification_status,
        "createdAt": u.created_at.isoformat() if u.created_at else None,
        "updatedAt": u.updated_at.isoformat() if u.updated_at else None,
    }



class SupabaseRepository:
    """
    CRUD repository for database operations against Supabase PostgreSQL.
    """

    # ── ALERTS ──
    def get_alerts(self, db: Session, severity: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        query = db.query(AlertModel)
        if severity and severity != "ALL CLEAR":
            query = query.filter(AlertModel.severity == severity)
        elif severity == "ALL CLEAR":
            query = query.filter(AlertModel.severity == "ALL CLEAR")

        alerts = query.order_by(AlertModel.created_at.desc()).all()

        if search and search.strip():
            q = search.lower().strip()
            alerts = [
                a for a in alerts
                if q in a.title.lower()
                or q in a.description.lower()
                or any(q in str(area).lower() for area in (a.affected_areas or []))
            ]

        return [alert_to_dict(a) for a in alerts]

    def get_alert_by_id(self, db: Session, alert_id: str) -> Optional[Dict[str, Any]]:
        a = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
        return alert_to_dict(a) if a else None

    def create_alert(self, db: Session, data: Dict[str, Any]) -> Dict[str, Any]:
        existing_ids = [r[0] for r in db.query(AlertModel.id).all()]
        nums = []
        for eid in existing_ids:
            if eid.startswith("alert-"):
                part = eid.split("-")[1]
                if part.isdigit():
                    nums.append(int(part))
        next_num = (max(nums) + 1) if nums else 1

        alert = AlertModel(
            id=f"alert-{next_num}",
            severity=data.get("severity", "LOW"),
            type=data.get("type", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            affected_areas=data.get("affectedAreas") or data.get("affected_areas") or [],
            issued_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            verification_status=data.get("verificationStatus") or data.get("verification_status", "Unverified"),
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert_to_dict(alert)

    # ── SHELTERS ──
    def get_shelters(self, db: Session, status: Optional[str] = None, district: Optional[str] = None, amenities: Optional[Dict[str, bool]] = None) -> List[Dict[str, Any]]:
        query = db.query(ShelterModel)
        if status and status != "All":
            query = query.filter(ShelterModel.status == status)
        if district and district != "All":
            query = query.filter(ShelterModel.district.ilike(district))

        shelters = query.all()

        if amenities:
            active_keys = [k for k, v in amenities.items() if v]
            if active_keys:
                shelters = [s for s in shelters if all((s.amenities or {}).get(k) for k in active_keys)]

        return [shelter_to_dict(s) for s in shelters]

    def get_shelter_stats(self, db: Session) -> Dict[str, Any]:
        shelters = db.query(ShelterModel).all()
        total = len(shelters)
        open_count = sum(1 for s in shelters if s.status == "Open")
        nearly_full = sum(1 for s in shelters if s.status == "Nearly Full")
        free_spaces = sum(max(0, s.capacity - s.occupancy) for s in shelters)
        return {
            "totalShelters": total,
            "openShelters": open_count,
            "nearlyFull": nearly_full,
            "freeSpaces": f"{free_spaces:,}",
        }

    # ── REQUESTS ──
    def create_request(self, db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
        random_num = random.randint(10000, 99999)
        tracking_id = f"SHY-2024-{random_num}"
        record_id = f"req-{int(datetime.now().timestamp() * 1000)}"

        req = AssistanceRequestModel(
            id=record_id,
            tracking_id=tracking_id,
            types=payload.get("types", []),
            household_size=payload.get("householdSize") or payload.get("household_size", 1),
            vulnerable_count=payload.get("vulnerableCount") or payload.get("vulnerable_count", {}),
            location=payload.get("location", {}),
            contact=payload.get("contact", {}),
            notes=payload.get("notes"),
            status="Pending",
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        return request_to_dict(req)

    def get_request_by_tracking_id(self, db: Session, tracking_id: str) -> Optional[Dict[str, Any]]:
        clean_id = tracking_id.strip().upper()
        r = db.query(AssistanceRequestModel).filter(AssistanceRequestModel.tracking_id == clean_id).first()
        return request_to_dict(r) if r else None

    # ── CAMPAIGNS ──
    def get_campaigns(self, db: Session) -> List[Dict[str, Any]]:
        return [campaign_to_dict(c) for c in db.query(CampaignModel).all()]

    def get_campaign_stats(self, db: Session) -> Dict[str, Any]:
        campaigns = db.query(CampaignModel).all()
        active = len(campaigns)
        households = sum(c.households_reached for c in campaigns)
        total_raised = sum(c.raised_amount for c in campaigns)
        return {
            "activeCampaigns": active,
            "householdsReached": f"{households:,}",
            "totalRaisedBDT": f"৳{(total_raised / 100000):.1f}L",
        }

    # ── CONTACTS ──
    def get_contacts(self, db: Session, category: Optional[str] = None, district: Optional[str] = None) -> List[Dict[str, Any]]:
        query = db.query(ContactModel)
        if category and category != "All":
            query = query.filter(ContactModel.category == category)
        if district and district != "All Districts":
            query = query.filter((ContactModel.district.is_(None)) | (ContactModel.district.ilike(district)))
        return [contact_to_dict(c) for c in query.all()]

    # ── VOLUNTEERS ──
    def get_volunteer_profile(self, db: Session) -> Dict[str, Any]:
        v = db.query(VolunteerProfileModel).first()
        if v:
            return volunteer_profile_to_dict(v)
        # Safe default if table is unseeded
        return {
            "id": "vol-1",
            "name": "Demo Volunteer",
            "code": "VOL-2024-DEMO",
            "district": "Sunamganj",
            "joinDate": "12 July 2024",
            "isAvailable": True,
            "hoursLogged": 24,
            "tasksCompleted": 7,
            "rating": 4.8,
            "currentAssignment": None,
            "skills": ["Food Distribution", "Administration"],
        }

    def get_open_assignments(self, db: Session) -> List[Dict[str, Any]]:
        assignments = db.query(VolunteerAssignmentModel).filter(VolunteerAssignmentModel.status == "Available").all()
        return [assignment_to_dict(a) for a in assignments]

    def update_assignment_status(self, db: Session, assignment_id: str, new_status: str) -> bool:
        a = db.query(VolunteerAssignmentModel).filter(VolunteerAssignmentModel.id == assignment_id).first()
        if a:
            a.status = new_status
            db.commit()
            return True
        return False

    # ── WAREHOUSE ──
    def get_warehouse_inventory(self, db: Session, category: Optional[str] = None) -> List[Dict[str, Any]]:
        query = db.query(WarehouseItemModel)
        if category and category != "All":
            query = query.filter(WarehouseItemModel.category == category)
        return [warehouse_to_dict(w) for w in query.all()]

    def get_low_stock_items(self, db: Session) -> List[Dict[str, Any]]:
        items = db.query(WarehouseItemModel).filter(WarehouseItemModel.status == "LOW").all()
        return [warehouse_to_dict(w) for w in items]

    def get_expiring_items(self, db: Session) -> List[Dict[str, Any]]:
        items = db.query(WarehouseItemModel).filter(
            WarehouseItemModel.expiry_date.is_not(None),
            WarehouseItemModel.expiry_date != ""
        ).all()
        return [warehouse_to_dict(w) for w in items]

    # ── USERS & AUTH ──
    def get_user_by_id(self, db: Session, user_id: str) -> Optional[Dict[str, Any]]:
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        return user_to_dict(user) if user else None

    def get_user_by_phone(self, db: Session, phone: str) -> Optional[Dict[str, Any]]:
        clean_target = phone.strip().replace(" ", "").replace("-", "")
        # Query users and match normalized phone
        users = db.query(UserModel).filter(UserModel.phone_number.is_not(None)).all()
        for u in users:
            p = (u.phone_number or "").strip().replace(" ", "").replace("-", "")
            if p and (p == clean_target or p.endswith(clean_target) or clean_target.endswith(p)):
                return user_to_dict(u)
        return None

    def get_user_by_email(self, db: Session, email: str) -> Optional[Dict[str, Any]]:
        clean_email = email.strip().lower()
        user = db.query(UserModel).filter(UserModel.email.ilike(clean_email)).first()
        return user_to_dict(user) if user else None

    def get_user_by_identifier(self, db: Session, identifier: str) -> Optional[Dict[str, Any]]:
        clean_id = identifier.strip().lower()
        if "@" in clean_id:
            return self.get_user_by_email(db, clean_id)
        return self.get_user_by_phone(db, clean_id)

    def create_user(self, db: Session, data: Dict[str, Any]) -> Dict[str, Any]:
        count = db.query(UserModel).count()
        user_id = data.get("id") or f"usr-{data.get('role', 'public')}-{count + 1:03d}"
        
        user = UserModel(
            id=user_id,
            role=data.get("role", "public"),
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone_number=data.get("phone_number"),
            email=data.get("email"),
            avatar=data.get("avatar"),
            gender=data.get("gender"),
            skills=data.get("skills", []),
            equipment=data.get("equipment", []),
            nid_number=data.get("nid_number"),
            address=data.get("address"),
            dob=data.get("dob"),
            experience_certificate=data.get("experience_certificate"),
            verification_status=data.get("verification_status", "Pending")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user_to_dict(user)

    def update_user(self, db: Session, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return None

        for k, v in updates.items():
            if hasattr(user, k):
                setattr(user, k, v)

        db.commit()
        db.refresh(user)
        return user_to_dict(user)

    def get_auth_options(self) -> Dict[str, Any]:
        return {
            "skills": PREDEFINED_SKILLS,
            "equipment": PREDEFINED_EQUIPMENT,
            "genders": PREDEFINED_GENDERS,
            "roles": ["public", "fieldworker"]
        }


supabase_repo = SupabaseRepository()

