-- Migration: 002_create_etcsys_admin.sql
-- Adds username and password_hash columns to admins and inserts the requested admin user (username 'etcsys').
-- Password is stored as salted PBKDF2-SHA256 (not plaintext). The salt+hash were generated at commit time.

ALTER TABLE admins
  ADD COLUMN IF NOT EXISTS username VARCHAR(100) UNIQUE,
  ADD COLUMN IF NOT EXISTS password_hash TEXT;

-- Insert admin user (or update hash if telegram_id exists)
INSERT INTO admins (name, telegram_id, role, username, password_hash) VALUES
  ('etcsys', 438407739, 'admin', 'etcsys', 'pbkdf2_sha256$150000$670be8c9e32b34f061967214c81a525b$62843a42c1adf0aec6a8a1887ee41b3b8fcda2752e3be100b46edd3793dd94c6')
ON CONFLICT (telegram_id) DO UPDATE SET username = EXCLUDED.username, password_hash = EXCLUDED.password_hash;
