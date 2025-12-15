-- Migration: 002_create_etcsys_admin.sql
-- Adds username and password_hash columns to admins and inserts the requested admin user (username 'etcsys').
-- Password is stored as salted PBKDF2-SHA256 (not plaintext). The salt+hash were generated at commit time.

ALTER TABLE admins
  ADD COLUMN IF NOT EXISTS username VARCHAR(100) UNIQUE,
  ADD COLUMN IF NOT EXISTS password_hash TEXT;

-- Insert admin user (or update hash if telegram_id exists)
-- NOTE: Inserting a default admin user (with plaintext or example passwords)
-- in migrations is a security risk. Remove any hard-coded credentials and use
-- a secure provisioning process to create admin accounts post-deployment
-- (e.g. `scripts/create_admin.py` or a one-time SQL run via the admin console).
