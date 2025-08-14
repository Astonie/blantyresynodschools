from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.schemas.academic import (
    ClassCreate, ClassRead, ClassUpdate,
    SubjectCreate, SubjectRead, SubjectUpdate,
    ClassSubjectCreate, ClassSubjectRead,
    AttendanceCreate, AttendanceRead, AttendanceUpdate,
    AcademicRecordCreate, AcademicRecordRead, AcademicRecordUpdate,
    BulkAttendanceCreate, StudentAcademicSummary
)
from app.tenancy.deps import get_tenant_db
from app.api.deps import require_roles, require_permissions, get_current_user_id


router = APIRouter()


# Class Management
@router.get("/classes", response_model=List[ClassRead], dependencies=[Depends(require_permissions(["academic.read"]))])
def list_classes(
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id),
    academic_year: Optional[str] = Query(None)
):
    query = "SELECT * FROM classes"
    params = {}
    if academic_year:
        query += " WHERE academic_year = :year"
        params["year"] = academic_year
    query += " ORDER BY name"
    
    rows = db.execute(text(query), params).mappings().all()
    return [ClassRead(**dict(r)) for r in rows]


@router.post("/classes", response_model=ClassRead, dependencies=[Depends(require_permissions(["settings.manage"]))])
def create_class(payload: ClassCreate, db: Session = Depends(get_tenant_db)):
    try:
        db.execute(
            text("""
                INSERT INTO classes(name, grade_level, capacity, teacher_id, academic_year)
                VALUES (:name, :grade, :cap, :teacher, :year)
            """),
            {
                "name": payload.name,
                "grade": payload.grade_level,
                "cap": payload.capacity,
                "teacher": payload.teacher_id,
                "year": payload.academic_year,
            }
        )
        row = db.execute(
            text("SELECT * FROM classes WHERE name = :name AND academic_year = :year"),
            {"name": payload.name, "year": payload.academic_year}
        ).mappings().first()
        db.commit()
        return ClassRead(**dict(row))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Class name already exists")
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/classes/{class_id}", response_model=ClassRead)
def get_class(class_id: int, db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    row = db.execute(text("SELECT * FROM classes WHERE id = :id"), {"id": class_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Class not found")
    return ClassRead(**dict(row))


@router.put("/classes/{class_id}", response_model=ClassRead, dependencies=[Depends(require_roles(["Administrator", "Head Teacher"]))])
def update_class(class_id: int, payload: ClassUpdate, db: Session = Depends(get_tenant_db)):
    try:
        # Build dynamic update query
        update_fields = []
        params = {"id": class_id}
        
        if payload.name is not None:
            update_fields.append("name = :name")
            params["name"] = payload.name
        if payload.grade_level is not None:
            update_fields.append("grade_level = :grade")
            params["grade"] = payload.grade_level
        if payload.capacity is not None:
            update_fields.append("capacity = :cap")
            params["cap"] = payload.capacity
        if payload.teacher_id is not None:
            update_fields.append("teacher_id = :teacher")
            params["teacher"] = payload.teacher_id
        if payload.academic_year is not None:
            update_fields.append("academic_year = :year")
            params["year"] = payload.academic_year
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE classes SET {', '.join(update_fields)} WHERE id = :id"
        
        db.execute(text(query), params)
        row = db.execute(text("SELECT * FROM classes WHERE id = :id"), {"id": class_id}).mappings().first()
        db.commit()
        return ClassRead(**dict(row))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Subject code already exists")
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ex))


# Subject Management
@router.get("/subjects", response_model=List[SubjectRead], dependencies=[Depends(require_permissions(["academic.read"]))])
def list_subjects(db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    rows = db.execute(text("SELECT * FROM subjects ORDER BY name")).mappings().all()
    return [SubjectRead(**dict(r)) for r in rows]


@router.post("/subjects", response_model=SubjectRead, dependencies=[Depends(require_permissions(["settings.manage"]))])
def create_subject(payload: SubjectCreate, db: Session = Depends(get_tenant_db)):
    try:
        db.execute(
            text("INSERT INTO subjects(name, code, description) VALUES (:name, :code, :desc)"),
            {
                "name": payload.name,
                "code": payload.code,
                "desc": payload.description,
            }
        )
        row = db.execute(
            text("SELECT * FROM subjects WHERE code = :code"),
            {"code": payload.code}
        ).mappings().first()
        db.commit()
        return SubjectRead(**dict(row))
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/subjects/{subject_id}", response_model=SubjectRead)
def get_subject(subject_id: int, db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    row = db.execute(text("SELECT * FROM subjects WHERE id = :id"), {"id": subject_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Subject not found")
    return SubjectRead(**dict(row))


# Class-Subject Assignment
@router.get("/class-subjects", response_model=List[ClassSubjectRead], dependencies=[Depends(require_permissions(["academic.read"]))])
def list_class_subjects(
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id),
    class_id: Optional[int] = Query(None)
):
    query = """
        SELECT cs.*, c.name as class_name, s.name as subject_name, s.code as subject_code
        FROM class_subjects cs
        JOIN classes c ON cs.class_id = c.id
        JOIN subjects s ON cs.subject_id = s.id
    """
    params = {}
    if class_id:
        query += " WHERE cs.class_id = :class_id"
        params["class_id"] = class_id
    query += " ORDER BY c.name, s.name"
    
    rows = db.execute(text(query), params).mappings().all()
    return [ClassSubjectRead(**dict(r)) for r in rows]


@router.post("/class-subjects", response_model=ClassSubjectRead, dependencies=[Depends(require_permissions(["settings.manage"]))])
def assign_subject_to_class(payload: ClassSubjectCreate, db: Session = Depends(get_tenant_db)):
    try:
        db.execute(
            text("INSERT INTO class_subjects(class_id, subject_id, teacher_id) VALUES (:class, :subject, :teacher)"),
            {
                "class": payload.class_id,
                "subject": payload.subject_id,
                "teacher": payload.teacher_id,
            }
        )
        row = db.execute(text("""
            SELECT cs.*, c.name as class_name, s.name as subject_name, s.code as subject_code
            FROM class_subjects cs
            JOIN classes c ON cs.class_id = c.id
            JOIN subjects s ON cs.subject_id = s.id
            WHERE cs.class_id = :class AND cs.subject_id = :subject
        """), {"class": payload.class_id, "subject": payload.subject_id}).mappings().first()
        db.commit()
        return ClassSubjectRead(**dict(row))
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ex))


# Attendance Management
@router.get("/attendance", response_model=List[AttendanceRead], dependencies=[Depends(require_permissions(["academic.read"]))])
def list_attendance(
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id),
    class_id: Optional[int] = Query(None),
    date: Optional[date] = Query(None),
    student_id: Optional[int] = Query(None)
):
    query = """
        SELECT a.*, s.first_name || ' ' || s.last_name as student_name, c.name as class_name
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN classes c ON a.class_id = c.id
        WHERE 1=1
    """
    params = {}
    
    if class_id:
        query += " AND a.class_id = :class_id"
        params["class_id"] = class_id
    if date:
        query += " AND a.date = :date"
        params["date"] = date
    if student_id:
        query += " AND a.student_id = :student_id"
        params["student_id"] = student_id
    
    query += " ORDER BY a.date DESC, s.first_name"
    
    rows = db.execute(text(query), params).mappings().all()
    # created_at may be absent in test table; pass through None
    return [AttendanceRead(**dict(r)) for r in rows]


@router.post("/attendance", response_model=AttendanceRead, dependencies=[Depends(require_permissions(["academic.attendance"]))])
def create_attendance(payload: AttendanceCreate, db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    try:
        db.execute(
            text("""
                INSERT INTO attendance(student_id, class_id, date, status, notes, recorded_by)
                VALUES (:student, :class, :date, :status, :notes, :recorded_by)
            """),
            {
                "student": payload.student_id,
                "class": payload.class_id,
                "date": payload.date,
                "status": payload.status,
                "notes": payload.notes,
                "recorded_by": user_id,
            }
        )
        row = db.execute(text("""
            SELECT a.*, s.first_name || ' ' || s.last_name as student_name, c.name as class_name
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            JOIN classes c ON a.class_id = c.id
            WHERE a.student_id = :student AND a.class_id = :class AND a.date = :date
        """), {"student": payload.student_id, "class": payload.class_id, "date": payload.date}).mappings().first()
        if not row:
            base = db.execute(text("""
                SELECT * FROM attendance WHERE student_id = :student AND class_id = :class AND date = :date
            """), {"student": payload.student_id, "class": payload.class_id, "date": payload.date}).mappings().first() or {}
            sname = db.execute(text("SELECT first_name || ' ' || last_name FROM students WHERE id = :sid"), {"sid": payload.student_id}).scalar() or ""
            cname = db.execute(text("SELECT name FROM classes WHERE id = :cid"), {"cid": payload.class_id}).scalar() or ""
            row = {**dict(base), "student_name": sname, "class_name": cname}
        db.commit()
        return AttendanceRead(**{**dict(row), "created_at": None})
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ex))


@router.post("/attendance/bulk", dependencies=[Depends(require_permissions(["academic.attendance"]))])
def create_bulk_attendance(payload: BulkAttendanceCreate, db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    try:
        for record in payload.attendance_records:
            db.execute(
                text("""
                    INSERT INTO attendance(student_id, class_id, date, status, notes, recorded_by)
                    VALUES (:student, :class, :date, :status, :notes, :recorded_by)
                    ON CONFLICT (student_id, class_id, date) DO UPDATE SET
                    status = EXCLUDED.status, notes = EXCLUDED.notes, recorded_by = EXCLUDED.recorded_by
                """),
                {
                    "student": record.student_id,
                    "class": payload.class_id,
                    "date": payload.date,
                    "status": record.status,
                    "notes": record.notes,
                    "recorded_by": user_id,
                }
            )
        db.commit()
        return {"message": f"Attendance recorded for {len(payload.attendance_records)} students"}
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ex))


# Academic Records
@router.get("/academic-records", response_model=List[AcademicRecordRead], dependencies=[Depends(require_permissions(["academic.read"]))])
def list_academic_records(
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id),
    student_id: Optional[int] = Query(None),
    class_id: Optional[int] = Query(None),
    subject_id: Optional[int] = Query(None),
    term: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None)
):
    query = """
        SELECT ar.*, s.first_name || ' ' || s.last_name as student_name, 
               sub.name as subject_name, sub.code as subject_code, c.name as class_name
        FROM academic_records ar
        JOIN students s ON ar.student_id = s.id
        JOIN subjects sub ON ar.subject_id = sub.id
        JOIN classes c ON ar.class_id = c.id
        WHERE 1=1
    """
    params = {}
    
    if student_id:
        query += " AND ar.student_id = :student_id"
        params["student_id"] = student_id
    if class_id:
        query += " AND ar.class_id = :class_id"
        params["class_id"] = class_id
    if subject_id:
        query += " AND ar.subject_id = :subject_id"
        params["subject_id"] = subject_id
    if term:
        query += " AND ar.term = :term"
        params["term"] = term
    if academic_year:
        query += " AND ar.academic_year = :year"
        params["year"] = academic_year
    
    query += " ORDER BY ar.student_id, ar.subject_id, ar.term"
    
    rows = db.execute(text(query), params).mappings().all()
    return [AcademicRecordRead(**dict(r)) for r in rows]


@router.post("/academic-records", response_model=AcademicRecordRead, dependencies=[Depends(require_permissions(["academic.record"]))])
def create_academic_record(payload: AcademicRecordCreate, db: Session = Depends(get_tenant_db)):
    try:
        # Compute overall score if not provided: prefer explicit score, else CA 40% + Exam 60%
        overall = payload.score
        if overall is None and (payload.ca_score is not None or payload.exam_score is not None):
            ca = payload.ca_score or 0
            ex = payload.exam_score or 0
            overall = round(ca * 0.4 + ex * 0.6, 2)

        # Derive grade if not provided (simple scale, can be customized per tenant later)
        grade = payload.grade
        if grade is None and overall is not None:
            if overall >= 80:
                grade = "A"
            elif overall >= 70:
                grade = "B"
            elif overall >= 60:
                grade = "C"
            elif overall >= 50:
                grade = "D"
            elif overall >= 40:
                grade = "E"
            else:
                grade = "F"

        db.execute(
            text(
                """
                INSERT INTO academic_records(
                    student_id, subject_id, class_id, term, academic_year,
                    score, ca_score, exam_score, overall_score, grade, remarks
                )
                VALUES (:student, :subject, :class, :term, :year,
                        :score, :ca, :exam, :overall, :grade, :remarks)
                """
            ),
            {
                "student": payload.student_id,
                "subject": payload.subject_id,
                "class": payload.class_id,
                "term": payload.term,
                "year": payload.academic_year,
                "score": payload.score,
                "ca": payload.ca_score,
                "exam": payload.exam_score,
                "overall": overall,
                "grade": grade,
                "remarks": payload.remarks,
            },
        )
        row = db.execute(text("""
            SELECT ar.*, s.first_name || ' ' || s.last_name as student_name, 
                   sub.name as subject_name, c.name as class_name
            FROM academic_records ar
            JOIN students s ON ar.student_id = s.id
            JOIN subjects sub ON ar.subject_id = sub.id
            JOIN classes c ON ar.class_id = c.id
            WHERE ar.student_id = :student AND ar.subject_id = :subject AND ar.class_id = :class 
                  AND ar.term = :term AND ar.academic_year = :year
        """), {
            "student": payload.student_id,
            "subject": payload.subject_id,
            "class": payload.class_id,
            "term": payload.term,
            "year": payload.academic_year
        }).mappings().first()
        db.commit()
        return AcademicRecordRead(**dict(row))
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/report-card/{student_id}")
def get_report_card(
    student_id: int,
    term: str = Query(...),
    academic_year: str = Query(...),
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id),
):
    student = db.execute(text("""
        SELECT s.id, s.first_name, s.last_name, s.current_class
        FROM students s WHERE s.id = :sid
    """), {"sid": student_id}).mappings().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    rows = db.execute(text("""
        SELECT ar.*, sub.name AS subject_name, sub.code AS subject_code
        FROM academic_records ar
        JOIN subjects sub ON ar.subject_id = sub.id
        WHERE ar.student_id = :sid AND ar.term = :term AND ar.academic_year = :yr
        ORDER BY sub.name
    """), {"sid": student_id, "term": term, "yr": academic_year}).mappings().all()

    subjects = [dict(r) for r in rows]
    scores = [r.overall_score for r in rows if r.overall_score is not None]
    overall_average = round(sum(scores) / len(scores), 2) if scores else None

    return {
        "student": {
            "id": student_id,
            "name": f"{student.first_name} {student.last_name}",
            "class": student.current_class,
        },
        "term": term,
        "academic_year": academic_year,
        "subjects": subjects,
        "overall_average": overall_average,
    }


@router.get("/academic-summary/{student_id}", response_model=StudentAcademicSummary)
def get_student_academic_summary(
    student_id: int,
    term: str = Query(...),
    academic_year: str = Query(...),
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    # Get student info
    student = db.execute(text("""
        SELECT s.id, s.first_name || ' ' || s.last_name as student_name, c.name as class_name
        FROM students s
        LEFT JOIN classes c ON s.current_class = c.name
        WHERE s.id = :student_id
    """), {"student_id": student_id}).mappings().first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get academic records
    records = db.execute(text("""
        SELECT ar.*, s.first_name || ' ' || s.last_name as student_name, 
               sub.name as subject_name, c.name as class_name
        FROM academic_records ar
        JOIN students s ON ar.student_id = s.id
        JOIN subjects sub ON ar.subject_id = sub.id
        JOIN classes c ON ar.class_id = c.id
        WHERE ar.student_id = :student_id AND ar.term = :term AND ar.academic_year = :year
        ORDER BY sub.name
    """), {"student_id": student_id, "term": term, "year": academic_year}).mappings().all()
    
    # Calculate average
    scores = [r.score for r in records if r.score is not None]
    average_score = sum(scores) / len(scores) if scores else None
    
    return StudentAcademicSummary(
        student_id=student_id,
        student_name=student.student_name,
        class_name=student.class_name,
        term=term,
        academic_year=academic_year,
        subjects=[AcademicRecordRead(**dict(r)) for r in records],
        average_score=average_score,
        total_subjects=len(records)
    )
