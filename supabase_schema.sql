-- ============================================================
-- SHOHAY BACKEND — SUPABASE POSTGRESQL SCHEMA & INITIAL DATA
-- Copy and run in: Supabase Dashboard > SQL Editor > New Query
-- ============================================================

-- 1. Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR(50) PRIMARY KEY,
    severity VARCHAR(20) NOT NULL,
    type VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    affected_areas JSONB NOT NULL DEFAULT '[]',
    issued_at VARCHAR(50) NOT NULL,
    verification_status VARCHAR(50) DEFAULT 'Unverified',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);

-- 2. Shelters Table
CREATE TABLE IF NOT EXISTS shelters (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(500) NOT NULL,
    upazila VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    occupancy INTEGER DEFAULT 0,
    capacity INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'Open',
    route_status VARCHAR(20) DEFAULT 'Route OK',
    category VARCHAR(100) NOT NULL,
    amenities JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_shelters_district ON shelters(district);
CREATE INDEX IF NOT EXISTS idx_shelters_status ON shelters(status);

-- 3. Relief Campaigns Table
CREATE TABLE IF NOT EXISTS campaigns (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    organization VARCHAR(255) NOT NULL,
    district VARCHAR(100) NOT NULL,
    coverage_areas JSONB NOT NULL DEFAULT '[]',
    target_amount DOUBLE PRECISION DEFAULT 0,
    raised_amount DOUBLE PRECISION DEFAULT 0,
    households_target INTEGER DEFAULT 0,
    households_reached INTEGER DEFAULT 0,
    verification_status VARCHAR(50) DEFAULT 'Unverified',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_campaigns_district ON campaigns(district);

-- 4. Emergency Contacts Table
CREATE TABLE IF NOT EXISTS contacts (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    district VARCHAR(100),
    phone VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    availability VARCHAR(50) NOT NULL,
    is_toll_free BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT TRUE,
    notes TEXT,
    last_verified VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_contacts_category ON contacts(category);

-- 5. Assistance Requests Table
CREATE TABLE IF NOT EXISTS assistance_requests (
    id VARCHAR(50) PRIMARY KEY,
    tracking_id VARCHAR(20) UNIQUE NOT NULL,
    types JSONB NOT NULL DEFAULT '[]',
    household_size INTEGER NOT NULL,
    vulnerable_count JSONB NOT NULL DEFAULT '{}',
    location JSONB NOT NULL DEFAULT '{}',
    contact JSONB NOT NULL DEFAULT '{}',
    notes TEXT,
    status VARCHAR(20) DEFAULT 'Pending',
    created_at VARCHAR(50) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_requests_tracking ON assistance_requests(tracking_id);
CREATE INDEX IF NOT EXISTS idx_requests_status ON assistance_requests(status);

-- 6. Volunteer Profiles Table
CREATE TABLE IF NOT EXISTS volunteer_profiles (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    district VARCHAR(100) NOT NULL,
    join_date VARCHAR(50) NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    hours_logged INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    rating DOUBLE PRECISION DEFAULT 0,
    current_assignment JSONB,
    skills JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Volunteer Assignments Table
CREATE TABLE IF NOT EXISTS volunteer_assignments (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    location VARCHAR(255) NOT NULL,
    district VARCHAR(100) NOT NULL,
    duration_hours INTEGER NOT NULL,
    team_size INTEGER NOT NULL,
    priority VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'Available',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_assignments_district ON volunteer_assignments(district);
CREATE INDEX IF NOT EXISTS idx_assignments_status ON volunteer_assignments(status);

-- 8. Warehouse Inventory Table
CREATE TABLE IF NOT EXISTS warehouse_items (
    id VARCHAR(50) PRIMARY KEY,
    sku VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    available_count INTEGER DEFAULT 0,
    unit VARCHAR(50) NOT NULL,
    reserved_count INTEGER DEFAULT 0,
    min_stock_threshold INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'OK',
    expiry_date VARCHAR(20),
    warehouse_name VARCHAR(255) NOT NULL,
    last_count_date VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_warehouse_category ON warehouse_items(category);
CREATE INDEX IF NOT EXISTS idx_warehouse_status ON warehouse_items(status);

-- 9. Users Table (Public & Fieldworker)
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(50) PRIMARY KEY,
    role VARCHAR(20) NOT NULL DEFAULT 'public',
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(50),
    email VARCHAR(255),
    avatar VARCHAR(500),
    gender VARCHAR(20),
    skills JSONB NOT NULL DEFAULT '[]',
    equipment JSONB NOT NULL DEFAULT '[]',
    nid_number VARCHAR(50),
    address VARCHAR(500),
    dob VARCHAR(50),
    experience_certificate TEXT,
    verification_status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone_number);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);


-- ============================================================
-- SEED DATA (Matches Frontend Mock Datasets 100%)
-- ============================================================

-- Alerts
INSERT INTO alerts (id, severity, type, title, description, affected_areas, issued_at, verification_status) VALUES
('alert-1', 'CRITICAL', 'Flash Flood Warning', 'Surma and Kushiyara Rivers Exceeding Danger Level by 1.2m', 'Rapid water rise expected across Sunamganj Sadar, Tahirpur, and Chhatak upazilas within next 6 hours. Low-lying settlements advised to evacuate immediately.', '["Sunamganj Sadar","Tahirpur","Chhatak","Bishwamvarpur"]', '2024-07-15 06:00', 'Government Verified'),
('alert-2', 'HIGH', 'River Level Warning', 'Jamuna River Flowing 65cm Above Danger Mark at Sirajganj Point', 'Water level continuing to rise at 3cm/hr. Inundation of riverside unions in Kazipur, Belkuchi, and Shahjadpur expected by evening.', '["Sirajganj Sadar","Kazipur","Belkuchi","Shahjadpur"]', '2024-07-15 07:30', 'Government Verified'),
('alert-3', 'MEDIUM', 'Road Closure', 'Sylhet-Sunamganj Highway Submerged at Gobindaganj Point', 'Water depth 1.5 to 2.5 feet on the carriageway. Heavy vehicles operating with caution; light vehicles and buses completely suspended.', '["Gobindaganj","Chhatak","Sunamganj highway corridor"]', '2024-07-15 08:15', 'Partner Verified'),
('alert-4', 'LOW', 'Rainfall Advisory', 'Moderate to Heavy Rainfall Forecast Across Northern Districts', 'Bangladesh Meteorological Department forecasts 50-90mm rainfall in next 24-48 hours over Rangpur and Mymensingh divisions. Flash flood risk moderate.', '["Kurigram","Gaibandha","Netrokona","Sherpur"]', '2024-07-15 05:00', 'Government Verified')
ON CONFLICT (id) DO NOTHING;

-- Shelters
INSERT INTO shelters (id, name, address, upazila, district, occupancy, capacity, status, route_status, category, amenities) VALUES
('shelter-1', 'Sunamganj Government College Shelter', 'Sunamganj Sadar, Sunamganj', 'Sunamganj Sadar', 'Sunamganj', 847, 1200, 'Open', 'Caution', 'Education Institution', '{"drinkingWater":true,"toilets":true,"womenToilets":true,"electricity":true,"generator":true,"food":true,"medicalSupport":true}'),
('shelter-2', 'Tahirpur Cyclone Shelter', 'Tahirpur, Sunamganj', 'Tahirpur', 'Sunamganj', 487, 500, 'Nearly Full', 'Blocked', 'Cyclone Shelter', '{"drinkingWater":true,"toilets":true,"womenToilets":true,"electricity":true,"generator":false,"food":true,"medicalSupport":true}'),
('shelter-3', 'Sirajganj Stadium Emergency Shelter', 'Sirajganj Sadar, Sirajganj', 'Sirajganj Sadar', 'Sirajganj', 1340, 2000, 'Open', 'Route OK', 'Sports Facility', '{"drinkingWater":true,"toilets":true,"womenToilets":true,"electricity":true,"generator":true,"food":true,"medicalSupport":true}'),
('shelter-4', 'Chhatak Model High School', 'Chhatak Municipality, Sunamganj', 'Chhatak', 'Sunamganj', 600, 600, 'Full', 'Route OK', 'School', '{"drinkingWater":true,"toilets":true,"womenToilets":false,"electricity":false,"generator":false,"food":true,"medicalSupport":false}')
ON CONFLICT (id) DO NOTHING;

-- Campaigns
INSERT INTO campaigns (id, title, organization, district, coverage_areas, target_amount, raised_amount, households_target, households_reached, verification_status) VALUES
('camp-1', 'Sunamganj Emergency Cooked Food and Clean Water Drive', 'Bidyanondo Foundation', 'Sunamganj', '["Sunamganj Sadar","Tahirpur","Bishwamvarpur"]', 2500000, 1875000, 5000, 3750, 'Partner Verified'),
('camp-2', 'Jamuna Basin Dry Food and Water Purification Tablets', 'BRAC Disaster Management', 'Sirajganj', '["Kazipur","Belkuchi","Shahjadpur"]', 4000000, 3200000, 8000, 6400, 'Government Verified')
ON CONFLICT (id) DO NOTHING;

-- Contacts
INSERT INTO contacts (id, title, category, district, phone, description, availability, is_toll_free, is_verified, last_verified) VALUES
('contact-1', 'National Emergency Services', 'National Emergency', NULL, '999', '24/7 Police, Fire Service, Ambulance across Bangladesh', '24/7', TRUE, TRUE, '2024-07-15'),
('contact-2', 'Disaster Management Control Room (Ministry)', 'Disaster Management', NULL, '1090', 'Toll-free flood early warning, river water status, shelter info', '24/7', TRUE, TRUE, '2024-07-15'),
('contact-3', 'Sunamganj District Control Room', 'District Control Room', 'Sunamganj', '01713-000001', 'DC Office flood emergency cell for Sunamganj', '24/7', FALSE, TRUE, '2024-07-14')
ON CONFLICT (id) DO NOTHING;

-- Volunteer Assignments
INSERT INTO volunteer_assignments (id, title, location, district, duration_hours, team_size, priority, status) VALUES
('assign-1', 'Food Distribution - Sunamganj Sadar', 'Sunamganj Sadar', 'Sunamganj', 4, 5, 'high', 'Available'),
('assign-2', 'Boat Rescue Support - Tahirpur', 'Tahirpur', 'Sunamganj', 6, 4, 'critical', 'Available'),
('assign-3', 'Shelter Registration Desk - Sirajganj', 'Sirajganj Sadar', 'Sirajganj', 8, 3, 'medium', 'Available')
ON CONFLICT (id) DO NOTHING;

-- Volunteer Profile
INSERT INTO volunteer_profiles (id, name, code, district, join_date, is_available, hours_logged, tasks_completed, rating, current_assignment, skills) VALUES
('vol-1', 'Demo Volunteer', 'VOL-2024-DEMO', 'Sunamganj', '12 July 2024', TRUE, 24, 7, 4.8, '{"id":"assign-active","title":"Food Distribution - Sunamganj College Shelter","location":"Sunamganj Sadar","district":"Sunamganj","durationHours":4,"teamSize":5,"priority":"high","status":"In Progress"}', '["Food Distribution","Administration","Psychosocial Support"]')
ON CONFLICT (id) DO NOTHING;

-- Warehouse Items
INSERT INTO warehouse_items (id, sku, name, category, available_count, unit, reserved_count, min_stock_threshold, status, expiry_date, warehouse_name, last_count_date) VALUES
('item-1', 'WTR-1000', 'Drinking Water 5L Jerrycan', 'Water', 450, 'Bottles', 120, 500, 'LOW', '2025-06-30', 'Sylhet Central Depot', '2024-07-14'),
('item-2', 'MED-2001', 'Water Purification Tablets (Pack 50)', 'Medicine', 2800, 'Packs', 400, 1000, 'OK', '2025-12-31', 'Sylhet Central Depot', '2024-07-14'),
('item-3', 'FOD-3001', 'Emergency Dry Ration Kit (7-day)', 'Food', 320, 'Kits', 300, 400, 'CAUTION', '2024-10-15', 'Sunamganj Field Hub', '2024-07-15')
ON CONFLICT (id) DO NOTHING;

-- Pre-existing Tracked Request
INSERT INTO assistance_requests (id, tracking_id, types, household_size, vulnerable_count, location, contact, notes, status, created_at) VALUES
('req-1', 'SHY-2024-89211', '["rescue","water"]', 5, '{"children":2,"elderly":1,"pregnant":0,"disabled":0}', '{"district":"Sunamganj","upazila":"Sunamganj Sadar","union":"Jahangirnagar","address":"Village Nabinagar, Ward 3","landmark":"Near primary school","gpsCoords":"25.0657, 91.4073"}', '{"name":"Rahim Uddin","phone":"01712345678","altPhone":"01912345678","isAnonymous":false}', 'Water rising rapidly on ground floor.', 'In Progress', '2024-07-15 08:30')
ON CONFLICT (id) DO NOTHING;

-- Seed Users (Public & Fieldworker)
INSERT INTO users (id, role, first_name, last_name, phone_number, email, avatar, gender, skills, equipment, nid_number, address, dob, experience_certificate, verification_status) VALUES
('usr-public-001', 'public', 'Rahim', 'Ahmed', '01712345678', 'rahim.ahmed@example.com', 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=200&q=80', 'Male', '["First Aid & CPR", "Food & Relief Distribution", "Bicycle Logistics"]', '["Life Jackets & Buoys", "First Aid Medical Kit"]', NULL, NULL, NULL, NULL, 'Verified'),
('usr-field-001', 'fieldworker', 'Nasrin', 'Akter', '01812345678', 'nasrin.akter@redcrescent.bd', 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=200&q=80', 'Female', '["Boat Operation & Navigation", "Search & Rescue", "Water Safety Training"]', '["Engine Boat / Speedboat", "Ropes, Harnesses & Carabiners", "Megaphone & VHF Two-Way Radios"]', '19948291827361928', 'Holding 42, Ward 4, Sunamganj Sadar, Sunamganj', '1994-08-22', 'https://example.com/certificates/nasrin_rescue_diver_2023.pdf', 'Verified')
ON CONFLICT (id) DO NOTHING;

