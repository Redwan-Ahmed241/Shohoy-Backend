import sys
import os

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project directory to Python sys.path
project_dir = os.path.abspath(os.path.dirname(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)


from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

print("=" * 60)
print("RUNNING SHOHAY FASTAPI BACKEND SUITE TEST")
print("=" * 60)

# 1. Root & Health
res = client.get("/")
assert res.status_code == 200, f"Root failed: {res.text}"
print("[PASS] GET / passed:", res.json()["service"])

res = client.get("/health")
assert res.status_code == 200, f"Health failed: {res.text}"
print("[PASS] GET /health passed:", res.json()["status"])

# 2. Alerts
res = client.get("/api/alerts")
assert res.status_code == 200, f"Get alerts failed: {res.text}"
alerts = res.json()
assert len(alerts) >= 4, f"Expected >= 4 alerts, got {len(alerts)}"
print(f"[PASS] GET /api/alerts passed: returned {len(alerts)} alerts")

res = client.get("/api/alerts/alert-1")
assert res.status_code == 200
assert res.json()["id"] == "alert-1"
print("[PASS] GET /api/alerts/alert-1 passed:", res.json()["title"][:30], "...")

new_alert_payload = {
    "severity": "CRITICAL",
    "type": "Flash Flood",
    "title": "Emergency Flash Flood in Sylhet",
    "description": "High water levels threatening riverbanks.",
    "affectedAreas": ["Sylhet Sadar"],
    "verificationStatus": "Government Verified"
}
res = client.post("/api/alerts", json=new_alert_payload)
assert res.status_code == 201
print("[PASS] POST /api/alerts passed, created:", res.json()["id"])

# 3. Shelters
res = client.get("/api/shelters")
assert res.status_code == 200
shelters = res.json()
print(f"[PASS] GET /api/shelters passed: returned {len(shelters)} shelters")

res = client.get("/api/shelters/summary")
assert res.status_code == 200
summary = res.json()
print("[PASS] GET /api/shelters/summary passed:", summary)

# 4. Requests (Multi-step assistance request)
request_payload = {
    "types": ["rescue", "food"],
    "householdSize": 4,
    "vulnerableCount": {"children": 1, "elderly": 1, "pregnant": 0, "disabled": 0},
    "location": {
        "district": "Sunamganj",
        "upazila": "Tahirpur",
        "union": "Dakshin Sreepur",
        "address": "Bazar Road, Ward 2"
    },
    "contact": {
        "name": "Kamal Hossain",
        "phone": "01812345678",
        "isAnonymous": False
    },
    "notes": "Elderly person needs stretcher support."
}
res = client.post("/api/requests", json=request_payload)
assert res.status_code == 201
req_data = res.json()
tracking_id = req_data["trackingId"]
print(f"[PASS] POST /api/requests passed, tracking ID created: {tracking_id}")

res = client.get(f"/api/requests/track/{tracking_id}")
assert res.status_code == 200
print(f"[PASS] GET /api/requests/track/{tracking_id} passed, status: {res.json()['status']}")

# 5. Campaigns
res = client.get("/api/campaigns")
assert res.status_code == 200
print(f"[PASS] GET /api/campaigns passed: returned {len(res.json())} campaigns")

res = client.get("/api/campaigns/summary")
assert res.status_code == 200
print("[PASS] GET /api/campaigns/summary passed:", res.json())

# 6. Contacts
res = client.get("/api/contacts")
assert res.status_code == 200
print(f"[PASS] GET /api/contacts passed: returned {len(res.json())} contacts")

# 7. Volunteers
res = client.get("/api/volunteers/profile")
assert res.status_code == 200
print("[PASS] GET /api/volunteers/profile passed, volunteer:", res.json()["name"])

res = client.get("/api/volunteers/assignments")
assert res.status_code == 200
print(f"[PASS] GET /api/volunteers/assignments passed: returned {len(res.json())} assignments")

res = client.post("/api/volunteers/assignments/assign-1/accept")
assert res.status_code == 200
print("[PASS] POST /api/volunteers/assignments/assign-1/accept passed:", res.json())

# 8. Warehouse
res = client.get("/api/warehouse/inventory")
assert res.status_code == 200
print(f"[PASS] GET /api/warehouse/inventory passed: returned {len(res.json())} items")

res = client.get("/api/warehouse/alerts/low-stock")
assert res.status_code == 200
print(f"[PASS] GET /api/warehouse/alerts/low-stock passed: returned {len(res.json())} low stock items")

# 9. Auth Suite (Twilio SMS, Resend Email, Public & Fieldworker)
# 9a. Options
res = client.get("/api/auth/options")
assert res.status_code == 200, f"Options failed: {res.text}"
opts = res.json()
assert "First Aid & CPR" in opts["skills"]
assert "Engine Boat / Speedboat" in opts["equipment"]
assert "Male" in opts["genders"]
assert "fieldworker" in opts["roles"]
print(f"[PASS] GET /api/auth/options passed: {len(opts['skills'])} skills, {len(opts['equipment'])} equipment items")

# 9b. Send OTP via Email (Resend)
email_res = client.post("/api/auth/send-otp", json={"email": "rahim.ahmed@example.com"})
assert email_res.status_code == 200, f"Send OTP email failed: {email_res.text}"
email_data = email_res.json()
assert email_data["email"] == "rahim.ahmed@example.com"
assert email_data["debug_otp"] is not None
print(f"[PASS] POST /api/auth/send-otp (Email/Resend) passed: OTP={email_data['debug_otp']}")

# 9c. Verify OTP with invalid code
invalid_res = client.post("/api/auth/verify-otp", json={"email": "rahim.ahmed@example.com", "otp": "000000"})
assert invalid_res.status_code == 400
print("[PASS] POST /api/auth/verify-otp invalid code rejected as expected")

# 9d. Verify OTP for existing user -> logs in and returns bearer token
verify_res = client.post("/api/auth/verify-otp", json={"email": "rahim.ahmed@example.com", "otp": email_data["debug_otp"]})
assert verify_res.status_code == 200, f"Verify existing user failed: {verify_res.text}"
auth_data = verify_res.json()
assert auth_data["is_new_user"] is False
assert auth_data["token"] is not None
auth_token = auth_data["token"]
print("[PASS] POST /api/auth/verify-otp (Existing User) passed, token issued for:", auth_data["user"]["first_name"])


# 9f. Register new Public User
import time
import random
unique_id = f"{int(time.time())}_{random.randint(100, 999)}"
new_public_phone = f"0199{random.randint(1000000, 9999999)}"
new_public_payload = {
    "first_name": "Tanvir",
    "last_name": "Hasan",
    "phone_number": new_public_phone,
    "email": f"tanvir_{unique_id}@example.com",
    "skills": ["First Aid & CPR", "Ham Radio Operation"],  # predefined + custom
    "equipment": ["Life Jackets & Buoys", "Drone for Aerial Survey"],  # predefined + custom
    "gender": "Male",
    "avatar": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"
}
pub_reg_res = client.post("/api/auth/register/public", json=new_public_payload)
assert pub_reg_res.status_code == 201, f"Register public failed: {pub_reg_res.text}"
pub_user = pub_reg_res.json()["user"]
assert pub_user["role"] == "public"
assert "Ham Radio Operation" in pub_user["skills"]
assert "Drone for Aerial Survey" in pub_user["equipment"]
pub_token = pub_reg_res.json()["token"]
print(f"[PASS] POST /api/auth/register/public passed: created {pub_user['first_name']} {pub_user['last_name']}")

# 9g. Register new Fieldworker
new_field_phone = f"0188{random.randint(1000000, 9999999)}"
new_field_payload = {
    "first_name": "Fatima",
    "last_name": "Zahra",
    "phone_number": new_field_phone,
    "email": f"fatima_{unique_id}@rescue.org",
    "skills": ["Search & Rescue", "Medical / Nursing Care", "High Altitude Climbing"],
    "equipment": ["Engine Boat / Speedboat", "First Aid Medical Kit", "Oxygen Concentrator"],
    "gender": "Female",
    "nid_number": f"1995{random.randint(1000000000000, 9999999999999)}",
    "address": "Upazila Health Complex, Tahirpur, Sunamganj",
    "dob": "1995-11-04",
    "experience_certificate": "https://storage.shohay.org/certs/fatima_paramedic_license.pdf"
}
field_reg_res = client.post("/api/auth/register/fieldworker", json=new_field_payload)
assert field_reg_res.status_code == 201, f"Register fieldworker failed: {field_reg_res.text}"
field_user = field_reg_res.json()["user"]
assert field_user["role"] == "fieldworker"
assert field_user["verification_status"] == "Pending"
field_token = field_reg_res.json()["token"]
print(f"[PASS] POST /api/auth/register/fieldworker passed: created {field_user['first_name']} (NID: {field_user['nid_number']})")


# 9h. Get Profile (/me) with Bearer token
me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {field_token}"})
assert me_res.status_code == 200, f"Get /me failed: {me_res.text}"
assert me_res.json()["id"] == field_user["id"]
print(f"[PASS] GET /api/auth/me passed with token: {me_res.json()['name']} ({me_res.json()['role']})")

# 9i. Update Profile
update_res = client.put(
    "/api/auth/profile",
    headers={"Authorization": f"Bearer {pub_token}"},
    json={"skills": ["First Aid & CPR", "Ham Radio Operation", "Emergency Water Transport"]}
)
assert update_res.status_code == 200, f"Update profile failed: {update_res.text}"
assert "Emergency Water Transport" in update_res.json()["skills"]
print("[PASS] PUT /api/auth/profile passed: skills successfully updated")

print("=" * 60)
print("ALL BACKEND & AUTH SUITE TESTS PASSED WITH 100% SUCCESS!")
print("=" * 60)

