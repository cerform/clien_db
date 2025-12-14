-- 006_create_services_table.sql
-- Создаёт таблицу услуг для тату-студии

CREATE TABLE IF NOT EXISTS services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    duration_min INTEGER NOT NULL DEFAULT 60,
    price_from NUMERIC(10,2) NOT NULL DEFAULT 0,
    price_to NUMERIC(10,2) NOT NULL DEFAULT 0,
    category TEXT NOT NULL DEFAULT 'tattoo',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_services_category ON services(category);
CREATE INDEX IF NOT EXISTS idx_services_active ON services(active);
