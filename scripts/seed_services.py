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

# Prices here are expressed in Israeli New Shekel (ILS / ₪) and reflect typical ranges in Israeli studios
SERVICES = [
    {"name": "Mini / Small tattoo (up to ~5cm)", "description": "Small tattoo — ориентирный размер до 5 см", "duration_min": 60, "price_from": 250, "price_to": 450, "category": "tattoo"},
    {"name": "Medium tattoo (~5–12 cm)", "description": "Средний размер — примерно 5–12 см", "duration_min": 120, "price_from": 450, "price_to": 1500, "category": "tattoo"},
    {"name": "Large tattoo / Major project", "description": "Крупный проект: рукав, спина, бедро — часто в несколько сессий", "duration_min": 240, "price_from": 1500, "price_to": 15000, "category": "tattoo"},
    {"name": "Hourly — Minimalism (per hour)", "description": "Почасовая ставка для минимализма", "duration_min": 60, "price_from": 250, "price_to": 450, "category": "hourly"},
    {"name": "Hourly — Black & Grey (per hour)", "description": "Почасовая ставка для Black & Grey", "duration_min": 60, "price_from": 300, "price_to": 600, "category": "hourly"},
    {"name": "Hourly — Traditional (per hour)", "description": "Почасовая ставка для Traditional", "duration_min": 60, "price_from": 300, "price_to": 700, "category": "hourly"},
    {"name": "Hourly — New School (per hour)", "description": "Почасовая ставка для New School", "duration_min": 60, "price_from": 350, "price_to": 800, "category": "hourly"},
    {"name": "Hourly — Realism (per hour)", "description": "Почасовая ставка для Realism", "duration_min": 60, "price_from": 400, "price_to": 1000, "category": "hourly"},
    {"name": "Studio minimum (minimum charge)", "description": "Минимальный чек студии / минимальная стоимость", "duration_min": 30, "price_from": 250, "price_to": 250, "category": "policy"},
    {"name": "Fine-line start (small tattoos)", "description": "Некоторые студии: small fine-line start from ~600 ₪", "duration_min": 60, "price_from": 600, "price_to": 600, "category": "tattoo"},
    {"name": "Consultation / Project estimate", "description": "Оценка проекта / консультация (может быть бесплатной или платной)", "duration_min": 30, "price_from": 0, "price_to": 150, "category": "consultation"},
    {"name": "Custom sketch / Design (creditable)", "description": "Разработка эскиза — может быть зачёт в итоговую стоимость", "duration_min": 120, "price_from": 0, "price_to": 700, "category": "design"},
    {"name": "Deposit (booking fee)", "description": "Депозит за бронь времени мастера (не возвращается при late-cancel)", "duration_min": 0, "price_from": 200, "price_to": 500, "category": "payment"},
    {"name": "Touch-up (correction) — policy window", "description": "Коррекция: бесплатно в рамках политики, иначе оплата", "duration_min": 60, "price_from": 0, "price_to": 400, "category": "touch-up"},
    {"name": "Aftercare kit / Product", "description": "Aftercare набор (плёнка / кремы) — доп. продажа", "duration_min": 0, "price_from": 40, "price_to": 200, "category": "product"},
]

# Typical real-world pricing modifiers / markups used in Israeli studios
MODIFIERS = [
    {"code": "WEEKEND_10", "name": "Weekend surcharge", "type": "percent", "value": 10, "description": "Дополнительная плата за работу в выходные (примерно +10%)"},
    {"code": "RUSH_25", "name": "Rush / Short notice surcharge", "type": "percent", "value": 25, "description": "Срочная бронь / короткие сроки — обычно +20–30%"},
    {"code": "SENIOR_30", "name": "Senior artist premium", "type": "percent", "value": 30, "description": "Наценка за работу признанного/старшего мастера (+~30%)"},
    {"code": "COLOR_15", "name": "Color surcharge", "type": "percent", "value": 15, "description": "Наценка за цветные работы (доп. время и расходники)"},
    {"code": "DEPOSIT_250", "name": "Standard deposit (non-refundable)", "type": "fixed", "value": 250, "description": "Типичный депозит за бронирование — фиксированная сумма, учитывается при оплате"},
    {"code": "SKETCH_credited", "name": "Sketch / Design fee (credited)", "type": "fixed", "value": 400, "description": "Плата за эскиз, зачитается в итоговую стоимость при оплате проекта"},
    {"code": "TRAVEL_150", "name": "Travel fee for mobile session", "type": "fixed", "value": 150, "description": "Плата за выезд мастера (фиксированная)"},
    {"code": "COVERUP_20", "name": "Cover-up complexity surcharge", "type": "percent", "value": 20, "description": "Наценка за сложное покрытие старой тату (+~20%)"},
    {"code": "LATE_CANCEL_100", "name": "Late cancel / no-show penalty", "type": "fixed", "value": 100, "description": "Штраф при отмене в последний момент или no-show (часто частичный, зависит от политики)"},
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


def upsert_modifier(conn, mod: dict):
    params = {
        'code': mod['code'],
        'name': mod['name'],
        'type': mod['type'],
        'value': mod['value'],
        'description': mod.get('description', ''),
        'active': True,
    }

    update_stmt = text(
        """
        UPDATE pricing_modifiers SET name = :name, type = :type, value = :value, description = :description, active = :active
        WHERE code = :code
        """
    )
    res = conn.execute(update_stmt, params)
    if res.rowcount == 0:
        insert_stmt = text(
            """
            INSERT INTO pricing_modifiers (code, name, type, value, description, active)
            VALUES (:code, :name, :type, :value, :description, :active)
            """
        )
        conn.execute(insert_stmt, params)
        logger.info(f"Inserted modifier: {mod['code']}")
    else:
        logger.info(f"Updated existing modifier: {mod['code']}")


def link_modifier_to_service(conn, service_name: str, modifier_code: str, default_applies: bool = False):
    # Lookup ids and upsert into service_pricing_modifiers
    svc_row = conn.execute(text("SELECT id FROM services WHERE name = :name"), {'name': service_name}).fetchone()
    mod_row = conn.execute(text("SELECT id FROM pricing_modifiers WHERE code = :code"), {'code': modifier_code}).fetchone()
    if not svc_row or not mod_row:
        logger.warning(f"Cannot link modifier {modifier_code} -> {service_name}: missing service or modifier")
        return

    params = {'service_id': svc_row[0], 'modifier_id': mod_row[0], 'default_applies': default_applies}
    # insert if not exists
    insert_stmt = text(
        """
        INSERT INTO service_pricing_modifiers (service_id, modifier_id, default_applies)
        VALUES (:service_id, :modifier_id, :default_applies)
        ON CONFLICT (service_id, modifier_id) DO UPDATE SET default_applies = EXCLUDED.default_applies
        """
    )
    conn.execute(insert_stmt, params)
    logger.info(f"Linked modifier {modifier_code} -> {service_name} (default_applies={default_applies})")


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

        # Ensure pricing_modifiers table exists (migration should be applied in production)
        try:
            conn.execute(text('SELECT 1 FROM pricing_modifiers LIMIT 1'))
            for mod in MODIFIERS:
                try:
                    upsert_modifier(conn, mod)
                except Exception as e:
                    logger.exception(f"Failed to upsert modifier {mod['code']}: {e}")

            # Example links: apply weekend surcharge to all services by default
            for svc in [s['name'] for s in SERVICES]:
                try:
                    link_modifier_to_service(conn, svc, 'WEEKEND_10', default_applies=True)
                except Exception as e:
                    logger.exception(f"Failed to link WEEKEND_10 to {svc}: {e}")

            # Link other modifiers to relevant service categories
            link_pairs = [
                ('Hourly — Minimalism (per hour)', 'SENIOR_30'),
                ('Hourly — Black & Grey (per hour)', 'SENIOR_30'),
                ('Hourly — Realism (per hour)', 'SENIOR_30'),
                ('Large tattoo / Major project', 'SENIOR_30'),
                ('Large tattoo / Major project', 'RUSH_25'),
                ('Medium tattoo (~5–12 cm)', 'COLOR_15'),
                ('Mini / Small tattoo (up to ~5cm)', 'COLOR_15'),
                ('Custom sketch / Design (creditable)', 'SKETCH_credited'),
                ('Deposit (booking fee)', 'DEPOSIT_250'),
                    ('Large tattoo / Major project', 'COVERUP_20'),
                    ('Mini / Small tattoo (up to ~5cm)', 'LATE_CANCEL_100'),
                    ('Large tattoo / Major project', 'TRAVEL_150'),
            ]
            for svc_name, mod_code in link_pairs:
                try:
                    link_modifier_to_service(conn, svc_name, mod_code, default_applies=False)
                except Exception as e:
                    logger.exception(f"Failed to link {mod_code} to {svc_name}: {e}")

        except Exception:
            logger.info('pricing_modifiers table not found, skipping modifier seeding (run migrations first)')

        conn.commit()
    logger.info('✅ Services seeding complete')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        logger.exception('Seeding failed')
        sys.exit(2)
