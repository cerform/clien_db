import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any
from src.db.sql_models import Base, Master, Service, Client, Booking, ScheduleEntry, AuditLog, TrainingExample
from src.config.config import get_config

logger = logging.getLogger(__name__)


class SQLClient:
    def __init__(self, database_url: str = None):
        config = get_config()
        self.database_url = database_url or os.getenv('DATABASE_URL') or config.google_spreadsheet_id
        # NOTE: config.google_spreadsheet_id used as a placeholder in local env when DATABASE_URL is not set
        if self.database_url is None:
            raise ValueError("DATABASE_URL must be set in environment or passed to SQLClient")

        # Create engine and session factory
        self.engine = create_engine(self.database_url, future=True)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False, future=True)

    def create_tables(self):
        try:
            Base.metadata.create_all(self.engine)
            logger.info("✅ SQL tables created (if they didn't exist)")
        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to create tables: {e}")
            raise

    def bulk_insert_masters(self, masters: List[Dict[str, Any]]):
        session = self.Session()
        try:
            for m in masters:
                row = Master(
                    id=m.get('id') or None,
                    name=m.get('name', ''),
                    phone=m.get('phone'),
                    telegram_id=m.get('telegram_id'),
                    specialization=m.get('specialization'),
                    rating=m.get('rating', '0'),
                    experience=m.get('experience'),
                    instagram=m.get('instagram'),
                    status=m.get('status', 'active'),
                    bio=m.get('bio')
                )
                session.merge(row)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting masters: {e}")
            raise
        finally:
            session.close()

    def bulk_insert_services(self, services: List[Dict[str, Any]]):
        session = self.Session()
        try:
            for s in services:
                row = Service(
                    id=s.get('id'),
                    name=s.get('name', ''),
                    description=s.get('description'),
                    duration_min=int(s.get('duration_min', 60)),
                    price_from=int(s.get('price_from', 0)),
                    price_to=int(s.get('price_to', 0)),
                    category=s.get('category', 'other'),
                    active=(s.get('active', 'TRUE') in [True, 'TRUE', 'true', 'True'])
                )
                session.merge(row)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting services: {e}")
            raise
        finally:
            session.close()

    def bulk_insert_clients(self, clients: List[Dict[str, Any]]):
        session = self.Session()
        try:
            for c in clients:
                row = Client(
                    id=c.get('id'),
                    telegram_id=c.get('telegram_id'),
                    name=c.get('name', ''),
                    phone=c.get('phone'),
                    email=c.get('email'),
                    notes=c.get('notes'),
                    created_at=c.get('created_at') or None,
                    last_visit=c.get('last_visit') or None
                )
                session.merge(row)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting clients: {e}")
            raise
        finally:
            session.close()

    def bulk_insert_bookings(self, bookings: List[Dict[str, Any]]):
        session = self.Session()
        try:
            for b in bookings:
                row = Booking(
                    id=b.get('id'),
                    client_id=b.get('client_id'),
                    master_id=b.get('master_id'),
                    service_id=b.get('service_id'),
                    date=b.get('date'),
                    time=b.get('time'),
                    duration_min=int(b.get('duration_min') or 0),
                    price=int(b.get('price') or 0),
                    status=b.get('status') or 'pending',
                    notes=b.get('notes')
                )
                session.merge(row)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting bookings: {e}")
            raise
        finally:
            session.close()

    def bulk_insert_schedule(self, schedule_rows: List[Dict[str, Any]]):
        session = self.Session()
        try:
            for s in schedule_rows:
                row = ScheduleEntry(
                    id=s.get('id'),
                    master_id=s.get('master_id'),
                    day_of_week=s.get('day_of_week'),
                    start_time=s.get('start_time'),
                    end_time=s.get('end_time'),
                    is_working=(s.get('is_working', 'true') in ['true', 'TRUE', True]),
                    break_start=s.get('break_start'),
                    break_end=s.get('break_end'),
                    notes=s.get('notes')
                )
                session.merge(row)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting schedule entries: {e}")
            raise
        finally:
            session.close()

    def bulk_insert_audit_logs(self, logs: List[Dict[str, Any]]):
        session = self.Session()
        try:
            for l in logs:
                row = AuditLog(
                    id=l.get('id'),
                    timestamp=l.get('timestamp'),
                    admin_id=l.get('admin_id'),
                    action=l.get('action'),
                    sheet=l.get('sheet'),
                    details=l.get('details')
                )
                session.merge(row)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting audit logs: {e}")
            raise
        finally:
            session.close()

    def bulk_insert_training(self, examples: List[Dict[str, Any]]):
        session = self.Session()
        try:
            for ex in examples:
                row = TrainingExample(
                    id=ex.get('id'),
                    timestamp=ex.get('timestamp'),
                    category=ex.get('category'),
                    user_input=ex.get('user_input'),
                    inka_response=ex.get('inka_response'),
                    admin_correction=ex.get('admin_correction'),
                    improvement=ex.get('improvement', 'no'),
                    tags=ex.get('tags'),
                    status=ex.get('status', 'active')
                )
                session.merge(row)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting training examples: {e}")
            raise
        finally:
            session.close()
