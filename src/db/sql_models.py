from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()


class Master(Base):
    __tablename__ = 'masters'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    telegram_id = Column(String, nullable=True)
    specialization = Column(String, nullable=True)
    rating = Column(String, default='0')
    experience = Column(String, nullable=True)
    instagram = Column(String, nullable=True)
    status = Column(String, default='active')
    bio = Column(Text, nullable=True)
    calendar_id = Column(String, nullable=True)


class Service(Base):
    __tablename__ = 'services'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    duration_min = Column(Integer, default=60)
    price_from = Column(Integer, default=0)
    price_to = Column(Integer, default=0)
    category = Column(String, default='other')
    active = Column(Boolean, default=True)


class Client(Base):
    __tablename__ = 'clients'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    telegram_id = Column(String, nullable=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_visit = Column(DateTime, nullable=True)


class Booking(Base):
    __tablename__ = 'bookings'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey('clients.id'), nullable=False)
    master_id = Column(String, ForeignKey('masters.id'), nullable=False)
    service_id = Column(String, ForeignKey('services.id'), nullable=False)
    date = Column(String, nullable=False)  # YYYY-MM-DD
    time = Column(String, nullable=False)  # HH:MM
    duration_min = Column(Integer, default=60)
    price = Column(Integer, default=0)
    status = Column(String, default='pending')
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship('Client')
    master = relationship('Master')
    service = relationship('Service')


class ScheduleEntry(Base):
    __tablename__ = 'schedule'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    master_id = Column(String, ForeignKey('masters.id'), nullable=False)
    day_of_week = Column(String, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    is_working = Column(Boolean, default=True)
    break_start = Column(String, nullable=True)
    break_end = Column(String, nullable=True)
    notes = Column(Text, nullable=True)


class AuditLog(Base):
    __tablename__ = 'admin_audit_log'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow)
    admin_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    sheet = Column(String, nullable=True)
    details = Column(Text, nullable=True)


class TrainingExample(Base):
    __tablename__ = 'inka_training'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow)
    category = Column(String, nullable=True)
    user_input = Column(Text, nullable=True)
    inka_response = Column(Text, nullable=True)
    admin_correction = Column(Text, nullable=True)
    improvement = Column(String, default='no')
    tags = Column(String, nullable=True)
    status = Column(String, default='active')
