-- 007_create_masters_public_view.sql
CREATE OR REPLACE VIEW masters_public AS
SELECT id, name, specialization, rating, experience_years, instagram, status
FROM masters;
