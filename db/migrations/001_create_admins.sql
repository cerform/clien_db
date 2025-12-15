-- Migration: 001_create_admins.sql
-- Creates a simple admins table and inserts initial admin records.
-- Intended for PostgreSQL (Cloud SQL PostgreSQL)

-- Ensure uuid generation function exists
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS admins (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  telegram_id BIGINT UNIQUE,
  role VARCHAR(64) DEFAULT 'admin',
  email VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Seed example admin records (do not overwrite existing entries)
-- NOTE: Example admin records have been removed from migrations to avoid
-- shipping embedded credentials or personally-identifiable data in repo.
-- Create initial admin users using the administrative CLI or via a secure
-- external provisioning process (e.g. run `scripts/create_admin.py` or
-- use the web admin interface after first deploy).
