"""
Pretends to be a flying drone so the UAV monitor can be demonstrated without hardware.
It sends heartbeats (GPS + battery) and, every few beats, a "human" or "animal" detection,
exactly like the on-board software of a real drone would.

    # local backend (python main.py) with the seeded demo drone:
    python scripts/simulate_drone.py

    # a drone you registered in the UAV monitor (the key is shown once when registering):
    python scripts/simulate_drone.py --api https://shohaybackend.vercel.app --drone-id SUN-UAV-02 --token <api key>
"""
import argparse
import random
import sys
import time
from datetime import datetime, timezone

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="Shohay UAV drone simulator")
    parser.add_argument("--api", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--drone-id", default="DEMO-UAV-01", help="Registration ID of the drone")
    parser.add_argument("--token", default="local-demo-drone-key", help="Drone API key")
    parser.add_argument("--interval", type=float, default=5, help="Seconds between heartbeats")
    parser.add_argument("--detections", type=int, default=5, help="Stop after this many detections")
    parser.add_argument("--every", type=int, default=3, help="Send a detection every N heartbeats")
    parser.add_argument("--lat", type=float, default=25.0712, help="Start latitude (default: Tahirpur, Sunamganj)")
    parser.add_argument("--lng", type=float, default=91.1843, help="Start longitude")
    args = parser.parse_args()

    headers = {"X-Drone-Id": args.drone_id, "X-Drone-Token": args.token}
    lat, lng, battery = args.lat, args.lng, 100.0
    sent, beat = 0, 0

    with httpx.Client(base_url=args.api.rstrip("/"), headers=headers, timeout=15) as client:
        while sent < args.detections:
            beat += 1
            lat += random.uniform(-0.0008, 0.0008)   # drift like a drone on patrol
            lng += random.uniform(-0.0008, 0.0008)
            battery = max(5.0, battery - random.uniform(0.2, 0.8))

            res = client.post("/api/uav/drones/heartbeat",
                              json={"latitude": round(lat, 6), "longitude": round(lng, 6), "battery_pct": round(battery, 1)})
            if res.status_code == 401:
                print("Drone credentials rejected - check --drone-id and --token.")
                return 1
            print(f"heartbeat {beat}: {res.status_code} ({lat:.5f}, {lng:.5f}) battery {battery:.0f}%")

            if beat % args.every == 0:
                kind = "human" if random.random() < 0.7 else "animal"
                res = client.post("/api/uav/detections", json={
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "latitude": round(lat, 6),
                    "longitude": round(lng, 6),
                    "detection_type": kind,
                    "confidence": round(random.uniform(0.62, 0.98), 2),
                    "bounding_box": {"x": 0.4, "y": 0.35, "w": 0.12, "h": 0.25},
                })
                sent += res.status_code == 201
                print(f"  -> detection ({kind}): {res.status_code} {res.json().get('id', res.text)}")

            time.sleep(args.interval)
    print(f"Sent {sent} detections. Open the UAV Monitor in the Command Center to see them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
