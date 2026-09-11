import sys
import os

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

project_dir = os.path.abspath(os.path.dirname(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from database import connection
from database.connection import init_engine, Base
from database.models import (
    AlertModel, ShelterModel, CampaignModel, ContactModel,
    AssistanceRequestModel, VolunteerProfileModel,
    VolunteerAssignmentModel, WarehouseItemModel, UserModel
)
from database.supabase_repository import supabase_repo

print("=" * 60)
print("TESTING SUPABASE SQLALCHEMY ORM & REPOSITORY LAYER")
print("=" * 60)

# 1. Initialize SQLite in-memory to test all ORM models & queries
engine = init_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
print("[PASS] Table schemas generated successfully with Base.metadata.create_all!")

db = connection.get_session()

# 2. Test Alert CRUD
alert_res = supabase_repo.create_alert(db, {
    "severity": "CRITICAL",
    "type": "Flash Flood Warning",
    "title": "Severe River Inundation",
    "description": "Rising waters in Sunamganj",
    "affectedAreas": ["Sunamganj Sadar", "Tahirpur"],
    "verificationStatus": "Government Verified"
})
assert alert_res["id"] == "alert-1", f"Expected alert-1, got {alert_res['id']}"
print("[PASS] create_alert passed:", alert_res["id"], alert_res["title"])

alerts = supabase_repo.get_alerts(db, search="Tahirpur")
assert len(alerts) == 1, f"Search by affectedArea failed: {len(alerts)}"
print("[PASS] get_alerts with affectedArea search passed!")

# 3. Test Shelter CRUD
shelter = ShelterModel(
    id="shelter-1",
    name="Test College Shelter",
    address="College Road",
    upazila="Sadar",
    district="Sunamganj",
    occupancy=400,
    capacity=1000,
    status="Open",
    route_status="Route OK",
    category="School",
    amenities={"drinkingWater": True, "toilets": True, "generator": True}
)
db.add(shelter)
db.commit()

shelters = supabase_repo.get_shelters(db, status="Open", district="Sunamganj")
assert len(shelters) == 1
print("[PASS] get_shelters passed:", shelters[0]["name"])

stats = supabase_repo.get_shelter_stats(db)
assert stats["totalShelters"] == 1
assert stats["openShelters"] == 1
print("[PASS] get_shelter_stats passed:", stats)

# 4. Test Assistance Requests CRUD
req = supabase_repo.create_request(db, {
    "types": ["rescue", "food"],
    "householdSize": 5,
    "vulnerableCount": {"children": 2},
    "location": {"district": "Sunamganj"},
    "contact": {"name": "Rahim", "phone": "01711111111"}
})
assert req["trackingId"].startswith("SHY-2024-")
print("[PASS] create_request passed:", req["trackingId"])

fetched_req = supabase_repo.get_request_by_tracking_id(db, req["trackingId"])
assert fetched_req is not None
print("[PASS] get_request_by_tracking_id passed!")

# 5. Test Campaigns CRUD
camp = CampaignModel(
    id="camp-1",
    title="Emergency Food Drive",
    organization="Relief Org",
    district="Sunamganj",
    coverage_areas=["Sadar"],
    target_amount=1000000,
    raised_amount=500000,
    households_target=2000,
    households_reached=1500,
    verification_status="Government Verified"
)
db.add(camp)
db.commit()

campaigns = supabase_repo.get_campaigns(db)
assert len(campaigns) == 1
camp_stats = supabase_repo.get_campaign_stats(db)
assert camp_stats["activeCampaigns"] == 1
print("[PASS] Campaigns & stats passed:", camp_stats)

# 6. Test Contacts CRUD
contact = ContactModel(
    id="contact-1",
    title="Emergency Hotline",
    category="National Emergency",
    district=None,
    phone="999",
    description="24/7 Police, Fire, Ambulance",
    availability="24/7",
    is_toll_free=True,
    is_verified=True,
    last_verified="2024-07-15"
)
db.add(contact)
db.commit()

contacts = supabase_repo.get_contacts(db, category="National Emergency", district="Sunamganj")
assert len(contacts) == 1
print("[PASS] get_contacts passed:", contacts[0]["title"])

# 7. Test Volunteers CRUD
vol = VolunteerProfileModel(
    id="vol-1",
    name="Test Volunteer",
    code="VOL-TEST-01",
    district="Sunamganj",
    join_date="12 July 2024",
    is_available=True,
    hours_logged=10,
    tasks_completed=3,
    rating=5.0,
    skills=["First Aid"]
)
db.add(vol)

assignment = VolunteerAssignmentModel(
    id="assign-1",
    title="Food Distribution",
    location="Camp 1",
    district="Sunamganj",
    duration_hours=4,
    team_size=5,
    priority="high",
    status="Available"
)
db.add(assignment)
db.commit()

prof = supabase_repo.get_volunteer_profile(db)
assert prof["name"] == "Test Volunteer"
assigns = supabase_repo.get_open_assignments(db)
assert len(assigns) == 1
supabase_repo.update_assignment_status(db, "assign-1", "Assigned")
assigns_after = supabase_repo.get_open_assignments(db)
assert len(assigns_after) == 0
print("[PASS] Volunteer profile, assignments, and status update passed!")

# 8. Test Warehouse CRUD
item = WarehouseItemModel(
    id="item-1",
    sku="WTR-01",
    name="Water Bottle 5L",
    category="Water",
    available_count=20,
    unit="Bottles",
    reserved_count=5,
    min_stock_threshold=50,
    status="LOW",
    expiry_date="2025-12-31",
    warehouse_name="Main Depot",
    last_count_date="2024-07-15"
)
db.add(item)
db.commit()

inventory = supabase_repo.get_warehouse_inventory(db)
assert len(inventory) == 1
low_stock = supabase_repo.get_low_stock_items(db)
assert len(low_stock) == 1
expiring = supabase_repo.get_expiring_items(db)
assert len(expiring) == 1
print("[PASS] Warehouse inventory, low-stock, and expiring queries passed!")

# 9. Test Users (Public & Fieldworker)
public_user = supabase_repo.create_user(db, {
    "role": "public",
    "first_name": "Sadman",
    "last_name": "Shakib",
    "phone_number": "01755554444",
    "email": "sadman@example.com",
    "avatar": "https://images.unsplash.com/photo-1535713875002",
    "gender": "Male",
    "skills": ["First Aid & CPR", "Drone Mapping"],
    "equipment": ["Life Jackets & Buoys"],
    "verification_status": "Verified"
})
assert public_user["id"].startswith("usr-public")
assert public_user["role"] == "public"
print("[PASS] Supabase ORM create_user (Public) passed:", public_user["firstName"], public_user["lastName"])

field_user = supabase_repo.create_user(db, {
    "role": "fieldworker",
    "first_name": "Tasmia",
    "last_name": "Rahman",
    "phone_number": "01855553333",
    "email": "tasmia.field@rescue.org",
    "avatar": "https://images.unsplash.com/photo-1494790108377",
    "gender": "Female",
    "skills": ["Search & Rescue", "Boat Operation & Navigation"],
    "equipment": ["Engine Boat / Speedboat"],
    "nid_number": "19939988776655443",
    "address": "Holding 12, River Road, Sunamganj",
    "dob": "1993-05-15",
    "experience_certificate": "https://certs.shohay.org/tasmia_rescue_cert.pdf",
    "verification_status": "Pending"
})
assert field_user["id"].startswith("usr-fieldworker")
assert field_user["nidNumber"] == "19939988776655443"
assert field_user["verificationStatus"] == "Pending"
print("[PASS] Supabase ORM create_user (Fieldworker) passed:", field_user["firstName"], f"(NID: {field_user['nidNumber']})")

by_phone = supabase_repo.get_user_by_phone(db, "01755554444")
assert by_phone is not None
assert by_phone["id"] == public_user["id"]
print("[PASS] Supabase ORM get_user_by_phone passed!")

by_email = supabase_repo.get_user_by_email(db, "tasmia.field@rescue.org")
assert by_email is not None
assert by_email["id"] == field_user["id"]
print("[PASS] Supabase ORM get_user_by_email passed!")

updated = supabase_repo.update_user(db, public_user["id"], {"skills": ["First Aid & CPR", "Drone Mapping", "Ambulance Driver"]})
assert len(updated["skills"]) == 3
print("[PASS] Supabase ORM update_user passed!")

options = supabase_repo.get_auth_options()
assert len(options["skills"]) > 0
assert len(options["equipment"]) > 0
print("[PASS] Supabase ORM get_auth_options passed!")

# 10. Test Vercel Entrypoint
from api.index import app as vercel_app
assert vercel_app is not None
print("[PASS] api/index.py imports and exposes FastAPI app instance for Vercel!")

db.close()

print("=" * 60)
print("ALL SUPABASE ORM & REPOSITORY TESTS PASSED WITH 100% SUCCESS!")
print("=" * 60)
