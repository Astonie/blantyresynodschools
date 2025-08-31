from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import date, datetime

from app.tenancy.deps import get_tenant_db
from app.api.deps import get_current_user_id, require_roles
from pydantic import BaseModel

router = APIRouter()

# Pydantic models for parent API responses
class SubjectGrade(BaseModel):
    subject_name: str
    ca_score: float
    exam_score: float
    overall_score: float
    grade: Optional[str] = None
    grade_points: float
    is_finalized: bool

class StudentReportCard(BaseModel):
    student_id: int
    first_name: str
    last_name: str
    admission_no: str
    class_name: str
    academic_year: str
    term: str
    subjects: List[SubjectGrade]
    total_subjects: int
    total_points: float
    gpa: float
    overall_gpa: float  # Alias for gpa to match frontend
    term_average: float  # Term average percentage
    class_position: Optional[int] = None  # Student's position in class
    total_students_in_class: Optional[int] = None  # Total students in class
    attendance_percentage: Optional[float] = None  # Attendance percentage

class ChildInfo(BaseModel):
    id: int
    first_name: str
    last_name: str
    admission_no: str
    class_name: str

@router.get("/children", response_model=List[ChildInfo], dependencies=[Depends(require_roles(["Parent"]))])
def get_parent_children(
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get list of children for the authenticated parent"""
    
    children = db.execute(text("""
        SELECT s.id, s.first_name, s.last_name, s.admission_no, c.name as class_name
        FROM parent_students ps
        JOIN students s ON ps.student_id = s.id
        LEFT JOIN classes c ON s.class_name = c.name
        WHERE ps.parent_user_id = :parent_id
        ORDER BY s.first_name, s.last_name
    """), {"parent_id": user_id}).mappings().all()
    
    if not children:
        raise HTTPException(status_code=404, detail="No children found for this parent")
    
    return [ChildInfo(**dict(child)) for child in children]


@router.get("/children/{student_id}/report-card", response_model=StudentReportCard, dependencies=[Depends(require_roles(["Parent"]))])
def get_child_report_card(
    student_id: int,
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id),
    academic_year: Optional[str] = "2025",
    term: Optional[str] = "Term 1"
):
    """Get report card for a specific child"""
    
    # Verify this parent has access to this child
    parent_child_check = db.execute(text("""
        SELECT 1 FROM parent_students ps
        WHERE ps.parent_user_id = :parent_id AND ps.student_id = :student_id
    """), {"parent_id": user_id, "student_id": student_id}).scalar()
    
    if not parent_child_check:
        raise HTTPException(status_code=403, detail="Access denied to this child's records")
    
    # Get student basic info
    student_info = db.execute(text("""
        SELECT s.id, s.first_name, s.last_name, s.admission_no, c.name as class_name
        FROM students s
        LEFT JOIN classes c ON s.class_name = c.name
        WHERE s.id = :student_id
    """), {"student_id": student_id}).mappings().first()
    
    if not student_info:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get academic records for report card
    academic_records = db.execute(text("""
        SELECT 
            CASE ar.subject_id 
                WHEN 1 THEN 'English Language'
                WHEN 2 THEN 'Mathematics'
                WHEN 3 THEN 'General Science'
                ELSE 'Unknown Subject'
            END as subject_name,
            ar.ca_score, ar.exam_score,
            ar.overall_score, ar.grade, ar.grade_points, ar.is_finalized,
            ar.academic_year, ar.term
        FROM academic_records ar
        WHERE ar.student_id = :student_id 
        AND ar.academic_year = :year AND ar.term = :term
        AND ar.is_finalized = true
        ORDER BY ar.subject_id
    """), {
        "student_id": student_id,
        "year": academic_year,
        "term": term
    }).mappings().all()
    
    if not academic_records:
        raise HTTPException(
            status_code=404, 
            detail=f"No finalized grades found for {academic_year} {term}"
        )
    
    # Calculate totals
    subjects = [SubjectGrade(**dict(record)) for record in academic_records]
    total_subjects = len(subjects)
    total_points = sum(subject.grade_points for subject in subjects)
    gpa = total_points / total_subjects if total_subjects > 0 else 0.0
    
    # Calculate term average percentage
    term_average = sum(subject.overall_score for subject in subjects) / total_subjects if total_subjects > 0 else 0.0
    
    # Calculate class position
    class_position = None
    total_students_in_class = None
    
    try:
        # Get class averages for all students in the same class for ranking
        class_rankings = db.execute(text("""
            WITH student_averages AS (
                SELECT 
                    ar.student_id,
                    AVG(ar.overall_score) as avg_score
                FROM academic_records ar
                JOIN students s ON ar.student_id = s.id
                WHERE s.class_name = :class_name 
                AND ar.academic_year = :year 
                AND ar.term = :term
                AND ar.is_finalized = true
                GROUP BY ar.student_id
            )
            SELECT 
                student_id,
                avg_score,
                ROW_NUMBER() OVER (ORDER BY avg_score DESC) as position,
                COUNT(*) OVER () as total_students
            FROM student_averages
            ORDER BY avg_score DESC
        """), {
            "class_name": student_info['class_name'],
            "year": academic_year,
            "term": term
        }).mappings().all()
        
        for ranking in class_rankings:
            if ranking['student_id'] == student_id:
                class_position = ranking['position']
                total_students_in_class = ranking['total_students']
                break
                
    except Exception as e:
        print(f"Error calculating class position: {e}")
    
    return StudentReportCard(
        student_id=student_info['id'],
        first_name=student_info['first_name'],
        last_name=student_info['last_name'],
        admission_no=student_info['admission_no'],
        class_name=student_info['class_name'] or "Not Assigned",
        academic_year=academic_year,
        term=term,
        subjects=subjects,
        total_subjects=total_subjects,
        total_points=total_points,
        gpa=round(gpa, 2),
        overall_gpa=round(gpa, 2),  # Same as gpa for frontend compatibility
        term_average=round(term_average, 1),
        class_position=class_position,
        total_students_in_class=total_students_in_class,
        attendance_percentage=85.0  # Placeholder - would come from attendance system
    )


@router.get("/children/{student_id}/grades", dependencies=[Depends(require_roles(["Parent"]))])
def get_child_grades_history(
    student_id: int,
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id),
    academic_year: Optional[str] = None,
    term: Optional[str] = None
):
    """Get grades history for a specific child"""
    
    # Verify parent access
    parent_child_check = db.execute(text("""
        SELECT 1 FROM parent_students ps
        WHERE ps.parent_user_id = :parent_id AND ps.student_id = :student_id
    """), {"parent_id": user_id, "student_id": student_id}).scalar()
    
    if not parent_child_check:
        raise HTTPException(status_code=403, detail="Access denied to this child's records")
    
    # Build query with optional filters
    query = """
        SELECT 
            ar.academic_year, ar.term, subj.name as subject_name,
            ar.ca_score, ar.exam_score, ar.overall_score, ar.grade,
            ar.grade_points, ar.is_finalized, ar.created_at
        FROM academic_records ar
        JOIN subjects subj ON ar.subject_id = subj.id
        WHERE ar.student_id = :student_id
    """
    
    params = {"student_id": student_id}
    
    if academic_year:
        query += " AND ar.academic_year = :year"
        params["year"] = academic_year
        
    if term:
        query += " AND ar.term = :term"
        params["term"] = term
        
    query += " ORDER BY ar.academic_year DESC, ar.term DESC, subj.name"
    
    grades = db.execute(text(query), params).mappings().all()
    
    return [dict(grade) for grade in grades]


@router.get("/children/{student_id}/attendance", dependencies=[Depends(require_roles(["Parent"]))])
def get_child_attendance(
    student_id: int,
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """Get attendance records for a specific child"""
    
    # Verify parent access
    parent_child_check = db.execute(text("""
        SELECT 1 FROM parent_students ps
        WHERE ps.parent_user_id = :parent_id AND ps.student_id = :student_id
    """), {"parent_id": user_id, "student_id": student_id}).scalar()
    
    if not parent_child_check:
        raise HTTPException(status_code=403, detail="Access denied to this child's records")
    
    # Build attendance query
    query = """
        SELECT 
            a.date, a.status, c.name as class_name, a.created_at
        FROM attendance a
        LEFT JOIN classes c ON a.class_id = c.id
        WHERE a.student_id = :student_id
    """
    
    params = {"student_id": student_id}
    
    if start_date:
        query += " AND a.date >= :start_date"
        params["start_date"] = start_date
        
    if end_date:
        query += " AND a.date <= :end_date"
        params["end_date"] = end_date
        
    query += " ORDER BY a.date DESC"
    
    attendance = db.execute(text(query), params).mappings().all()
    
    # Calculate attendance statistics
    total_days = len(attendance)
    present_days = len([a for a in attendance if a['status'] == 'present'])
    attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
    
    return {
        "attendance_records": [dict(record) for record in attendance],
        "statistics": {
            "total_days": total_days,
            "present_days": present_days,
            "absent_days": total_days - present_days,
            "attendance_rate": round(attendance_rate, 2)
        }
    }


@router.get("/dashboard", dependencies=[Depends(require_roles(["Parent"]))])
def get_parent_dashboard(
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get parent dashboard summary"""
    
    # Get children count
    children_count = db.execute(text("""
        SELECT COUNT(*) FROM parent_students ps
        WHERE ps.parent_user_id = :parent_id
    """), {"parent_id": user_id}).scalar()
    
    # Get latest report cards summary
    latest_grades = db.execute(text("""
        SELECT 
            s.first_name, s.last_name, s.admission_no,
            AVG(ar.grade_points) as avg_gpa,
            COUNT(ar.id) as subjects_count
        FROM parent_students ps
        JOIN students s ON ps.student_id = s.id
        JOIN academic_records ar ON s.id = ar.student_id
        WHERE ps.parent_user_id = :parent_id
        AND ar.academic_year = '2025' AND ar.term = 'Term 1'
        AND ar.is_finalized = true
        GROUP BY s.id, s.first_name, s.last_name, s.admission_no
        ORDER BY s.first_name, s.last_name
    """), {"parent_id": user_id}).mappings().all()
    
    # Get recent attendance summary
    recent_attendance = db.execute(text("""
        SELECT 
            s.first_name, s.last_name,
            COUNT(a.id) as total_days,
            SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_days
        FROM parent_students ps
        JOIN students s ON ps.student_id = s.id
        LEFT JOIN attendance a ON s.id = a.student_id
        WHERE ps.parent_user_id = :parent_id
        AND a.date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY s.id, s.first_name, s.last_name
        ORDER BY s.first_name, s.last_name
    """), {"parent_id": user_id}).mappings().all()
    
    return {
        "children_count": children_count,
        "academic_summary": [
            {
                "student_name": f"{grade['first_name']} {grade['last_name']}",
                "admission_no": grade['admission_no'],
                "current_gpa": round(float(grade['avg_gpa']), 2),
                "subjects_count": grade['subjects_count']
            } for grade in latest_grades
        ],
        "attendance_summary": [
            {
                "student_name": f"{att['first_name']} {att['last_name']}",
                "attendance_rate": round((att['present_days'] / att['total_days'] * 100) if att['total_days'] > 0 else 0, 1),
                "total_days": att['total_days'],
                "present_days": att['present_days']
            } for att in recent_attendance
        ]
    }
