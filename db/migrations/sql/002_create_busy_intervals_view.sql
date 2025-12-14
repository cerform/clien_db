-- 002_create_busy_intervals_view.sql
BEGIN;

-- Busy intervals view that merges calendar events + confirmed bookings + pending bookings
CREATE OR REPLACE VIEW calendar_busy_intervals AS
SELECT cs.master_id, ce.start_time, ce.end_time, 'calendar_event' AS source
FROM calendar_events ce
JOIN calendar_sources cs ON cs.id = ce.source_id
WHERE ce.status = 'busy'

UNION ALL

SELECT b.master_id, b.start_time, b.end_time, 'booking' AS source
FROM bookings b
WHERE b.status = 'confirmed'

UNION ALL

SELECT p.master_id, p.start_time, p.end_time, 'pending' AS source
FROM bookings_pending p
WHERE p.status = 'pending' AND (p.expires_at IS NULL OR p.expires_at > now())

ORDER BY master_id, start_time;

COMMIT;
