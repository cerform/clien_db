-- 001_create_calendar_slots_schema.sql
-- Schema for calendar-based slot engine and bookings, for Postgres
-- NOTE: Create in a transaction and ensure proper permissions

BEGIN;

-- Calendar sources: salon & master calendars
CREATE TABLE IF NOT EXISTS calendar_sources (
    id BIGSERIAL PRIMARY KEY,
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('salon', 'master')),
    master_id UUID NULL,
    calendar_id TEXT NOT NULL,
    timezone TEXT DEFAULT 'UTC',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Normalized events (only the time boundaries and basic meta)
CREATE TABLE IF NOT EXISTS calendar_events (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES calendar_sources(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status TEXT DEFAULT 'busy', -- busy, free, blocked
    external_event_id TEXT NULL,
    last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(source_id, external_event_id)
);

-- Append-only bookings pending table (INKA initial post)
CREATE TABLE IF NOT EXISTS bookings_pending (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NULL,
    master_id UUID NULL,
    service_id UUID NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status TEXT DEFAULT 'pending', -- pending, expired, cancelled
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    expires_at TIMESTAMP WITH TIME ZONE NULL,
    locked_by VARCHAR(64) NULL,
    meta JSONB DEFAULT '{}'::JSONB
);

-- The actual confirmed bookings
CREATE TABLE IF NOT EXISTS bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pending_id UUID NULL REFERENCES bookings_pending(id),
    user_id BIGINT NULL,
    master_id UUID NULL,
    service_id UUID NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status TEXT DEFAULT 'confirmed', -- confirmed, cancelled
    calendar_event_id TEXT NULL, -- optional calendar sync id
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_by VARCHAR(64) NULL,
    meta JSONB DEFAULT '{}'::JSONB
);

-- Slot locks to prevent double booking during confirmation. Append-only: insert to create a lock, remove by TTL or action.
CREATE TABLE IF NOT EXISTS slot_locks (
    master_id UUID NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    locked_by VARCHAR(128) NOT NULL,
    locked_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    expires_at TIMESTAMP WITH TIME ZONE NULL,
    PRIMARY KEY (master_id, start_time)
);

-- Views for availability: precomputed slots view
-- NOTE: We'll later create a materialized view / jobs for precompute

COMMIT;
