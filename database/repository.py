"""
Data-access layer: every database read and write in the app goes through `repo`.
Works the same on Supabase PostgreSQL (production) and local SQLite (development).
Functions return plain dicts shaped like the API responses (camelCase keys).
"""
import hashlib
import secrets
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .models import (
    AlertModel, ShelterModel, CampaignModel, ContactModel,
    AssistanceRequestModel, VolunteerProfileModel,
    VolunteerAssignmentModel, WarehouseItemModel, UserModel,
    WarehouseMovementModel, DonationModel
)
from .mock_data import PREDEFINED_SKILLS, PREDEFINED_EQUIPMENT, PREDEFINED_GENDERS

# Tracking IDs are handed to citizens; 6 characters from this alphabet (~1 billion
# combinations) keep them short to read over the phone but impossible to guess.
_TRACKING_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class RepositoryError(Exception):
    """A request that conflicts with the current state (e.g. task already taken)."""
    def __init__(self, message: str, status_code: int = 409):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def iso(dt: Optional[datetime]) -> Optional[str]:
    """UTC datetime -> ISO string with a Z suffix. Full precision, so a dashboard can poll
    with ?since=<last createdAt> without getting the same row back."""
    return dt.isoformat() + "Z" if dt else None

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

def donation_to_dict(d: DonationModel) -> Dict[str, Any]:
    return {
        "tranId": d.tran_id,
        "status": d.status,
        "amount": d.amount,
        "currency": d.currency,
        "campaignId": d.campaign_id,
        "donorName": d.donor_name,
        "createdAt": iso(d.created_at),
        "validatedAt": iso(d.validated_at),
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

def request_to_tracking_dict(r: AssistanceRequestModel) -> Dict[str, Any]:
    """Public view for the citizen tracker: status only, no names, phones or addresses."""
    location = r.location if isinstance(r.location, dict) else {}
    return {
        "trackingId": r.tracking_id,
        "types": r.types if isinstance(r.types, list) else [],
        "status": r.status,
        "district": location.get("district", ""),
        "upazila": location.get("upazila", ""),
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
        "hoursLogged": round(v.hours_logged or 0, 1),
        "tasksCompleted": v.tasks_completed,
        "rating": v.rating,
        "currentAssignment": v.current_assignment,
        "skills": v.skills if isinstance(v.skills, list) else [],
        "dutyStatus": v.duty_status or "Off Duty",
        "checkedInAt": iso(v.checked_in_at),
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
        "requestId": a.request_id,
        "assignedVolunteerId": a.assigned_volunteer_id,
    }

def movement_to_dict(mv: WarehouseMovementModel, item_name: str = "") -> Dict[str, Any]:
    sign = "+" if mv.movement_type == "INBOUND" else "-"
    return {
        "id": mv.id,
        "itemId": mv.item_id,
        "item": item_name,
        "type": mv.movement_type,
        "quantity": mv.quantity,
        "qty": f"{sign}{mv.quantity}",
        "fromTo": mv.from_to,
        "ref": mv.reference or "",
        "notes": mv.notes,
        "date": mv.created_at.strftime("%Y-%m-%d %H:%M") if mv.created_at else "",
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
        "first_name": u.first_name,
        "last_name": u.last_name,
        "firstName": u.first_name,
        "lastName": u.last_name,
        "phone_number": u.phone_number,
        "phoneNumber": u.phone_number,
        "email": u.email,
        "avatar": u.avatar,
        "gender": u.gender,
        "skills": u.skills if isinstance(u.skills, list) else [],
        "equipment": u.equipment if isinstance(u.equipment, list) else [],
        "nid_number": u.nid_number,
        "nidNumber": u.nid_number,
        "address": u.address,
        "dob": u.dob,
        "experience_certificate": u.experience_certificate,
        "experienceCertificate": u.experience_certificate,
        "verification_status": u.verification_status,
        "verificationStatus": u.verification_status,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "updated_at": u.updated_at.isoformat() if u.updated_at else None,
    }




class Repository:
    """CRUD operations for every Shohay table (UAV tables live in uav_repository.py)."""

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

    def create_shelter(self, db: Session, data: Dict[str, Any]) -> Dict[str, Any]:
        default_amenities = {
            "drinkingWater": True, "toilets": True, "womenToilets": True,
            "electricity": True, "generator": False, "food": True, "medicalSupport": False
        }
        shelter = ShelterModel(
            id=new_id("shelter"),
            name=data["name"],
            address=data["address"],
            upazila=data["upazila"],
            district=data["district"],
            capacity=data.get("capacity", 0),
            occupancy=data.get("occupancy", 0),
            category=data.get("category", "Government Building"),
            status=data.get("status", "Open"),
            route_status=data.get("routeStatus", "Route OK"),
            amenities=data.get("amenities") or default_amenities,
        )
        db.add(shelter)
        db.commit()
        db.refresh(shelter)
        return shelter_to_dict(shelter)

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
    def _new_tracking_id(self, db: Session) -> str:
        while True:
            code = "".join(secrets.choice(_TRACKING_ALPHABET) for _ in range(6))
            tracking_id = f"SHY-{datetime.now().year}-{code}"
            if not db.query(AssistanceRequestModel.id).filter(AssistanceRequestModel.tracking_id == tracking_id).first():
                return tracking_id

    def create_request(self, db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
        tracking_id = self._new_tracking_id(db)
        record_id = new_id("req")

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
        if not r:
            return None
        tracking = request_to_tracking_dict(r)
        task = self._latest_task_for_request(db, r.id)
        tracking["taskStatus"] = task.status if task else None
        return tracking

    def _latest_task_for_request(self, db: Session, request_id: str) -> Optional[VolunteerAssignmentModel]:
        return (
            db.query(VolunteerAssignmentModel)
            .filter(VolunteerAssignmentModel.request_id == request_id)
            .order_by(VolunteerAssignmentModel.created_at.desc())
            .first()
        )

    def _find_request(self, db: Session, request_id: str) -> Optional[AssistanceRequestModel]:
        return db.query(AssistanceRequestModel).filter(
            (AssistanceRequestModel.id == request_id) | (AssistanceRequestModel.tracking_id == request_id)
        ).first()

    def _with_task(self, db: Session, records: List[AssistanceRequestModel]) -> List[Dict[str, Any]]:
        """Adds the dispatched volunteer task (and who took it) to each request dict."""
        ids = [r.id for r in records]
        tasks: Dict[str, VolunteerAssignmentModel] = {}
        if ids:
            for a in (
                db.query(VolunteerAssignmentModel)
                .filter(VolunteerAssignmentModel.request_id.in_(ids))
                .order_by(VolunteerAssignmentModel.created_at.asc())
                .all()
            ):
                tasks[a.request_id] = a  # latest task wins
        volunteer_ids = [t.assigned_volunteer_id for t in tasks.values() if t.assigned_volunteer_id]
        names = {
            v.id: v.name
            for v in db.query(VolunteerProfileModel).filter(VolunteerProfileModel.id.in_(volunteer_ids)).all()
        } if volunteer_ids else {}

        result = []
        for r in records:
            d = request_to_dict(r)
            task = tasks.get(r.id)
            d["task"] = {
                "id": task.id,
                "status": task.status,
                "assignedVolunteerName": names.get(task.assigned_volunteer_id),
            } if task else None
            result.append(d)
        return result

    def get_all_requests(self, db: Session, status: Optional[str] = None, district: Optional[str] = None) -> List[Dict[str, Any]]:
        query = db.query(AssistanceRequestModel)
        if status and status != "All":
            query = query.filter(AssistanceRequestModel.status.ilike(status))
        records = query.order_by(AssistanceRequestModel.created_at.desc()).all()
        if district and district != "All":
            d = district.lower()
            records = [r for r in records if str((r.location or {}).get("district", "")).lower() == d]
        return self._with_task(db, records)

    def update_request_status(self, db: Session, request_id: str, new_status: str, notes: Optional[str] = None) -> Optional[Dict[str, Any]]:
        r = self._find_request(db, request_id)
        if not r:
            return None
        r.status = new_status
        if notes:
            r.notes = (r.notes or "") + f" | {notes}"
        db.commit()
        db.refresh(r)
        return self._with_task(db, [r])[0]

    def dispatch_request(self, db: Session, request_id: str, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Creates a volunteer task for a citizen request and marks the request Assigned."""
        r = self._find_request(db, request_id)
        if not r:
            return None
        if r.status == "Resolved":
            raise RepositoryError("This request is already resolved.")
        active = self._latest_task_for_request(db, r.id)
        if active and active.status in ("Available", "In Progress"):
            raise RepositoryError("A volunteer task for this request is already open.")

        self.create_assignment(db, {**task_data, "request_id": r.id}, commit=False)
        r.status = "Assigned"
        db.commit()
        db.refresh(r)
        return self._with_task(db, [r])[0]

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

    # ── DONATIONS (SSLCommerz) ──
    def create_donation(
        self, db: Session, campaign_id: str, amount: float,
        donor_name: str, donor_email: str, donor_phone: str, return_origin: str
    ) -> DonationModel:
        campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
        if not campaign:
            raise RepositoryError("Campaign not found.", status_code=404)
        donation = DonationModel(
            id=new_id("don"),
            campaign_id=campaign_id,
            tran_id=f"SHY{uuid.uuid4().hex[:16].upper()}",
            amount=amount,
            donor_name=donor_name,
            donor_email=donor_email,
            donor_phone=donor_phone,
            return_origin=return_origin,
            status="Pending",
        )
        db.add(donation)
        db.commit()
        db.refresh(donation)
        return donation

    def get_donation_by_tran_id(self, db: Session, tran_id: str) -> Optional[DonationModel]:
        return db.query(DonationModel).filter(DonationModel.tran_id == tran_id).first()

    def finalize_donation(
        self, db: Session, tran_id: str, status: str,
        val_id: Optional[str] = None, bank_tran_id: Optional[str] = None, card_type: Optional[str] = None
    ) -> Optional[DonationModel]:
        """Marks a donation Success/Failed/Cancelled. Crediting the campaign only happens once —
        SSLCommerz calls both the success redirect AND the IPN webhook for the same payment."""
        donation = self.get_donation_by_tran_id(db, tran_id)
        if not donation:
            return None
        if donation.status == "Success":
            return donation
        donation.status = status
        donation.val_id = val_id
        donation.bank_tran_id = bank_tran_id
        donation.card_type = card_type
        donation.validated_at = datetime.utcnow()
        if status == "Success":
            campaign = db.query(CampaignModel).filter(CampaignModel.id == donation.campaign_id).first()
            if campaign:
                campaign.raised_amount = (campaign.raised_amount or 0) + donation.amount
        db.commit()
        db.refresh(donation)
        return donation

    # ── CONTACTS ──
    def get_contacts(self, db: Session, category: Optional[str] = None, district: Optional[str] = None) -> List[Dict[str, Any]]:
        query = db.query(ContactModel)
        if category and category != "All":
            query = query.filter(ContactModel.category == category)
        if district and district != "All Districts":
            query = query.filter((ContactModel.district.is_(None)) | (ContactModel.district.ilike(district)))
        return [contact_to_dict(c) for c in query.all()]

    # ── VOLUNTEERS ──
    def get_or_create_volunteer_profile(self, db: Session, user: Dict[str, Any]) -> VolunteerProfileModel:
        """Every field volunteer has one profile row whose id equals their users.id."""
        v = db.query(VolunteerProfileModel).filter(VolunteerProfileModel.id == user["id"]).first()
        if v:
            return v
        name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or "Volunteer"
        v = VolunteerProfileModel(
            id=user["id"],
            name=name,
            code=f"VOL-{hashlib.sha1(user['id'].encode()).hexdigest()[:8].upper()}",
            district="Not set",
            join_date=datetime.utcnow().strftime("%d %B %Y"),
            is_available=True,
            hours_logged=0.0,
            tasks_completed=0,
            rating=0.0,
            skills=user.get("skills") or [],
            duty_status="Off Duty",
            declined_assignment_ids=[],
        )
        db.add(v)
        try:
            db.commit()
        except IntegrityError:
            # A parallel request created it first
            db.rollback()
            return db.query(VolunteerProfileModel).filter(VolunteerProfileModel.id == user["id"]).one()
        db.refresh(v)
        return v

    def get_volunteer_profile(self, db: Session, user: Dict[str, Any]) -> Dict[str, Any]:
        return volunteer_profile_to_dict(self.get_or_create_volunteer_profile(db, user))

    def update_volunteer_details(self, db: Session, user: Dict[str, Any], district: Optional[str], skills: List[str]) -> Dict[str, Any]:
        v = self.get_or_create_volunteer_profile(db, user)
        v.name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or v.name
        if district:
            v.district = district
        v.skills = skills
        db.commit()
        db.refresh(v)
        return volunteer_profile_to_dict(v)

    def set_volunteer_availability(self, db: Session, user: Dict[str, Any], is_available: bool) -> Dict[str, Any]:
        v = self.get_or_create_volunteer_profile(db, user)
        v.is_available = is_available
        db.commit()
        db.refresh(v)
        return volunteer_profile_to_dict(v)

    def get_open_assignments(self, db: Session, user: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Tasks nobody has accepted yet, minus ones this volunteer declined; own district first."""
        v = self.get_or_create_volunteer_profile(db, user) if user else None
        declined = set(v.declined_assignment_ids or []) if v else set()
        rows = db.query(VolunteerAssignmentModel).filter(
            VolunteerAssignmentModel.status == "Available"
        ).order_by(VolunteerAssignmentModel.created_at.desc()).all()
        rows = [a for a in rows if a.id not in declined]
        if v and v.district:
            rows.sort(key=lambda a: a.district.lower() != v.district.lower())
        return [assignment_to_dict(a) for a in rows]

    def get_all_assignments(self, db: Session, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Coordinator view of every task with the volunteer working on it."""
        query = db.query(VolunteerAssignmentModel)
        if status and status != "All":
            query = query.filter(VolunteerAssignmentModel.status == status)
        rows = query.order_by(VolunteerAssignmentModel.created_at.desc()).all()
        volunteer_ids = [a.assigned_volunteer_id for a in rows if a.assigned_volunteer_id]
        names = {
            v.id: v.name
            for v in db.query(VolunteerProfileModel).filter(VolunteerProfileModel.id.in_(volunteer_ids)).all()
        } if volunteer_ids else {}
        result = []
        for a in rows:
            d = assignment_to_dict(a)
            d["assignedVolunteerName"] = names.get(a.assigned_volunteer_id)
            result.append(d)
        return result

    def _set_request_status(self, db: Session, request_id: Optional[str], new_status: str) -> None:
        if not request_id:
            return
        r = db.query(AssistanceRequestModel).filter(AssistanceRequestModel.id == request_id).first()
        if r and r.status != "Resolved":
            r.status = new_status

    @staticmethod
    def _stop_duty(v: VolunteerProfileModel, now: datetime) -> None:
        """Adds the time since check-in to hours_logged."""
        if v.duty_status == "On Duty" and v.checked_in_at:
            v.hours_logged = (v.hours_logged or 0) + (now - v.checked_in_at).total_seconds() / 3600
        v.checked_in_at = None

    def accept_assignment(self, db: Session, user: Dict[str, Any], assignment_id: str) -> Optional[Dict[str, Any]]:
        v = self.get_or_create_volunteer_profile(db, user)
        if v.current_assignment:
            raise RepositoryError("Complete or drop your current task before accepting another.")
        a = db.query(VolunteerAssignmentModel).filter(VolunteerAssignmentModel.id == assignment_id).first()
        if not a:
            return None

        # Conditional UPDATE: only one volunteer can move a task out of "Available".
        claimed = db.query(VolunteerAssignmentModel).filter(
            VolunteerAssignmentModel.id == assignment_id,
            VolunteerAssignmentModel.status == "Available",
        ).update(
            {"status": "In Progress", "assigned_volunteer_id": v.id, "accepted_at": datetime.utcnow()},
            synchronize_session=False,
        )
        if claimed == 0:
            db.rollback()
            raise RepositoryError("Another volunteer already accepted this task.")

        db.refresh(a)
        assignment_dict = assignment_to_dict(a)
        v.current_assignment = assignment_dict
        self._set_request_status(db, a.request_id, "In Progress")
        db.commit()
        return assignment_dict

    def decline_assignment(self, db: Session, user: Dict[str, Any], assignment_id: str) -> Optional[Dict[str, Any]]:
        """Hides an open task for this volunteer only. Declining your own active task drops it
        back into the open pool for others."""
        v = self.get_or_create_volunteer_profile(db, user)
        a = db.query(VolunteerAssignmentModel).filter(VolunteerAssignmentModel.id == assignment_id).first()
        if not a:
            return None

        if a.assigned_volunteer_id == v.id and a.status == "In Progress":
            self._stop_duty(v, datetime.utcnow())
            v.duty_status = "Off Duty"
            v.current_assignment = None
            a.status = "Available"
            a.assigned_volunteer_id = None
            a.accepted_at = None
            self._set_request_status(db, a.request_id, "Assigned")

        v.declined_assignment_ids = sorted(set(v.declined_assignment_ids or []) | {a.id})
        db.commit()
        db.refresh(v)
        return volunteer_profile_to_dict(v)

    def cancel_assignment(self, db: Session, assignment_id: str) -> Optional[Dict[str, Any]]:
        """Coordinator withdraws a task; the linked request goes back to Verified."""
        a = db.query(VolunteerAssignmentModel).filter(VolunteerAssignmentModel.id == assignment_id).first()
        if not a:
            return None
        if a.status == "Completed":
            raise RepositoryError("Completed tasks cannot be cancelled.")
        if a.assigned_volunteer_id:
            v = db.query(VolunteerProfileModel).filter(VolunteerProfileModel.id == a.assigned_volunteer_id).first()
            if v and (v.current_assignment or {}).get("id") == a.id:
                self._stop_duty(v, datetime.utcnow())
                v.duty_status = "Off Duty"
                v.current_assignment = None
        a.status = "Cancelled"
        self._set_request_status(db, a.request_id, "Verified")
        db.commit()
        db.refresh(a)
        return assignment_to_dict(a)

    def update_assignment_status(self, db: Session, assignment_id: str, new_status: str) -> bool:
        a = db.query(VolunteerAssignmentModel).filter(VolunteerAssignmentModel.id == assignment_id).first()
        if a:
            a.status = new_status
            db.commit()
            return True
        return False

    def get_all_volunteers(self, db: Session) -> List[Dict[str, Any]]:
        users = db.query(UserModel).filter(UserModel.role.in_(["fieldworker", "volunteer"])).order_by(UserModel.created_at.desc()).all()
        profiles = {
            p.id: p
            for p in db.query(VolunteerProfileModel).filter(VolunteerProfileModel.id.in_([u.id for u in users])).all()
        } if users else {}
        result = []
        for u in users:
            d = user_to_dict(u)
            p = profiles.get(u.id)
            d.update({
                "district": p.district if p else None,
                "dutyStatus": (p.duty_status if p else None) or "Off Duty",
                "isAvailable": p.is_available if p else True,
                "currentAssignment": p.current_assignment if p else None,
                "hoursLogged": round(p.hours_logged or 0, 1) if p else 0,
                "tasksCompleted": p.tasks_completed if p else 0,
            })
            result.append(d)
        return result

    def create_assignment(self, db: Session, data: Dict[str, Any], commit: bool = True) -> Dict[str, Any]:
        a = VolunteerAssignmentModel(
            id=new_id("assign"),
            title=data.get("title", "Emergency Relief Dispatch"),
            location=data.get("location", "Field Station"),
            district=data.get("district", "Sunamganj"),
            duration_hours=data.get("durationHours") or data.get("duration_hours", 4),
            team_size=data.get("teamSize") or data.get("team_size", 4),
            priority=data.get("priority", "high"),
            status="Available",
            request_id=data.get("request_id"),
        )
        db.add(a)
        if not commit:
            db.flush()
            return assignment_to_dict(a)
        db.commit()
        db.refresh(a)
        return assignment_to_dict(a)

    def checkin_volunteer(self, db: Session, user: Dict[str, Any], status: str) -> Dict[str, Any]:
        """
        "Checked In" starts the duty clock, "Paused" stops it, "Completed" stops it and
        finishes the current task (resolving the citizen request it came from).
        """
        v = self.get_or_create_volunteer_profile(db, user)
        now = datetime.utcnow()
        if status == "Checked In":
            if v.duty_status != "On Duty":
                v.duty_status = "On Duty"
                v.checked_in_at = now
        elif status == "Paused":
            self._stop_duty(v, now)
            v.duty_status = "Paused"
        elif status == "Completed":
            if not v.current_assignment:
                raise RepositoryError("You have no active task to complete.")
            self._stop_duty(v, now)
            v.duty_status = "Off Duty"
            task = db.query(VolunteerAssignmentModel).filter(
                VolunteerAssignmentModel.id == v.current_assignment.get("id")
            ).first()
            if task:
                task.status = "Completed"
                task.completed_at = now
                self._set_request_status(db, task.request_id, "Resolved")
            v.tasks_completed = (v.tasks_completed or 0) + 1
            v.current_assignment = None
        else:
            raise RepositoryError(f"Unknown duty status '{status}'.", status_code=400)
        db.commit()
        db.refresh(v)
        return volunteer_profile_to_dict(v)

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

    def record_stock_movement(
        self, db: Session, item_id: str, movement_type: str, quantity: int,
        from_to: str, reference: Optional[str], notes: Optional[str], actor_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Receives (INBOUND) or dispatches (DISPATCH) stock and logs the movement."""
        w = db.query(WarehouseItemModel).filter(WarehouseItemModel.id == item_id).first()
        if not w:
            return None
        if movement_type == "DISPATCH":
            if quantity > w.available_count:
                raise RepositoryError(f"Only {w.available_count} {w.unit} of {w.name} in stock.")
            w.available_count -= quantity
        else:
            w.available_count += quantity

        if w.available_count >= w.min_stock_threshold:
            w.status = "OK"
        elif w.available_count >= 0.8 * w.min_stock_threshold:
            w.status = "CAUTION"
        else:
            w.status = "LOW"
        w.last_count_date = datetime.utcnow().strftime("%Y-%m-%d")

        mv = WarehouseMovementModel(
            id=new_id("mov"),
            item_id=w.id,
            movement_type=movement_type,
            quantity=quantity,
            from_to=from_to,
            reference=reference,
            notes=notes,
            actor_id=actor_id,
        )
        db.add(mv)
        db.commit()
        db.refresh(w)
        db.refresh(mv)
        return {"item": warehouse_to_dict(w), "movement": movement_to_dict(mv, w.name)}

    def get_stock_movements(self, db: Session, limit: int = 50) -> List[Dict[str, Any]]:
        rows = db.query(WarehouseMovementModel).order_by(WarehouseMovementModel.created_at.desc()).limit(limit).all()
        names = {w.id: w.name for w in db.query(WarehouseItemModel).all()}
        return [movement_to_dict(mv, names.get(mv.item_id, mv.item_id)) for mv in rows]

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
        user_id = data.get("id") or new_id(f"usr-{data.get('role', 'public')}")
        
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
            "roles": ["public", "fieldworker", "admin"]
        }


repo = Repository()

