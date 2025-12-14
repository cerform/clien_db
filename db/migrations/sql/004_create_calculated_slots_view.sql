-- 004_create_calculated_slots_view.sql
-- Create a table for calculated slots and a materialized view to read them fast

BEGIN;

-- Table for calculated slots (materialized or directly populated by job)
CREATE TABLE IF NOT EXISTS calculated_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    master_id UUID NOT NULL,
    slot_start TIMESTAMP WITH TIME ZONE NOT NULL,
    slot_end TIMESTAMP WITH TIME ZONE NOT NULL,
    slot_id TEXT NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(master_id, slot_start)
);

-- Materialized view for quick availability reads (for usage by INKA)
CREATE MATERIALIZED VIEW IF NOT EXISTS availability_view AS
SELECT cs.master_id, cs.slot_start, cs.slot_end, cs.slot_id, cs.is_available
FROM calculated_slots cs
WHERE cs.is_available = true
ORDER BY cs.master_id, cs.slot_start;

-- Refresh index
CREATE INDEX IF NOT EXISTS idx_calculated_slots_master_time ON calculated_slots (master_id, slot_start, slot_end);
CREATE INDEX IF NOT EXISTS idx_availability_view_master_time ON availability_view (master_id, slot_start);

COMMIT;
