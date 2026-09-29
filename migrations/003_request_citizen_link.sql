-- ============================================================================
-- Shohay migration 003 — link a request to the signed-in citizen who submitted it
--
-- Run ONCE on the existing Supabase database, before deploying this backend:
--   * Supabase Dashboard -> SQL Editor -> paste this file -> Run, or
--   * python scripts/migrate.py
-- Every statement is idempotent (IF NOT EXISTS), so running it twice is harmless.
-- ============================================================================
BEGIN;

ALTER TABLE assistance_requests ADD COLUMN IF NOT EXISTS citizen_id VARCHAR(50);
CREATE INDEX IF NOT EXISTS ix_assistance_requests_citizen_id ON assistance_requests (citizen_id);

COMMIT;
