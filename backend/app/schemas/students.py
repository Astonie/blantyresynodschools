from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    admission_no: Optional[str] = None  # Will be auto-generated if not provided
    class_name: Optional[str] = None  # Changed from current_class
    parent_name: Optional[str] = None  # Added to match DB
    parent_phone: Optional[str] = None
    parent_email: Optional[EmailStr] = None
    address: Optional[str] = None
    student_number: Optional[str] = None  # Added to match DB


class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    class_name: Optional[str] = None  # Changed from current_class
    parent_name: Optional[str] = None  # Added to match DB
    parent_phone: Optional[str] = None
    parent_email: Optional[str] = None
    address: Optional[str] = None
    student_number: Optional[str] = None  # Added to match DB


class StudentRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    gender: Optional[str]
    date_of_birth: Optional[date]
    admission_no: str
    class_name: Optional[str]  # Changed from current_class
    parent_name: Optional[str]  # Added field that exists in DB
    parent_phone: Optional[str]
    parent_email: Optional[str]
    address: Optional[str]
    student_number: Optional[str]  # Added field that exists in DB
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


