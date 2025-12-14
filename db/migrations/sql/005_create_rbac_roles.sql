-- 005_create_rbac_roles.sql
-- Create per-role database users and grant role-limited access for INKA microservices.
-- This script creates the default users (if missing) and grants table permissions.
-- For production please manage passwords via environment variables / secret manager and do not commit secrets.

BEGIN;

-- Create roles if missing (no password is set here; prefer setting via ALTER ROLE in scripts)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'inka_llm_runtime') THEN
        CREATE ROLE inka_llm_runtime NOINHERIT; -- Login and password handled via deployment
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'inka_booking_agent') THEN
        CREATE ROLE inka_booking_agent NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'inka_learning_agent') THEN
        CREATE ROLE inka_learning_agent NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'calendar_sync') THEN
        CREATE ROLE calendar_sync NOINHERIT;
    END IF;
END$$;

-- Grant minimal read access to inka_llm_runtime
GRANT SELECT ON services, masters_public, availability_view TO inka_llm_runtime;
REVOKE INSERT, UPDATE, DELETE ON bookings, calendar_events FROM inka_llm_runtime;

-- Booking agent: select availability, insert into bookings_pending and slot_locks
GRANT INSERT ON bookings_pending, slot_locks TO inka_booking_agent;
GRANT SELECT ON availability_view, calendar_events TO inka_booking_agent;

-- Learning agent: write to learning tables
GRANT SELECT, INSERT, UPDATE ON learning_rules, learning_faq, learning_style TO inka_learning_agent;

-- Calendar sync: insert/update calendar_events
GRANT INSERT, UPDATE ON calendar_events TO calendar_sync;
GRANT SELECT ON calendar_sources TO calendar_sync;

COMMIT;
