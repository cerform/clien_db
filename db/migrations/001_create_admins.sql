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
INSERT INTO admins (name, telegram_id, role, email) VALUES
  ('Владимир Петров', 1, 'owner', NULL)
ON CONFLICT (telegram_id) DO NOTHING;

-- You can add more records here if needed
