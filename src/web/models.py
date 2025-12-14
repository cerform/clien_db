from pydantic import BaseModel
from typing import Optional

class Client(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    phone: str

class Master(BaseModel):
    id: Optional[int] = None
    name: str
    specialization: str
    email: str
    phone: str

class Service(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    duration_minutes: int
    price: int
    category: str

class Booking(BaseModel):
    id: Optional[int] = None
    client_id: int
    master_id: int
    service_id: int
    booking_date: str
    start_time: str
    end_time: str
    status: str

class NewAdminModel(BaseModel):
    admin_id: int
    name: Optional[str] = None
