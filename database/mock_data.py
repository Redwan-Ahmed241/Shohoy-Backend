from typing import List, Dict, Any

MOCK_ALERTS: List[Dict[str, Any]] = [
    {
        "id": "alert-1",
        "severity": "CRITICAL",
        "type": "Flash Flood Warning",
        "title": "Surma and Kushiyara Rivers Exceeding Danger Level by 1.2m",
        "description": "Rapid water rise expected across Sunamganj Sadar, Tahirpur, and Chhatak upazilas within next 6 hours. Low-lying settlements advised to evacuate immediately.",
        "affectedAreas": ["Sunamganj Sadar", "Tahirpur", "Chhatak", "Bishwamvarpur"],
        "issuedAt": "2024-07-15 06:00",
        "verificationStatus": "Government Verified"
    },
    {
        "id": "alert-2",
        "severity": "HIGH",
        "type": "River Level Warning",
        "title": "Jamuna River Flowing 65cm Above Danger Mark at Sirajganj Point",
        "description": "Water level continuing to rise at 3cm/hr. Inundation of riverside unions in Kazipur, Belkuchi, and Shahjadpur expected by evening.",
        "affectedAreas": ["Sirajganj Sadar", "Kazipur", "Belkuchi", "Shahjadpur"],
        "issuedAt": "2024-07-15 07:30",
        "verificationStatus": "Government Verified"
    },
    {
        "id": "alert-3",
        "severity": "MEDIUM",
        "type": "Road Closure",
        "title": "Sylhet-Sunamganj Highway Submerged at Gobindaganj Point",
        "description": "Water depth 1.5 to 2.5 feet on the carriageway. Heavy vehicles operating with caution; light vehicles and buses completely suspended.",
        "affectedAreas": ["Gobindaganj", "Chhatak", "Sunamganj highway corridor"],
        "issuedAt": "2024-07-15 08:15",
        "verificationStatus": "Partner Verified"
    },
    {
        "id": "alert-4",
        "severity": "LOW",
        "type": "Rainfall Advisory",
        "title": "Moderate to Heavy Rainfall Forecast Across Northern Districts",
        "description": "Bangladesh Meteorological Department forecasts 50-90mm rainfall in next 24-48 hours over Rangpur and Mymensingh divisions. Flash flood risk moderate.",
        "affectedAreas": ["Kurigram", "Gaibandha", "Netrokona", "Sherpur"],
        "issuedAt": "2024-07-15 05:00",
        "verificationStatus": "Government Verified"
    }
]

MOCK_SHELTERS: List[Dict[str, Any]] = [
    {
        "id": "shelter-1",
        "name": "Sunamganj Government College Shelter",
        "address": "Sunamganj Sadar, Sunamganj",
        "upazila": "Sunamganj Sadar",
        "district": "Sunamganj",
        "occupancy": 847,
        "capacity": 1200,
        "status": "Open",
        "routeStatus": "Caution",
        "category": "Education Institution",
        "amenities": {
            "drinkingWater": True,
            "toilets": True,
            "womenToilets": True,
            "electricity": True,
            "generator": True,
            "food": True,
            "medicalSupport": True
        }
    },
    {
        "id": "shelter-2",
        "name": "Tahirpur Cyclone Shelter",
        "address": "Tahirpur, Sunamganj",
        "upazila": "Tahirpur",
        "district": "Sunamganj",
        "occupancy": 487,
        "capacity": 500,
        "status": "Nearly Full",
        "routeStatus": "Blocked",
        "category": "Cyclone Shelter",
        "amenities": {
            "drinkingWater": True,
            "toilets": True,
            "womenToilets": True,
            "electricity": True,
            "generator": False,
            "food": True,
            "medicalSupport": True
        }
    },
    {
        "id": "shelter-3",
        "name": "Sirajganj Stadium Emergency Shelter",
        "address": "Sirajganj Sadar, Sirajganj",
        "upazila": "Sirajganj Sadar",
        "district": "Sirajganj",
        "occupancy": 1340,
        "capacity": 2000,
        "status": "Open",
        "routeStatus": "Route OK",
        "category": "Sports Facility",
        "amenities": {
            "drinkingWater": True,
            "toilets": True,
            "womenToilets": True,
            "electricity": True,
            "generator": True,
            "food": True,
            "medicalSupport": True
        }
    },
    {
        "id": "shelter-4",
        "name": "Chhatak Model High School",
        "address": "Chhatak Municipality, Sunamganj",
        "upazila": "Chhatak",
        "district": "Sunamganj",
        "occupancy": 600,
        "capacity": 600,
        "status": "Full",
        "routeStatus": "Route OK",
        "category": "School",
        "amenities": {
            "drinkingWater": True,
            "toilets": True,
            "womenToilets": False,
            "electricity": False,
            "generator": False,
            "food": True,
            "medicalSupport": False
        }
    }
]

MOCK_CAMPAIGNS: List[Dict[str, Any]] = [
    {
        "id": "camp-1",
        "title": "Sunamganj Emergency Cooked Food and Clean Water Drive",
        "organization": "Bidyanondo Foundation",
        "district": "Sunamganj",
        "coverageAreas": ["Sunamganj Sadar", "Tahirpur", "Bishwamvarpur"],
        "targetAmount": 2500000.0,
        "raisedAmount": 1875000.0,
        "householdsTarget": 5000,
        "householdsReached": 3750,
        "verificationStatus": "Partner Verified"
    },
    {
        "id": "camp-2",
        "title": "Jamuna Basin Dry Food and Water Purification Tablets",
        "organization": "BRAC Disaster Management",
        "district": "Sirajganj",
        "coverageAreas": ["Kazipur", "Belkuchi", "Shahjadpur"],
        "targetAmount": 4000000.0,
        "raisedAmount": 3200000.0,
        "householdsTarget": 8000,
        "householdsReached": 6400,
        "verificationStatus": "Government Verified"
    }
]

MOCK_CONTACTS: List[Dict[str, Any]] = [
    {
        "id": "contact-1",
        "title": "National Emergency Services",
        "category": "National Emergency",
        "phone": "999",
        "description": "24/7 Police, Fire Service, Ambulance across Bangladesh",
        "availability": "24/7",
        "isTollFree": True,
        "isVerified": True,
        "lastVerified": "2024-07-15"
    },
    {
        "id": "contact-2",
        "title": "Disaster Management Control Room (Ministry)",
        "category": "Disaster Management",
        "phone": "1090",
        "description": "Toll-free flood early warning, river water status, shelter info",
        "availability": "24/7",
        "isTollFree": True,
        "isVerified": True,
        "lastVerified": "2024-07-15"
    },
    {
        "id": "contact-3",
        "title": "Sunamganj District Control Room",
        "category": "District Control Room",
        "district": "Sunamganj",
        "phone": "01713-000001",
        "description": "DC Office flood emergency cell for Sunamganj",
        "availability": "24/7",
        "isTollFree": False,
        "isVerified": True,
        "lastVerified": "2024-07-14"
    }
]

MOCK_VOLUNTEER_ASSIGNMENTS: List[Dict[str, Any]] = [
    {
        "id": "assign-1",
        "title": "Food Distribution - Sunamganj Sadar",
        "location": "Sunamganj Sadar",
        "district": "Sunamganj",
        "durationHours": 4,
        "teamSize": 5,
        "priority": "high",
        "status": "Available"
    },
    {
        "id": "assign-2",
        "title": "Boat Rescue Support - Tahirpur",
        "location": "Tahirpur",
        "district": "Sunamganj",
        "durationHours": 6,
        "teamSize": 4,
        "priority": "critical",
        "status": "Available"
    },
    {
        "id": "assign-3",
        "title": "Shelter Registration Desk - Sirajganj",
        "location": "Sirajganj Sadar",
        "district": "Sirajganj",
        "durationHours": 8,
        "teamSize": 3,
        "priority": "medium",
        "status": "Available"
    }
]

MOCK_VOLUNTEER_PROFILE: Dict[str, Any] = {
    "id": "vol-1",
    "name": "Demo Volunteer",
    "code": "VOL-2024-DEMO",
    "district": "Sunamganj",
    "joinDate": "12 July 2024",
    "isAvailable": True,
    "hoursLogged": 24,
    "tasksCompleted": 7,
    "rating": 4.8,
    "skills": ["Food Distribution", "Administration", "Psychosocial Support"],
    "currentAssignment": {
        "id": "assign-active",
        "title": "Food Distribution - Sunamganj College Shelter",
        "location": "Sunamganj Sadar",
        "district": "Sunamganj",
        "durationHours": 4,
        "teamSize": 5,
        "priority": "high",
        "status": "In Progress"
    }
}

MOCK_WAREHOUSE_ITEMS: List[Dict[str, Any]] = [
    {
        "id": "item-1",
        "sku": "WTR-1000",
        "name": "Drinking Water 5L Jerrycan",
        "category": "Water",
        "availableCount": 450,
        "unit": "Bottles",
        "reservedCount": 120,
        "minStockThreshold": 500,
        "status": "LOW",
        "expiryDate": "2025-06-30",
        "warehouseName": "Sylhet Central Depot",
        "lastCountDate": "2024-07-14"
    },
    {
        "id": "item-2",
        "sku": "MED-2001",
        "name": "Water Purification Tablets (Pack 50)",
        "category": "Medicine",
        "availableCount": 2800,
        "unit": "Packs",
        "reservedCount": 400,
        "minStockThreshold": 1000,
        "status": "OK",
        "expiryDate": "2025-12-31",
        "warehouseName": "Sylhet Central Depot",
        "lastCountDate": "2024-07-14"
    },
    {
        "id": "item-3",
        "sku": "FOD-3001",
        "name": "Emergency Dry Ration Kit (7-day)",
        "category": "Food",
        "availableCount": 320,
        "unit": "Kits",
        "reservedCount": 300,
        "minStockThreshold": 400,
        "status": "CAUTION",
        "expiryDate": "2024-10-15",
        "warehouseName": "Sunamganj Field Hub",
        "lastCountDate": "2024-07-15"
    }
]

MOCK_REQUESTS_DB: Dict[str, Dict[str, Any]] = {
    "SHY-2024-89211": {
        "id": "req-1",
        "trackingId": "SHY-2024-89211",
        "types": ["rescue", "water"],
        "householdSize": 5,
        "vulnerableCount": {"children": 2, "elderly": 1, "pregnant": 0, "disabled": 0},
        "location": {
            "district": "Sunamganj",
            "upazila": "Sunamganj Sadar",
            "union": "Jahangirnagar",
            "address": "Village Nabinagar, Ward 3",
            "landmark": "Near primary school",
            "gpsCoords": "25.0657, 91.4073"
        },
        "contact": {
            "name": "Rahim Uddin",
            "phone": "01712345678",
            "altPhone": "01912345678",
            "isAnonymous": False
        },
        "notes": "Water rising rapidly on ground floor.",
        "status": "In Progress",
        "createdAt": "2024-07-15 08:30"
    }
}
