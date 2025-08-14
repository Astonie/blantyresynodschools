from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    admission_no: Optional[str] = None  # Will be auto-generated if not provided
    current_class: Optional[str] = None
    parent_phone: Optional[str] = None
    parent_email: Optional[EmailStr] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None


class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    current_class: Optional[str] = None
    parent_phone: Optional[str] = None
    parent_email: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    status: Optional[str] = None


class StudentRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    gender: Optional[str]
    date_of_birth: Optional[date]
    admission_no: str
    current_class: Optional[str]
    parent_phone: Optional[str]
    parent_email: Optional[str]
    address: Optional[str]
    emergency_contact: Optional[str]
    emergency_phone: Optional[str]
    enrollment_date: date
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


