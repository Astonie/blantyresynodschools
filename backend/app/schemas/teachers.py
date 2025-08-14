from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel


class TeacherCreate(BaseModel):
    email: str
    full_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    hire_date: Optional[date] = None
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    salary: Optional[float] = None


class TeacherUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    hire_date: Optional[date] = None
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    salary: Optional[float] = None
    is_active: Optional[bool] = None


class TeacherRead(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    address: Optional[str]
    date_of_birth: Optional[date]
    hire_date: Optional[date]
    qualification: Optional[str]
    specialization: Optional[str]
    salary: Optional[float]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeacherAssignmentCreate(BaseModel):
    teacher_id: int
    class_id: int
    subject_id: int
    academic_year: str
    is_primary: bool = False


class TeacherAssignmentRead(BaseModel):
    id: int
    teacher_id: int
    class_id: int
    subject_id: int
    academic_year: str
    is_primary: bool
    created_at: datetime
    teacher_name: str
    class_name: str
    subject_name: str

    class Config:
        from_attributes = True


class TeacherPerformanceCreate(BaseModel):
    teacher_id: int
    academic_year: str
    term: str
    evaluation_date: date
    teaching_effectiveness: Optional[int] = None  # 1-5 scale
    classroom_management: Optional[int] = None
    student_engagement: Optional[int] = None
    lesson_planning: Optional[int] = None
    professional_development: Optional[int] = None
    overall_rating: Optional[int] = None
    comments: Optional[str] = None
    evaluator_id: int


class TeacherPerformanceRead(BaseModel):
    id: int
    teacher_id: int
    academic_year: str
    term: str
    evaluation_date: date
    teaching_effectiveness: Optional[int]
    classroom_management: Optional[int]
    student_engagement: Optional[int]
    lesson_planning: Optional[int]
    professional_development: Optional[int]
    overall_rating: Optional[int]
    comments: Optional[str]
    evaluator_id: int
    created_at: datetime
    teacher_name: str
    evaluator_name: str

    class Config:
        from_attributes = True


class TeacherDashboard(BaseModel):
    teacher_id: int
    teacher_name: str
    total_classes: int
    total_students: int
    subjects_taught: List[str]
    current_assignments: List[TeacherAssignmentRead]
    recent_performance: Optional[TeacherPerformanceRead]
    attendance_rate: Optional[float]  # Percentage of classes attended
