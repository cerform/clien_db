-- 002_create_busy_intervals_view.sql
BEGIN;

-- Busy intervals view that merges calendar events + confirmed bookings + pending bookings

-- Ensure 'start_time'/'end_time' columns exist on bookings/bookings_pending for compatibility
ALTER TABLE IF EXISTS bookings ADD COLUMN IF NOT EXISTS start_time TIMESTAMP WITH TIME ZONE;
ALTER TABLE IF EXISTS bookings ADD COLUMN IF NOT EXISTS end_time TIMESTAMP WITH TIME ZONE;
DO $$
BEGIN
	IF EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'bookings' AND column_name = 'datetime_start') THEN
		EXECUTE 'UPDATE bookings SET start_time = datetime_start WHERE start_time IS NULL AND (datetime_start IS NOT NULL)';
	END IF;
	IF EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'bookings' AND column_name = 'datetime_end') THEN
		EXECUTE 'UPDATE bookings SET end_time = datetime_end WHERE end_time IS NULL AND (datetime_end IS NOT NULL)';
	END IF;
END $$;

ALTER TABLE IF EXISTS bookings_pending ADD COLUMN IF NOT EXISTS start_time TIMESTAMP WITH TIME ZONE;
ALTER TABLE IF EXISTS bookings_pending ADD COLUMN IF NOT EXISTS end_time TIMESTAMP WITH TIME ZONE;
DO $$
BEGIN
	IF EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'bookings_pending' AND column_name = 'datetime_start') THEN
		EXECUTE 'UPDATE bookings_pending SET start_time = datetime_start WHERE start_time IS NULL AND (datetime_start IS NOT NULL)';
	END IF;
	IF EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'bookings_pending' AND column_name = 'datetime_end') THEN
		EXECUTE 'UPDATE bookings_pending SET end_time = datetime_end WHERE end_time IS NULL AND (datetime_end IS NOT NULL)';
	END IF;
END $$;

CREATE OR REPLACE VIEW calendar_busy_intervals AS
SELECT cs.master_id, ce.start_time, ce.end_time, 'calendar_event' AS source
FROM calendar_events ce
JOIN calendar_sources cs ON cs.id = ce.source_id
WHERE ce.status = 'busy'

UNION ALL

-- bookings table historically used either 'start_time'/'end_time' or 'datetime_start'/'datetime_end'.
-- Use COALESCE to support both schemas so migration works on different environments.
SELECT b.master_id, b.start_time, b.end_time, 'booking' AS source
FROM bookings b
WHERE b.status = 'confirmed'

UNION ALL

SELECT p.master_id, p.start_time, p.end_time, 'pending' AS source
FROM bookings_pending p
WHERE p.status = 'pending' AND (p.expires_at IS NULL OR p.expires_at > now())

ORDER BY master_id, start_time;

COMMIT;
