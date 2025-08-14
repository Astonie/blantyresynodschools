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
    BulkAttendanceCreate, StudentAcademicSummary,
    ExamScheduleCreate, ExamScheduleRead, ExamScheduleUpdate
)
from app.tenancy.deps import get_tenant_db
from app.api.deps import require_roles, require_permissions, get_current_user_id


router = APIRouter()


def _compute_grade_for_scores(db: Session, ca_score: Optional[float], exam_score: Optional[float], explicit_overall: Optional[float]) -> tuple[Optional[float], Optional[str], Optional[float]]:
    """Compute overall score, grade letter, and grade points using current grading policy and grade scales.
    Returns (overall_score, grade_letter, grade_points)."""
    policy = db.execute(text("SELECT policy_type, ca_weight, exam_weight FROM grading_policies LIMIT 1")).mappings().first()
    ca_w = float(policy.ca_weight) if policy and policy.ca_weight is not None else 40.0
    ex_w = float(policy.exam_weight) if policy and policy.exam_weight is not None else 60.0

    overall: Optional[float] = None
    if explicit_overall is not None:
        overall = float(explicit_overall)
    elif ca_score is not None or exam_score is not None:
        ca = float(ca_score or 0)
        ex = float(exam_score or 0)
        overall = round((ca * ca_w / 100.0) + (ex * ex_w / 100.0), 2)

    # Determine grade via grade scales
    letter: Optional[str] = None
    points: Optional[float] = None
    if overall is not None:
        scales = db.execute(text("""
            SELECT letter, min_score, max_score, points
            FROM grade_scales
            ORDER BY sort_order ASC, min_score DESC
        """)).mappings().all()
        for s in scales:
            try:
                if float(s.min_score) <= overall <= float(s.max_score):
                    letter = s.letter
                    points = float(s.points) if s.points is not None else None
                    break
            except Exception:
                continue
    return overall, letter, points


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
        # Compute overall score if not provided, using grading policy
        overall, grade_letter, grade_points = _compute_grade_for_scores(
            db,
            payload.ca_score,
            payload.exam_score,
            payload.score,
        )

        db.execute(
            text(
                """
                INSERT INTO academic_records(
                    student_id, subject_id, class_id, term, academic_year,
                    score, ca_score, exam_score, overall_score, grade, grade_points, remarks
                )
                VALUES (:student, :subject, :class, :term, :year,
                        :score, :ca, :exam, :overall, :grade, :gpoints, :remarks)
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
                "grade": grade_letter,
                "gpoints": grade_points,
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


# Report Card and Analytics remain below ...

# Grading policy management
@router.get("/grading/policy", dependencies=[Depends(require_permissions(["academic.read"]))])
def get_grading_policy(db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    row = db.execute(text("SELECT id, policy_type, ca_weight, exam_weight, pass_mark FROM grading_policies LIMIT 1")).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Grading policy not found")
    return dict(row)


@router.put("/grading/policy", dependencies=[Depends(require_permissions(["academic.manage"]))])
def update_grading_policy(
    policy_type: Optional[str] = Query(None, pattern="^(percentage|gpa)$"),
    ca_weight: Optional[float] = Query(None, ge=0, le=100),
    exam_weight: Optional[float] = Query(None, ge=0, le=100),
    pass_mark: Optional[float] = Query(None, ge=0, le=100),
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    sets = []
    params: dict = {}
    if policy_type is not None:
        sets.append("policy_type = :pt")
        params["pt"] = policy_type
    if ca_weight is not None:
        sets.append("ca_weight = :cw")
        params["cw"] = ca_weight
    if exam_weight is not None:
        sets.append("exam_weight = :ew")
        params["ew"] = exam_weight
    if pass_mark is not None:
        sets.append("pass_mark = :pm")
        params["pm"] = pass_mark
    if not sets:
        raise HTTPException(status_code=400, detail="No fields to update")
    q = f"UPDATE grading_policies SET {', '.join(sets)}, updated_at = CURRENT_TIMESTAMP"
    db.execute(text(q), params)
    row = db.execute(text("SELECT id, policy_type, ca_weight, exam_weight, pass_mark FROM grading_policies LIMIT 1")).mappings().first()
    db.commit()
    return dict(row)


@router.get("/grading/scales", dependencies=[Depends(require_permissions(["academic.read"]))])
def get_grade_scales(db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    rows = db.execute(text("SELECT id, letter, min_score, max_score, points, remarks, sort_order FROM grade_scales ORDER BY sort_order ASC, min_score DESC")).mappings().all()
    return [dict(r) for r in rows]


@router.post("/grading/scales", dependencies=[Depends(require_permissions(["academic.manage"]))])
def create_grade_scale(
    letter: str,
    min_score: float,
    max_score: float,
    points: Optional[float] = None,
    remarks: Optional[str] = None,
    sort_order: Optional[int] = 0,
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    db.execute(text("""
        INSERT INTO grade_scales(letter, min_score, max_score, points, remarks, sort_order)
        VALUES (:l, :min, :max, :p, :r, :o)
    """), {"l": letter, "min": min_score, "max": max_score, "p": points, "r": remarks, "o": sort_order or 0})
    row = db.execute(text("SELECT id, letter, min_score, max_score, points, remarks, sort_order FROM grade_scales WHERE letter = :l AND min_score = :min AND max_score = :max"), {"l": letter, "min": min_score, "max": max_score}).mappings().first()
    db.commit()
    return dict(row)


@router.put("/grading/scales/{scale_id}", dependencies=[Depends(require_permissions(["academic.manage"]))])
def update_grade_scale(
    scale_id: int,
    letter: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    points: Optional[float] = None,
    remarks: Optional[str] = None,
    sort_order: Optional[int] = None,
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    sets = []
    params = {"id": scale_id}
    if letter is not None:
        sets.append("letter = :l")
        params["l"] = letter
    if min_score is not None:
        sets.append("min_score = :min")
        params["min"] = min_score
    if max_score is not None:
        sets.append("max_score = :max")
        params["max"] = max_score
    if points is not None:
        sets.append("points = :p")
        params["p"] = points
    if remarks is not None:
        sets.append("remarks = :r")
        params["r"] = remarks
    if sort_order is not None:
        sets.append("sort_order = :o")
        params["o"] = sort_order
    if not sets:
        raise HTTPException(status_code=400, detail="No fields to update")
    q = f"UPDATE grade_scales SET {', '.join(sets)} WHERE id = :id"
    res = db.execute(text(q), params)
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Scale not found")
    row = db.execute(text("SELECT id, letter, min_score, max_score, points, remarks, sort_order FROM grade_scales WHERE id = :id"), {"id": scale_id}).mappings().first()
    db.commit()
    return dict(row)


@router.delete("/grading/scales/{scale_id}", dependencies=[Depends(require_permissions(["academic.manage"]))])
def delete_grade_scale(scale_id: int, db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    res = db.execute(text("DELETE FROM grade_scales WHERE id = :id"), {"id": scale_id})
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Scale not found")
    db.commit()
    return {"message": "Deleted"}


@router.post("/academic-records/finalize", dependencies=[Depends(require_permissions(["academic.manage"]))])
def finalize_results(
    term: str = Query(...),
    academic_year: str = Query(...),
    student_id: Optional[int] = Query(None),
    class_id: Optional[int] = Query(None),
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    if not student_id and not class_id:
        raise HTTPException(status_code=400, detail="Provide student_id or class_id")
    q = "UPDATE academic_records SET is_finalized = TRUE WHERE term = :term AND academic_year = :year"
    params: dict = {"term": term, "year": academic_year}
    if student_id:
        q += " AND student_id = :sid"
        params["sid"] = student_id
    if class_id:
        q += " AND class_id = :cid"
        params["cid"] = class_id
    db.execute(text(q), params)
    db.commit()
    return {"message": "Results finalized"}


# Parent endpoints
@router.get("/parent/students", dependencies=[Depends(require_permissions(["academic.read"]))])
def list_parent_students(db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    rows = db.execute(text("""
        SELECT s.id, s.first_name, s.last_name, s.admission_no, s.class_name
        FROM parent_students ps
        JOIN students s ON ps.student_id = s.id
        WHERE ps.parent_user_id = :uid
        ORDER BY s.first_name, s.last_name
    """), {"uid": user_id}).mappings().all()
    return [dict(r) for r in rows]


@router.get("/parent/results", dependencies=[Depends(require_permissions(["academic.read"]))])
def parent_results(
    student_id: Optional[int] = Query(None),
    term: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    query = """
        SELECT ar.*, s.first_name || ' ' || s.last_name as student_name, sub.name as subject_name, c.name as class_name
        FROM academic_records ar
        JOIN parent_students ps ON ps.student_id = ar.student_id AND ps.parent_user_id = :uid
        JOIN students s ON s.id = ar.student_id
        JOIN subjects sub ON sub.id = ar.subject_id
        JOIN classes c ON c.id = ar.class_id
        WHERE 1=1
    """
    params = {"uid": user_id}
    if student_id:
        query += " AND ar.student_id = :sid"
        params["sid"] = student_id
    if term:
        query += " AND ar.term = :term"
        params["term"] = term
    if academic_year:
        query += " AND ar.academic_year = :yr"
        params["yr"] = academic_year
    query += " ORDER BY ar.academic_year DESC, ar.term, ar.student_id"
    rows = db.execute(text(query), params).mappings().all()
    return [dict(r) for r in rows]
