import copy
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from .mock_data import (
    MOCK_ALERTS,
    MOCK_SHELTERS,
    MOCK_CAMPAIGNS,
    MOCK_CONTACTS,
    MOCK_VOLUNTEER_ASSIGNMENTS,
    MOCK_VOLUNTEER_PROFILE,
    MOCK_WAREHOUSE_ITEMS,
    MOCK_REQUESTS_DB,
    MOCK_USERS,
    PREDEFINED_SKILLS,
    PREDEFINED_EQUIPMENT,
    PREDEFINED_GENDERS
)

class InMemoryDatabase:
    def __init__(self):
        self.alerts: List[Dict[str, Any]] = copy.deepcopy(MOCK_ALERTS)
        self.shelters: List[Dict[str, Any]] = copy.deepcopy(MOCK_SHELTERS)
        self.campaigns: List[Dict[str, Any]] = copy.deepcopy(MOCK_CAMPAIGNS)
        self.contacts: List[Dict[str, Any]] = copy.deepcopy(MOCK_CONTACTS)
        self.volunteer_assignments: List[Dict[str, Any]] = copy.deepcopy(MOCK_VOLUNTEER_ASSIGNMENTS)
        self.volunteer_profile: Dict[str, Any] = copy.deepcopy(MOCK_VOLUNTEER_PROFILE)
        self.warehouse_items: List[Dict[str, Any]] = copy.deepcopy(MOCK_WAREHOUSE_ITEMS)
        self.requests_db: Dict[str, Dict[str, Any]] = copy.deepcopy(MOCK_REQUESTS_DB)
        self.users: List[Dict[str, Any]] = copy.deepcopy(MOCK_USERS)

    # ── ALERTS ──
    def get_alerts(self, severity: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        results = list(self.alerts)
        if severity and severity != 'ALL CLEAR':
            results = [a for a in results if a.get('severity') == severity]
        elif severity == 'ALL CLEAR':
            results = [a for a in results if a.get('severity') == 'ALL CLEAR']

        if search and search.strip():
            q = search.lower().strip()
            results = [
                a for a in results
                if q in a.get('title', '').lower()
                or q in a.get('description', '').lower()
                or any(q in area.lower() for area in a.get('affectedAreas', []))
            ]
        return results

    def get_alert_by_id(self, alert_id: str) -> Optional[Dict[str, Any]]:
        for a in self.alerts:
            if a['id'] == alert_id:
                return a
        return None

    def create_alert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        alert_id = f"alert-{len(self.alerts) + 1}"
        new_alert = {
            **data,
            "id": alert_id,
            "issuedAt": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.alerts.insert(0, new_alert)
        return new_alert

    # ── SHELTERS ──
    def get_shelters(self, status: Optional[str] = None, district: Optional[str] = None, amenities: Optional[Dict[str, bool]] = None) -> List[Dict[str, Any]]:
        results = list(self.shelters)
        if status and status != 'All':
            results = [s for s in results if s.get('status') == status]
        if district and district != 'All':
            results = [s for s in results if s.get('district', '').lower() == district.lower()]
        if amenities:
            active_keys = [k for k, v in amenities.items() if v]
            if active_keys:
                results = [s for s in results if all(s.get('amenities', {}).get(k) for k in active_keys)]
        return results

    def get_shelter_stats(self) -> Dict[str, Any]:
        total = len(self.shelters)
        open_count = sum(1 for s in self.shelters if s.get('status') == 'Open')
        nearly_full = sum(1 for s in self.shelters if s.get('status') == 'Nearly Full')
        free_spaces = sum(max(0, s.get('capacity', 0) - s.get('occupancy', 0)) for s in self.shelters)
        return {
            "totalShelters": total,
            "openShelters": open_count,
            "nearlyFull": nearly_full,
            "freeSpaces": f"{free_spaces:,}"
        }

    # ── REQUESTS ──
    def create_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        random_num = random.randint(10000, 99999)
        tracking_id = f"SHY-2024-{random_num}"
        record_id = f"req-{int(datetime.now().timestamp() * 1000)}"

        new_record = {
            **payload,
            "id": record_id,
            "trackingId": tracking_id,
            "status": "Pending",
            "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.requests_db[tracking_id] = new_record
        return new_record

    def get_request_by_tracking_id(self, tracking_id: str) -> Optional[Dict[str, Any]]:
        clean_id = tracking_id.strip().upper()
        return self.requests_db.get(clean_id)

    # ── CAMPAIGNS ──
    def get_campaigns(self) -> List[Dict[str, Any]]:
        return list(self.campaigns)

    def get_campaign_stats(self) -> Dict[str, Any]:
        active = len(self.campaigns)
        households = sum(c.get('householdsReached', 0) for c in self.campaigns)
        total_raised = sum(c.get('raisedAmount', 0.0) for c in self.campaigns)
        return {
            "activeCampaigns": active,
            "householdsReached": f"{households:,}",
            "totalRaisedBDT": f"৳{(total_raised / 100000):.1f}L"
        }

    # ── CONTACTS ──
    def get_contacts(self, category: Optional[str] = None, district: Optional[str] = None) -> List[Dict[str, Any]]:
        results = list(self.contacts)
        if category and category != 'All':
            results = [c for c in results if c.get('category') == category]
        if district and district != 'All Districts':
            results = [c for c in results if not c.get('district') or c.get('district', '').lower() == district.lower()]
        return results

    # ── VOLUNTEERS ──
    def get_volunteer_profile(self) -> Dict[str, Any]:
        return copy.deepcopy(self.volunteer_profile)

    def get_open_assignments(self) -> List[Dict[str, Any]]:
        return list(self.volunteer_assignments)

    def update_assignment_status(self, assignment_id: str, new_status: str) -> bool:
        for a in self.volunteer_assignments:
            if a['id'] == assignment_id:
                a['status'] = new_status
                return True
        return False

    # ── WAREHOUSE ──
    def get_warehouse_inventory(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        results = list(self.warehouse_items)
        if category and category != 'All':
            results = [item for item in results if item.get('category') == category]
        return results

    def get_low_stock_items(self) -> List[Dict[str, Any]]:
        return [item for item in self.warehouse_items if item.get('status') == 'LOW']

    def get_expiring_items(self) -> List[Dict[str, Any]]:
        return [item for item in self.warehouse_items if item.get('expiryDate')]

    # ── USERS & AUTH ──
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        for u in self.users:
            if u["id"] == user_id:
                return copy.deepcopy(u)
        return None

    def get_user_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        clean_target = phone.strip().replace(" ", "").replace("-", "")
        for u in self.users:
            p = (u.get("phone_number") or "").strip().replace(" ", "").replace("-", "")
            if p and (p == clean_target or p.endswith(clean_target) or clean_target.endswith(p)):
                return copy.deepcopy(u)
        return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        clean_target = email.strip().lower()
        for u in self.users:
            e = (u.get("email") or "").strip().lower()
            if e and e == clean_target:
                return copy.deepcopy(u)
        return None

    def get_user_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        clean_id = identifier.strip().lower()
        if "@" in clean_id:
            return self.get_user_by_email(clean_id)
        return self.get_user_by_phone(clean_id)

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = user_data.get("id") or f"usr-{user_data.get('role', 'public')}-{len(self.users) + 1:03d}"
        now_str = datetime.utcnow().isoformat() + "Z"
        new_user = {
            **user_data,
            "id": user_id,
            "created_at": now_str,
            "updated_at": now_str,
        }
        self.users.append(new_user)
        return copy.deepcopy(new_user)

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for i, u in enumerate(self.users):
            if u["id"] == user_id:
                now_str = datetime.utcnow().isoformat() + "Z"
                updated = {**u, **updates, "updated_at": now_str}
                self.users[i] = updated
                return copy.deepcopy(updated)
        return None

    def get_auth_options(self) -> Dict[str, Any]:
        return {
            "skills": PREDEFINED_SKILLS,
            "equipment": PREDEFINED_EQUIPMENT,
            "genders": PREDEFINED_GENDERS,
            "roles": ["public", "fieldworker"]
        }

# Singleton instance
db = InMemoryDatabase()

