"""
End-to-end flow test: runs the whole Shohay journey against a throwaway SQLite database.

    python test_flows.py

1. Permissions   — who may call what (401 not signed in, 403 wrong role)
2. Rescue flow   — citizen request -> approve -> dispatch -> volunteer accepts -> duty -> complete -> resolved
3. Volunteers    — decline is personal, two volunteers cannot take the same task, dropping a task
4. Warehouse     — receive and dispatch stock
5. UAV / drones  — register -> heartbeat -> detection -> assign rescuer -> acknowledge -> rescue request
6. Supabase Auth — signed tokens verified, accounts created/linked, roles decided by the server
"""
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
# Default: a throwaway SQLite file. Optionally point SHOHAY_TEST_DB_URL at an EMPTY, disposable
# PostgreSQL database that already has the schema (migrations applied) — never at production.
TEST_DB_URL = os.environ.get("SHOHAY_TEST_DB_URL", "")
os.environ["SUPABASE_DB_URL"] = TEST_DB_URL
os.environ["LOCAL_DB_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test_flows.db"
os.environ["RESEND_API_KEY"] = ""
os.environ["SUPABASE_URL"] = "https://test-project.supabase.co"
os.environ["ADMIN_EMAILS"] = "boss@example.org"

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from database.connection import get_session  # noqa: E402
from database.models import VolunteerProfileModel  # noqa: E402
from database.repository import repo  # noqa: E402
from services.otp_service import otp_service  # noqa: E402

client = TestClient(app)

if TEST_DB_URL:
    from database.seed import seed_if_empty  # noqa: E402
    with get_session() as _db:
        seed_if_empty(_db)


def auth(user_id: str) -> dict:
    return {"Authorization": f"Bearer {otp_service.create_token({'sub': user_id})}"}


def ok(res, code=200):
    assert res.status_code == code, f"{res.request.method} {res.request.url.path} -> {res.status_code}: {res.text}"
    return res.json() if res.content else None


def step(msg: str):
    print(f"[PASS] {msg}")


ADMIN = auth("usr-admin-001")
VOL_A = auth("usr-field-001")
CITIZEN = auth("usr-public-001")

with get_session() as db:
    repo.create_user(db, {"id": "usr-field-002", "role": "fieldworker", "first_name": "Karim", "last_name": "Uddin",
                          "email": "karim@example.org", "verification_status": "Verified"})
VOL_B = auth("usr-field-002")

print("=" * 64)
print("SHOHAY END-TO-END FLOW TEST")
print("=" * 64)

# ── 1. Permissions ──
for method, path in [("get", "/api/requests"), ("get", "/api/volunteers"), ("get", "/api/warehouse/inventory"),
                     ("get", "/api/uav/logs"), ("get", "/api/volunteers/profile")]:
    assert getattr(client, method)(path).status_code == 401, path
for path in ["/api/requests", "/api/volunteers", "/api/warehouse/inventory", "/api/uav/logs"]:
    assert client.get(path, headers=VOL_A).status_code == 403, path
assert client.get("/api/volunteers/profile", headers=CITIZEN).status_code == 403
for path in ["/api/alerts", "/api/shelters", "/api/campaigns", "/api/contacts"]:
    ok(client.get(path))
assert client.post("/api/auth/login", json={"email": "x@example.org", "role": "admin"}).status_code == 410
step("permissions: public pages open, coordinator/volunteer endpoints protected, legacy login off")

# ── 2. Rescue flow ──
created = ok(client.post("/api/requests", json={
    "types": ["rescue"], "householdSize": 5,
    "vulnerableCount": {"children": 2, "elderly": 1, "pregnant": 0, "disabled": 0},
    "location": {"district": "Sunamganj", "upazila": "Tahirpur", "union": "Sreepur", "address": "Ward 3"},
    "contact": {"name": "Rahima Begum", "phone": "01711111111", "isAnonymous": False},
}), 201)
tracking = created["trackingId"]
public_view = ok(client.get(f"/api/requests/track/{tracking.lower()}"))
assert public_view["status"] == "Pending" and "contact" not in public_view and "location" not in public_view
step(f"citizen submitted {tracking} without an account; tracker hides name/phone/address")

ok(client.patch(f"/api/requests/{created['id']}/status", json={"status": "Verified"}, headers=ADMIN))
dispatched = ok(client.post(f"/api/requests/{created['id']}/dispatch", headers=ADMIN, json={
    "title": "Boat rescue - Tahirpur Ward 3", "location": "Tahirpur", "district": "Sunamganj",
    "durationHours": 3, "teamSize": 2, "priority": "critical",
}))
assert dispatched["status"] == "Assigned" and dispatched["task"]["status"] == "Available"
task_id = dispatched["task"]["id"]
assert client.post(f"/api/requests/{created['id']}/dispatch", headers=ADMIN, json={
    "title": "Duplicate", "location": "x", "district": "Sunamganj"}).status_code == 409
step("coordinator verified and dispatched it; a second dispatch is refused")

open_tasks = ok(client.get("/api/volunteers/assignments", headers=VOL_A))
assert open_tasks[0]["id"] == task_id and open_tasks[0]["requestId"] == created["id"]
ok(client.post(f"/api/volunteers/assignments/{task_id}/accept", headers=VOL_A))
res = client.post(f"/api/volunteers/assignments/{task_id}/accept", headers=VOL_B)
assert res.status_code == 409 and "already accepted" in res.json()["detail"]
assert ok(client.get(f"/api/requests/track/{tracking}"))["status"] == "In Progress"
step("volunteer A accepted (request -> In Progress); volunteer B gets 409 for the same task")

profile = ok(client.post("/api/volunteers/checkin", json={"status": "Checked In"}, headers=VOL_A))
assert profile["dutyStatus"] == "On Duty"
with get_session() as db:  # pretend 90 minutes passed
    v = db.get(VolunteerProfileModel, "usr-field-001")
    v.checked_in_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=90)
    db.commit()
profile = ok(client.post("/api/volunteers/checkin", json={"status": "Completed"}, headers=VOL_A))
assert profile["currentAssignment"] is None and profile["tasksCompleted"] == 1
assert 1.4 <= profile["hoursLogged"] <= 1.6, profile["hoursLogged"]
assert ok(client.get(f"/api/requests/track/{tracking}"))["status"] == "Resolved"
assert client.post("/api/volunteers/checkin", json={"status": "Completed"}, headers=VOL_A).status_code == 409
step(f"duty clock logged {profile['hoursLogged']} h from real time; completing resolved the citizen request")

# ── 3. Volunteer declines and drops ──
t2 = ok(client.post("/api/volunteers/assignments", headers=ADMIN, json={
    "title": "Water distribution", "location": "Chhatak", "district": "Sunamganj"}), 201)["id"]
ok(client.post(f"/api/volunteers/assignments/{t2}/decline", headers=VOL_A))
assert t2 not in [a["id"] for a in ok(client.get("/api/volunteers/assignments", headers=VOL_A))]
assert t2 in [a["id"] for a in ok(client.get("/api/volunteers/assignments", headers=VOL_B))]
ok(client.post(f"/api/volunteers/assignments/{t2}/accept", headers=VOL_B))
profile_b = ok(client.post(f"/api/volunteers/assignments/{t2}/decline", headers=VOL_B))
assert profile_b["currentAssignment"] is None
all_tasks = {a["id"]: a for a in ok(client.get("/api/volunteers/assignments/all", headers=ADMIN))}
assert all_tasks[t2]["status"] == "Available" and all_tasks[task_id]["assignedVolunteerName"] == "Nasrin Akter"
directory = ok(client.get("/api/volunteers", headers=ADMIN))
assert directory["count"] == 2
step("declining hides a task only for that volunteer; dropping an accepted task returns it to the pool")

# ── 4. Warehouse ──
inv = ok(client.get("/api/warehouse/inventory", headers=ADMIN))
item = inv[0]
moved = ok(client.post("/api/warehouse/receive", headers=ADMIN, json={
    "itemId": item["id"], "quantity": 100, "fromTo": "WFP donation -> Sylhet Central", "reference": "DON-1"}))
assert moved["item"]["availableCount"] == item["availableCount"] + 100
res = client.post("/api/warehouse/dispatch", headers=ADMIN, json={
    "itemId": item["id"], "quantity": 10**6, "fromTo": "Sylhet -> Tahirpur"})
assert res.status_code == 409
movements = ok(client.get("/api/warehouse/movements", headers=ADMIN))
assert movements[0]["type"] == "INBOUND" and movements[0]["qty"] == "+100"
step("stock received and logged; over-dispatch refused")

# ── 5. UAV / drones ──
reg = ok(client.post("/api/uav/drones", headers=ADMIN, json={
    "name": "Tahirpur Scout", "registration_id": "SUN-UAV-02", "district": "Sunamganj"}), 201)
drone_id, key = reg["id"], reg["apiKey"]
DRONE = {"X-Drone-Id": "SUN-UAV-02", "X-Drone-Token": key}
assert client.post("/api/uav/drones", headers=ADMIN, json={"name": "dup", "registration_id": "SUN-UAV-02"}).status_code == 409
assert client.post("/api/uav/drones/heartbeat", json={}, headers={**DRONE, "X-Drone-Token": "wrong"}).status_code == 401
hb = ok(client.post("/api/uav/drones/heartbeat", headers=DRONE, json={"latitude": 25.07, "longitude": 91.18, "battery_pct": 87}))
assert hb["isOnline"] and hb["batteryPct"] == 87
assert client.post("/api/uav/drones/heartbeat", headers=DRONE, json={}).status_code == 429
assert client.post("/api/uav/drones/stream", headers=DRONE, json={"stream_url": "javascript:alert(1)"}).status_code == 422
step("drone registered (key shown once), authenticated by header, online after heartbeat, rate-limited")

since = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()  # clock ticks ~15 ms on Windows
det = ok(client.post("/api/uav/detections", headers=DRONE, json={
    "timestamp": datetime.now(timezone.utc).isoformat(), "latitude": 25.0712, "longitude": 91.1843,
    "detection_type": "human", "confidence": 0.94, "bounding_box": {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4}}), 201)
assert client.post("/api/uav/detections", headers=DRONE, json={
    "timestamp": "2026-01-01T00:00:00Z", "latitude": 99, "longitude": 0, "detection_type": "human", "confidence": 0.5}).status_code == 422
polled = ok(client.get("/api/uav/detections", params={"since": since}, headers=ADMIN))
assert [d["id"] for d in polled] == [det["id"]], (since, det, polled)
assert ok(client.get("/api/uav/detections", headers=VOL_A)) == []
step("detection stored; coordinator poll with ?since= finds it; unassigned volunteer sees nothing")

asg = ok(client.post("/api/uav/assignments", headers=ADMIN, json={"user_id": "usr-field-001", "drone_id": drone_id}), 201)
assert client.post("/api/uav/assignments", headers=ADMIN, json={"user_id": "usr-public-001", "drone_id": drone_id}).status_code == 400
assert [d["id"] for d in ok(client.get("/api/uav/detections", headers=VOL_A))] == [det["id"]]
acked = ok(client.post(f"/api/uav/detections/{det['id']}/acknowledge", headers=VOL_A))
assert acked["status"] == "Acknowledged"
assert client.post(f"/api/uav/detections/{det['id']}/acknowledge", headers=VOL_B).status_code == 403
step("assigned volunteer sees and acknowledges the detection; other volunteers are refused")

rescue = ok(client.post(f"/api/uav/detections/{det['id']}/rescue-request", headers=ADMIN))
req = rescue["request"]
assert rescue["detection"]["status"] == "Rescue Requested" and req["status"] == "Verified"
assert req["types"] == ["rescue"] and req["location"]["gpsCoords"] == "25.071200,91.184300"
assert client.post(f"/api/uav/detections/{det['id']}/rescue-request", headers=ADMIN).status_code == 409
queue = ok(client.get("/api/requests", params={"status": "Verified"}, headers=ADMIN))
assert req["id"] in [r["id"] for r in queue]
ok(client.post(f"/api/requests/{req['id']}/dispatch", headers=ADMIN, json={
    "title": "UAV rescue", "location": req["location"]["address"], "district": "Sunamganj", "priority": "critical"}))
step(f"detection became rescue request {req['trackingId']} in the normal queue and was dispatched")

rotated = ok(client.post(f"/api/uav/drones/{drone_id}/rotate-key", headers=ADMIN))
assert client.post("/api/uav/detections", headers=DRONE, json={
    "timestamp": "2026-01-01T00:00:00Z", "latitude": 25, "longitude": 91, "detection_type": "animal", "confidence": 0.5}).status_code == 401
NEW_DRONE = {"X-Drone-Id": "SUN-UAV-02", "X-Drone-Token": rotated["apiKey"]}
for _ in range(29):
    ok(client.post("/api/uav/detections", headers=NEW_DRONE, json={
        "timestamp": "2026-01-01T00:00:00Z", "latitude": 25, "longitude": 91, "detection_type": "animal", "confidence": 0.5}), 201)
assert client.post("/api/uav/detections", headers=NEW_DRONE, json={
    "timestamp": "2026-01-01T00:00:00Z", "latitude": 25, "longitude": 91, "detection_type": "animal", "confidence": 0.5}).status_code == 429
ok(client.delete(f"/api/uav/assignments/{asg['id']}", headers=ADMIN), 204)
events = {e["eventType"] for e in ok(client.get("/api/uav/logs", params={"limit": 500}, headers=ADMIN))}
assert {"drone_registered", "drone_online", "detection", "detection_acknowledged", "rescue_request_created",
        "rescuer_assigned", "rescuer_unassigned", "drone_key_rotated"} <= events
step("key rotation locks out the old key; 30 detections/minute limit; full audit trail logged")

# ── 6. Supabase Auth tokens ──
import uuid  # noqa: E402
import jwt  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import ec  # noqa: E402

otp_module = sys.modules["services.otp_service"]  # the package re-exports an instance under the same name
project_key, attacker_key = ec.generate_private_key(ec.SECP256R1()), ec.generate_private_key(ec.SECP256R1())


class FakeJWKS:  # stands in for the project's public key endpoint
    def get_signing_key_from_jwt(self, token):
        return jwt.PyJWK.from_dict({**jwt.algorithms.ECAlgorithm.to_jwk(project_key.public_key(), as_dict=True), "alg": "ES256"})


otp_module._supabase_jwks_client = FakeJWKS()


def supabase_token(key=project_key, email="", meta=None, **extra):
    now = int(datetime.now(timezone.utc).timestamp())
    claims = {"iss": "https://test-project.supabase.co/auth/v1", "aud": "authenticated", "sub": str(uuid.uuid4()),
              "email": email, "phone": "", "user_metadata": meta or {}, "iat": now, "exp": now + 3600, **extra}
    return {"Authorization": f"Bearer {jwt.encode(claims, key, algorithm='ES256')}"}, claims["sub"]


hdr, uid = supabase_token(email="New.Volunteer@Example.org", meta={"requested_role": "fieldworker", "first_name": "Mitu"})
me = ok(client.get("/api/auth/me", headers=hdr))
assert me["id"] == uid and me["role"] == "fieldworker" and me["email"] == "new.volunteer@example.org"
ok(client.get("/api/volunteers/profile", headers=hdr))
hdr, _ = supabase_token(email="sneaky@example.org", meta={"role": "admin", "requested_role": "admin"})
assert ok(client.get("/api/auth/me", headers=hdr))["role"] == "public"
assert client.get("/api/requests", headers=hdr).status_code == 403
hdr, _ = supabase_token(email="boss@example.org")
assert ok(client.get("/api/auth/me", headers=hdr))["role"] == "admin"
ok(client.get("/api/requests", headers=hdr))
hdr, _ = supabase_token(email="nasrin.akter@redcrescent.bd")
assert ok(client.get("/api/auth/me", headers=hdr))["id"] == "usr-field-001"
for bad in [supabase_token(key=attacker_key, email="a@b.c")[0], supabase_token(email="a@b.c", aud="anon")[0],
            supabase_token(email="a@b.c", exp=1)[0]]:
    assert client.get("/api/auth/me", headers=bad).status_code == 401
step("Supabase tokens: new users created, existing linked by email, ADMIN_EMAILS -> admin, forged/expired rejected")

print("=" * 64)
print("ALL END-TO-END FLOWS PASSED")
print("=" * 64)
