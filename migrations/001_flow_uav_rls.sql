-- ============================================================================
-- Shohay migration 001 — volunteer flow, warehouse movements, UAV module, RLS
--
-- Run ONCE on the existing Supabase database, before deploying this backend:
--   * Supabase Dashboard -> SQL Editor -> paste this file -> Run, or
--   * python scripts/migrate.py
-- Every statement is idempotent (IF NOT EXISTS), so running it twice is harmless.
-- ============================================================================
BEGIN;

-- 1. Volunteer profiles: one per user, real-time duty clock, personal declines
ALTER TABLE volunteer_profiles ADD COLUMN IF NOT EXISTS duty_status VARCHAR(20) DEFAULT 'Off Duty';
ALTER TABLE volunteer_profiles ADD COLUMN IF NOT EXISTS checked_in_at TIMESTAMP;
ALTER TABLE volunteer_profiles ADD COLUMN IF NOT EXISTS declined_assignment_ids JSON NOT NULL DEFAULT '[]';
ALTER TABLE volunteer_profiles ALTER COLUMN hours_logged TYPE DOUBLE PRECISION;

-- 2. Volunteer tasks: who accepted it and which citizen request it serves
ALTER TABLE volunteer_assignments ADD COLUMN IF NOT EXISTS assigned_volunteer_id VARCHAR(50);
ALTER TABLE volunteer_assignments ADD COLUMN IF NOT EXISTS request_id VARCHAR(50);
ALTER TABLE volunteer_assignments ADD COLUMN IF NOT EXISTS accepted_at TIMESTAMP;
ALTER TABLE volunteer_assignments ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP;
CREATE INDEX IF NOT EXISTS ix_volunteer_assignments_assigned_volunteer_id ON volunteer_assignments (assigned_volunteer_id);
CREATE INDEX IF NOT EXISTS ix_volunteer_assignments_request_id ON volunteer_assignments (request_id);
-- "Declined" used to hide a task from everyone; declines are now per volunteer.
UPDATE volunteer_assignments SET status = 'Available' WHERE status = 'Declined';

-- 3. Warehouse stock movements
CREATE TABLE IF NOT EXISTS warehouse_movements (
    id VARCHAR(50) PRIMARY KEY,
    item_id VARCHAR(50) NOT NULL,
    movement_type VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL,
    from_to VARCHAR(255) NOT NULL,
    reference VARCHAR(100),
    notes TEXT,
    actor_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS ix_warehouse_movements_item_id ON warehouse_movements (item_id);
CREATE INDEX IF NOT EXISTS ix_warehouse_movements_created_at ON warehouse_movements (created_at);

-- 4. UAV (drone) module — from the ResQTech FYDP backend
CREATE TABLE IF NOT EXISTS uav_drones (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    registration_id VARCHAR(100) NOT NULL UNIQUE,
    api_key_hash VARCHAR(64) NOT NULL,
    district VARCHAR(100),
    stream_url VARCHAR(500),
    last_heartbeat TIMESTAMP,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    battery_pct DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS ix_uav_drones_registration_id ON uav_drones (registration_id);

CREATE TABLE IF NOT EXISTS uav_detections (
    id VARCHAR(50) PRIMARY KEY,
    drone_id VARCHAR(50) NOT NULL REFERENCES uav_drones (id) ON DELETE CASCADE,
    detected_at TIMESTAMP NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    detection_type VARCHAR(20) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    bounding_box JSON,
    image_url VARCHAR(500),
    status VARCHAR(30) DEFAULT 'New',
    acknowledged_by VARCHAR(50),
    acknowledged_at TIMESTAMP,
    request_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS ix_uav_detections_drone_id ON uav_detections (drone_id);
CREATE INDEX IF NOT EXISTS ix_uav_detections_status ON uav_detections (status);
CREATE INDEX IF NOT EXISTS ix_uav_detections_created_at ON uav_detections (created_at);

CREATE TABLE IF NOT EXISTS uav_rescuer_assignments (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    drone_id VARCHAR(50) NOT NULL REFERENCES uav_drones (id) ON DELETE CASCADE,
    assigned_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'utc'),
    CONSTRAINT uq_uav_rescuer_drone UNIQUE (user_id, drone_id)
);
CREATE INDEX IF NOT EXISTS ix_uav_rescuer_assignments_user_id ON uav_rescuer_assignments (user_id);
CREATE INDEX IF NOT EXISTS ix_uav_rescuer_assignments_drone_id ON uav_rescuer_assignments (drone_id);

CREATE TABLE IF NOT EXISTS uav_logs (
    id VARCHAR(50) PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    actor_id VARCHAR(50),
    drone_id VARCHAR(50),
    detection_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS ix_uav_logs_created_at ON uav_logs (created_at);

-- 5. Row Level Security
-- Supabase exposes every public table through its REST API to anyone holding the
-- (public) anon key. With RLS on and no policies, that API returns nothing, while the
-- backend — which connects as the table owner "postgres" — keeps full access.
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE shelters ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE assistance_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE volunteer_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE volunteer_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE warehouse_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE warehouse_movements ENABLE ROW LEVEL SECURITY;
ALTER TABLE uav_drones ENABLE ROW LEVEL SECURITY;
ALTER TABLE uav_detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE uav_rescuer_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE uav_logs ENABLE ROW LEVEL SECURITY;

COMMIT;
