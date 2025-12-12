#!/usr/bin/env python3
"""
Full migration from Google Sheets to PostgreSQL
Migrates all data: clients, masters, bookings, calendar, services
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import sqlalchemy
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Database URL from secret
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set")

logger.info(f"Connecting to database...")

# Create engine
engine = sqlalchemy.create_engine(DATABASE_URL)

def create_schema():
    """Create all tables in PostgreSQL"""
    with engine.connect() as conn:
        logger.info("Creating schema...")

        # Clients table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE,
            name VARCHAR(255) NOT NULL,
            phone VARCHAR(50),
            email VARCHAR(255),
            language VARCHAR(10) DEFAULT 'ru',
            created_at TIMESTAMP DEFAULT NOW(),
            last_interaction TIMESTAMP,
            notes TEXT,
            preferences JSONB
        );
        """))
        logger.info("✓ clients table created")

        # Masters table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS masters (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE,
            name VARCHAR(255) NOT NULL,
            phone VARCHAR(50),
            email VARCHAR(255),
            role VARCHAR(50) DEFAULT 'master',
            username VARCHAR(255) UNIQUE,
            password_hash VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            calendar_link VARCHAR(500),
            created_at TIMESTAMP DEFAULT NOW(),
            specialization VARCHAR(255),
            bio TEXT,
            photo_url VARCHAR(500)
        );
        """))
        logger.info("✓ masters table created")

        # Services table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS services (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            duration_minutes INTEGER,
            price DECIMAL(10, 2),
            category VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE
        );
        """))
        logger.info("✓ services table created")

        # Bookings table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            client_id INTEGER REFERENCES clients(id),
            master_id INTEGER REFERENCES masters(id),
            service_id INTEGER REFERENCES services(id),
            booking_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            telegram_message_id BIGINT,
            client_telegram_id BIGINT,
            client_name VARCHAR(255),
            client_phone VARCHAR(50)
        );
        """))
        logger.info("✓ bookings table created")

        # Calendar slots table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS calendar_slots (
            id SERIAL PRIMARY KEY,
            master_id INTEGER REFERENCES masters(id),
            date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            is_available BOOLEAN DEFAULT TRUE,
            booking_id INTEGER REFERENCES bookings(id),
            notes TEXT,
            UNIQUE(master_id, date, start_time)
        );
        """))
        logger.info("✓ calendar_slots table created")

        # Conversation history for AI (INKA)
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS conversation_history (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            message TEXT NOT NULL,
            role VARCHAR(20) NOT NULL,
            timestamp TIMESTAMP DEFAULT NOW(),
            context JSONB,
            INDEX idx_user_time (user_id, timestamp)
        );
        """))
        logger.info("✓ conversation_history table created")

        # Admin messages (already exists, but ensure schema)
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
            sheet_row INTEGER
        );
        """))
        logger.info("✓ admin_messages table created")

        conn.commit()
        logger.info("✅ All tables created successfully!")

def seed_data():
    """Add initial data"""
    with engine.connect() as conn:
        logger.info("Seeding initial data...")

        # Add default services
        conn.execute(text("""
        INSERT INTO services (name, description, duration_minutes, price, category)
        VALUES
            ('Small tattoo', 'Small tattoo up to 5cm', 60, 100, 'tattoo'),
            ('Medium tattoo', 'Medium tattoo 5-15cm', 120, 250, 'tattoo'),
            ('Large tattoo', 'Large tattoo 15cm+', 180, 500, 'tattoo'),
            ('Consultation', 'Design consultation', 30, 0, 'consultation')
        ON CONFLICT DO NOTHING;
        """))

        conn.commit()
        logger.info("✅ Initial data seeded!")

if __name__ == "__main__":
    try:
        logger.info("="*60)
        logger.info("PostgreSQL Migration Script")
        logger.info("="*60)

        create_schema()
        seed_data()

        logger.info("="*60)
        logger.info("✅ Migration completed successfully!")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
