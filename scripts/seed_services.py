#!/usr/bin/env python3
"""Idempotent seeding/upsert of services based on a predefined tattoo price catalog.

Usage:
  python3 scripts/seed_services.py

This script will connect using DATABASE_URL env var if present, otherwise it will try
to initialize Cloud SQL client (same as other scripts in the repo).
"""
import os
import logging
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine

try:
    from src.db.cloudsql_client import init_cloudsql_client
except Exception:
    init_cloudsql_client = None

SERVICES = [
    {"name": "Mini / Small tattoo (up to ~5cm)", "description": "Small tattoo — ориентирный размер до 5 см", "duration_min": 60, "price_from": 300, "price_to": 600, "category": "tattoo"},
    {"name": "Medium tattoo (~5–12 cm)", "description": "Средний размер — примерно 5–12 см", "duration_min": 120, "price_from": 600, "price_to": 1500, "category": "tattoo"},
    {"name": "Large tattoo / Major project", "description": "Крупный проект: рукав, спина, бедро — часто в несколько сессий", "duration_min": 240, "price_from": 1500, "price_to": 5000, "category": "tattoo"},
    {"name": "Hourly — Minimalism (per hour)", "description": "Почасовая ставка для минимализма", "duration_min": 60, "price_from": 400, "price_to": 700, "category": "hourly"},
    {"name": "Hourly — Black & Grey (per hour)", "description": "Почасовая ставка для Black & Grey", "duration_min": 60, "price_from": 500, "price_to": 800, "category": "hourly"},
    {"name": "Hourly — Traditional (per hour)", "description": "Почасовая ставка для Traditional", "duration_min": 60, "price_from": 500, "price_to": 900, "category": "hourly"},
    {"name": "Hourly — New School (per hour)", "description": "Почасовая ставка для New School", "duration_min": 60, "price_from": 550, "price_to": 1000, "category": "hourly"},
    {"name": "Hourly — Realism (per hour)", "description": "Почасовая ставка для Realism", "duration_min": 60, "price_from": 600, "price_to": 1200, "category": "hourly"},
    {"name": "Studio minimum (minimum charge)", "description": "Минимальный чек студии / минимальная стоимость", "duration_min": 30, "price_from": 300, "price_to": 300, "category": "policy"},
    {"name": "Fine-line start (small tattoos)", "description": "Некоторые студии: small fine-line start from ~600 ₪", "duration_min": 60, "price_from": 600, "price_to": 600, "category": "tattoo"},
    {"name": "Consultation / Project estimate", "description": "Оценка проекта / консультация (может быть бесплатной или платной)", "duration_min": 30, "price_from": 0, "price_to": 150, "category": "consultation"},
    {"name": "Custom sketch / Design (creditable)", "description": "Разработка эскиза — может быть зачёт в итоговую стоимость", "duration_min": 120, "price_from": 0, "price_to": 500, "category": "design"},
    {"name": "Deposit (booking fee)", "description": "Депозит за бронь времени мастера (не возвращается при late-cancel)", "duration_min": 0, "price_from": 200, "price_to": 500, "category": "payment"},
    {"name": "Touch-up (correction) — policy window", "description": "Коррекция: бесплатно в рамках политики, иначе оплата", "duration_min": 60, "price_from": 0, "price_to": 400, "category": "touch-up"},
    {"name": "Aftercare kit / Product", "description": "Aftercare набор (плёнка / кремы) — доп. продажа", "duration_min": 0, "price_from": 50, "price_to": 200, "category": "product"},
]


def get_engine():
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        logger.info('Using DATABASE_URL for seeding services')
        return create_engine(database_url)

    if init_cloudsql_client:
        logger.info('Using Cloud SQL client for seeding services')
        client = init_cloudsql_client()
        return client.get_engine()

    raise RuntimeError('No DATABASE_URL set and Cloud SQL client not available')


def upsert_service(conn, svc: dict):
    # Try to update by name, if no rows updated then insert
    params = {
        'name': svc['name'],
        'description': svc.get('description', ''),
        'duration_min': svc.get('duration_min', 60),
        'price_from': svc.get('price_from', 0),
        'price_to': svc.get('price_to', 0),
        'category': svc.get('category', 'tattoo'),
        'active': True,
    }

    update_stmt = text(
        """
        UPDATE services SET description = :description, duration_min = :duration_min,
            price_from = :price_from, price_to = :price_to, category = :category, active = :active
        WHERE name = :name
        """
    )
    res = conn.execute(update_stmt, params)
    if res.rowcount == 0:
        insert_stmt = text(
            """
            INSERT INTO services (name, description, duration_min, price_from, price_to, category, active)
            VALUES (:name, :description, :duration_min, :price_from, :price_to, :category, :active)
            """
        )
        conn.execute(insert_stmt, params)
        logger.info(f"Inserted service: {svc['name']}")
    else:
        logger.info(f"Updated existing service: {svc['name']}")


def main():
    engine = get_engine()
    with engine.connect() as conn:
        # Ensure services table exists
        conn.execute(text('SELECT 1 FROM services LIMIT 1'))

        for svc in SERVICES:
            try:
                upsert_service(conn, svc)
            except Exception as e:
                logger.exception(f"Failed to upsert service {svc['name']}: {e}")

        conn.commit()
    logger.info('✅ Services seeding complete')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        logger.exception('Seeding failed')
        sys.exit(2)
