from pydantic import BaseModel
from typing import Optional

class Client(BaseModel):
    id: Optional[int] = None
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None

class Master(BaseModel):
    id: Optional[int] = None
    name: str
    specialization: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class Service(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = ''
    duration_minutes: Optional[int] = 60
    price: Optional[int] = 0
    category: Optional[str] = 'tattoo'

class Booking(BaseModel):
    id: Optional[int] = None
    client_id: Optional[int] = None
    master_id: Optional[int] = None
    service_id: Optional[int] = None
    booking_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: Optional[str] = None

class NewAdminModel(BaseModel):
    admin_id: int
    name: Optional[str] = None
