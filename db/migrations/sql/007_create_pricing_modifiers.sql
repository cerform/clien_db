-- 007_create_pricing_modifiers.sql
-- Создаёт таблицы для хранения модификаторов ценообразования (наценки / скидки / фикс. сборы)

CREATE TABLE IF NOT EXISTS pricing_modifiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('percent','fixed')),
    value NUMERIC(10,2) NOT NULL DEFAULT 0,
    description TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS service_pricing_modifiers (
    service_id UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    modifier_id UUID NOT NULL REFERENCES pricing_modifiers(id) ON DELETE CASCADE,
    default_applies BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (service_id, modifier_id)
);

CREATE INDEX IF NOT EXISTS idx_pricing_modifiers_code ON pricing_modifiers(code);
CREATE INDEX IF NOT EXISTS idx_service_pricing_modifiers_service ON service_pricing_modifiers(service_id);
