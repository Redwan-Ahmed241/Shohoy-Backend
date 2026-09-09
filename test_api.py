import sys
import os

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add Shohoy-Backend to Python sys.path
backend_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'Shohoy-Backend'))
sys.path.insert(0, backend_dir)

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

# 9. Auth
res = client.post("/api/auth/login", json={"phone": "01712345678", "role": "volunteer"})
assert res.status_code == 200
print("[PASS] POST /api/auth/login passed:", res.json()["message"])

res = client.post("/api/auth/verify-otp", json={"phone": "01712345678", "otp": "123456", "role": "volunteer"})
assert res.status_code == 200
print("✓ POST /api/auth/verify-otp passed, user:", res.json()["user"]["name"])

print("=" * 60)
print("ALL BACKEND SUITE TESTS PASSED WITH 100% SUCCESS!")
print("=" * 60)
