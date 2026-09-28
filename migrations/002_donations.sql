-- ============================================================================
-- Shohay migration 002 — donations (SSLCommerz)
--
-- Run ONCE on the existing Supabase database, before deploying this backend:
--   * Supabase Dashboard -> SQL Editor -> paste this file -> Run, or
--   * python scripts/migrate.py
-- Every statement is idempotent (IF NOT EXISTS), so running it twice is harmless.
-- ============================================================================
BEGIN;

CREATE TABLE IF NOT EXISTS donations (
    id VARCHAR(50) PRIMARY KEY,
    campaign_id VARCHAR(50) NOT NULL REFERENCES campaigns (id),
    tran_id VARCHAR(100) NOT NULL UNIQUE,
    amount DOUBLE PRECISION NOT NULL,
    currency VARCHAR(10) DEFAULT 'BDT',
    donor_name VARCHAR(255) NOT NULL,
    donor_email VARCHAR(255) NOT NULL,
    donor_phone VARCHAR(50) NOT NULL,
    return_origin VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'Pending',
    val_id VARCHAR(100),
    bank_tran_id VARCHAR(100),
    card_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'utc'),
    validated_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_donations_campaign_id ON donations (campaign_id);
CREATE INDEX IF NOT EXISTS ix_donations_tran_id ON donations (tran_id);
CREATE INDEX IF NOT EXISTS ix_donations_status ON donations (status);

-- Same reasoning as migration 001: the backend connects as table owner and is unaffected;
-- this only blocks the public Supabase REST API from reading/writing donation records directly.
ALTER TABLE donations ENABLE ROW LEVEL SECURITY;

COMMIT;
