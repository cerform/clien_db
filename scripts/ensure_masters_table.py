#!/usr/bin/env python3
import os
import logging
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL not set; please export it or set CLOUDSQL_HOST/PORT and CLOUDSQL_USER/PASSWORD')

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    logger.info('Ensuring masters table exists and has required columns...')
    conn.execute(text('''
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
    '''))
    # Add missing columns if any (idempotent)
    for col_sql in [
        "ALTER TABLE masters ADD COLUMN IF NOT EXISTS username VARCHAR(255) UNIQUE;",
        "ALTER TABLE masters ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);",
        "ALTER TABLE masters ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'master';",
        "ALTER TABLE masters ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;",
    ]:
        try:
            conn.execute(text(col_sql))
        except Exception as e:
            logger.info(f'Could not alter masters table: {e}')

    logger.info('Masters table ensured successfully')

if __name__ == '__main__':
    print('Done')
