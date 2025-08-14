from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel


# Class schemas
class ClassCreate(BaseModel):
    name: str
    grade_level: Optional[str] = None
    capacity: Optional[int] = 40
    teacher_id: Optional[int] = None
    academic_year: str


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    grade_level: Optional[str] = None
    capacity: Optional[int] = None
    teacher_id: Optional[int] = None
    academic_year: Optional[str] = None


class ClassRead(BaseModel):
    id: int
    name: str
    grade_level: Optional[str]
    capacity: int
    teacher_id: Optional[int]
    academic_year: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Subject schemas
class SubjectCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None


class SubjectRead(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Class-Subject Assignment
class ClassSubjectCreate(BaseModel):
    class_id: int
    subject_id: int
    teacher_id: Optional[int] = None


class ClassSubjectRead(BaseModel):
    id: int
    class_id: int
    subject_id: int
    teacher_id: Optional[int]
    class_name: str
    subject_name: str
    subject_code: str

    class Config:
        from_attributes = True


# Attendance schemas
class AttendanceCreate(BaseModel):
    student_id: int
    class_id: int
    date: date
    status: str = "present"
    notes: Optional[str] = None


class AttendanceUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class AttendanceRead(BaseModel):
    id: int
    student_id: int
    class_id: int
    date: date
    status: str
    notes: Optional[str]
    recorded_by: Optional[int]
    created_at: Optional[datetime] = None
    student_name: str
    class_name: str

    class Config:
        from_attributes = True


# Academic Records schemas
class AcademicRecordCreate(BaseModel):
    student_id: int
    subject_id: int
    class_id: int
    term: str
    academic_year: str
    score: Optional[float] = None
    ca_score: Optional[float] = None
    exam_score: Optional[float] = None
    grade: Optional[str] = None
    remarks: Optional[str] = None


class AcademicRecordUpdate(BaseModel):
    score: Optional[float] = None
    ca_score: Optional[float] = None
    exam_score: Optional[float] = None
    grade: Optional[str] = None
    remarks: Optional[str] = None


class AcademicRecordRead(BaseModel):
    id: int
    student_id: int
    subject_id: int
    class_id: int
    term: str
    academic_year: str
    score: Optional[float] = None
    ca_score: Optional[float] = None
    exam_score: Optional[float] = None
    overall_score: Optional[float] = None
    grade: Optional[str]
    remarks: Optional[str]
    created_at: datetime
    updated_at: datetime
    student_name: str
    subject_name: str
    class_name: str

    class Config:
        from_attributes = True


# Bulk operations
class BulkAttendanceCreate(BaseModel):
    class_id: int
    date: date
    attendance_records: List[AttendanceCreate]


class StudentAcademicSummary(BaseModel):
    student_id: int
    student_name: str
    class_name: Optional[str] = None
    term: str
    academic_year: str
    subjects: List[AcademicRecordRead]
    average_score: Optional[float]
    total_subjects: int


# Exam Schedule schemas
class ExamScheduleCreate(BaseModel):
    title: str
    subject_id: int
    class_id: int
    exam_date: date
    start_time: str
    duration: int  # in minutes
    total_marks: int


class ExamScheduleUpdate(BaseModel):
    title: Optional[str] = None
    subject_id: Optional[int] = None
    class_id: Optional[int] = None
    exam_date: Optional[date] = None
    start_time: Optional[str] = None
    duration: Optional[int] = None
    total_marks: Optional[int] = None


class ExamScheduleRead(BaseModel):
    id: int
    title: str
    subject_id: int
    class_id: int
    exam_date: date
    start_time: str
    duration: int
    total_marks: int
    created_at: datetime
    updated_at: datetime
    subject_name: str
    class_name: str

    class Config:
        from_attributes = True
