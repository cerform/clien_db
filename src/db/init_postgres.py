"""
Initialize PostgreSQL schema on Cloud Run startup
This runs automatically when the bot starts
"""
import os
import logging
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

def init_database():
    """Initialize PostgreSQL database with schema

    Attempts to initialize using DATABASE_URL first.
    If DATABASE_URL is not set (e.g. Cloud Run Unix socket setup),
    the function will attempt to obtain an engine from the CloudSQL client.
    """
    try:
        database_url = os.getenv("DATABASE_URL")
        engine = None
        if database_url:
            logger.info("Initializing PostgreSQL schema using DATABASE_URL...")
            engine = create_engine(database_url)
        else:
            # Try to use Cloud SQL client engine if available (Cloud Run unix socket case)
            try:
                from src.db.cloudsql_client import get_cloudsql_client
                client = get_cloudsql_client()
                engine = client.get_engine()
                logger.info("Initializing PostgreSQL schema using Cloud SQL client engine...")
            except Exception as e:
                logger.warning(f"DATABASE_URL not set and CloudSQL client not available: {e}")
                return False

        with engine.connect() as conn:
            # Clients table - matches Google Sheets structure
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS clients (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                telegram_id BIGINT UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                phone VARCHAR(50),
                email VARCHAR(255),
                notes TEXT,
                tags VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW(),
                last_visit TIMESTAMP,
                language VARCHAR(10) DEFAULT 'ru',
                preferences JSONB
            );
            CREATE INDEX IF NOT EXISTS idx_clients_telegram_id ON clients(telegram_id);
            """))

            # Masters table - matches Google Sheets structure
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS masters (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                specialization TEXT,
                rating DECIMAL(3, 2),
                experience_years INTEGER,
                instagram VARCHAR(255),
                status VARCHAR(50) DEFAULT 'active',
                telegram_id BIGINT UNIQUE,
                calendar_id VARCHAR(500),
                notes TEXT,
                phone VARCHAR(50),
                email VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_masters_status ON masters(status);
            CREATE INDEX IF NOT EXISTS idx_masters_telegram_id ON masters(telegram_id);
            """))

            # Services table - matches Google Sheets structure
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS services (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                description TEXT,
                duration_min INTEGER,
                price_from DECIMAL(10, 2),
                price_to DECIMAL(10, 2),
                category VARCHAR(100),
                active BOOLEAN DEFAULT TRUE
            );
            CREATE INDEX IF NOT EXISTS idx_services_active ON services(active);
            CREATE INDEX IF NOT EXISTS idx_services_category ON services(category);
            """))

            # Bookings table - matches Google Sheets structure
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bookings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id UUID,
                master_id UUID,
                service_id UUID,
                datetime_start TIMESTAMP NOT NULL,
                datetime_end TIMESTAMP NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                price DECIMAL(10, 2),
                comment_client TEXT,
                comment_master TEXT,
                source VARCHAR(50) DEFAULT 'telegram',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                google_event_id VARCHAR(255)
            );
            CREATE INDEX IF NOT EXISTS idx_bookings_client ON bookings(client_id);
            CREATE INDEX IF NOT EXISTS idx_bookings_master ON bookings(master_id);
            CREATE INDEX IF NOT EXISTS idx_bookings_datetime ON bookings(datetime_start);
            CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
            """))

            # Calendar slots table - matches Google Sheets structure
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS calendar (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                date DATE NOT NULL,
                master_id UUID,
                slot_start TIME NOT NULL,
                slot_end TIME NOT NULL,
                available BOOLEAN DEFAULT TRUE,
                note TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_calendar_lookup ON calendar(master_id, date, slot_start);
            CREATE INDEX IF NOT EXISTS idx_calendar_date ON calendar(date);
            """))

            # Config table - for application settings
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS config (
                key VARCHAR(100) PRIMARY KEY,
                value TEXT,
                description TEXT
            );
            """))

            # Conversations table - for AI chat history
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS conversations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id UUID,
                message TEXT NOT NULL,
                assistant_reply TEXT,
                timestamp TIMESTAMP DEFAULT NOW(),
                source VARCHAR(50) DEFAULT 'telegram'
            );
            CREATE INDEX IF NOT EXISTS idx_conversations_client ON conversations(client_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);
            """))

            # Admin messages table - already exists from CloudSQL migration
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS admin_messages (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT NOW(),
                user_id VARCHAR(32),
                username VARCHAR(64),
                message TEXT,
                category VARCHAR(64),
                data JSONB,
                inka_category VARCHAR(64),
                sheet_row INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_admin_messages_timestamp ON admin_messages(timestamp);
            CREATE INDEX IF NOT EXISTS idx_admin_messages_user_id ON admin_messages(user_id);
            CREATE INDEX IF NOT EXISTS idx_admin_messages_category ON admin_messages(category);
            """))

            conn.commit()
            logger.info("✅ PostgreSQL schema initialized successfully!")

            # Seed default services
            result = conn.execute(text("SELECT COUNT(*) as cnt FROM services"))
            count = result.fetchone()[0]
            if count == 0:
                logger.info("Seeding default services (tattoo catalog for Israel)...")
                # Practical catalog based on local ranges (₪). These are market ranges and can be
                # adjusted per master/studio. Duration is a rough estimate.
                conn.execute(text("""
                INSERT INTO services (name, description, duration_min, price_from, price_to, category, active)
                VALUES
                    ('Mini / Small tattoo (up to ~5cm)', 'Small tattoo — ориентирный размер до 5 см', 60, 300, 600, 'tattoo', TRUE),
                    ('Medium tattoo (~5–12 cm)', 'Средний размер — примерно 5–12 см', 120, 600, 1500, 'tattoo', TRUE),
                    ('Large tattoo / Major project', 'Крупный проект: рукав, спина, бедро — часто в несколько сессий', 240, 1500, 5000, 'tattoo', TRUE),
                    ('Hourly — Minimalism (per hour)', 'Почасовая ставка для минимализма', 60, 400, 700, 'hourly', TRUE),
                    ('Hourly — Black & Grey (per hour)', 'Почасовая ставка для Black & Grey', 60, 500, 800, 'hourly', TRUE),
                    ('Hourly — Traditional (per hour)', 'Почасовая ставка для Traditional', 60, 500, 900, 'hourly', TRUE),
                    ('Hourly — New School (per hour)', 'Почасовая ставка для New School', 60, 550, 1000, 'hourly', TRUE),
                    ('Hourly — Realism (per hour)', 'Почасовая ставка для Realism', 60, 600, 1200, 'hourly', TRUE),
                    ('Studio minimum (minimum charge)', 'Минимальный чек студии / минимальная стоимость', 30, 300, 300, 'policy', TRUE),
                    ('Fine-line start (small tattoos)', 'Некоторые студии: small fine-line start from ~600 ₪', 60, 600, 600, 'tattoo', TRUE),
                    ('Consultation / Project estimate', 'Оценка проекта / консультация (может быть бесплатной или платной)', 30, 0, 150, 'consultation', TRUE),
                    ('Custom sketch / Design (creditable)', 'Разработка эскиза — может быть зачёт в итоговую стоимость', 120, 0, 500, 'design', TRUE),
                    ('Deposit (booking fee)', 'Депозит за бронь времени мастера (не возвращается при late-cancel)', 0, 200, 500, 'payment', TRUE),
                    ('Touch-up (correction) — policy window', 'Коррекция: бесплатно в рамках политики, иначе оплата', 60, 0, 400, 'touch-up', TRUE),
                    ('Aftercare kit / Product', 'Aftercare набор (плёнка / кремы) — доп. продажа', 0, 50, 200, 'product', TRUE);
                """))
                conn.commit()
                logger.info("✅ Tattoo catalog services added")

            return True

    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL: {e}")
        logger.exception("Full error:")
        return False
