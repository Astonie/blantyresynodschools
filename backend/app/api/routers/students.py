from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional

from app.schemas.students import StudentCreate, StudentRead, StudentUpdate
from sqlalchemy.exc import IntegrityError
from app.tenancy.deps import get_tenant_db
from app.api.deps import require_roles, require_permissions, get_current_user_id


router = APIRouter()


@router.get("", response_model=List[StudentRead], dependencies=[Depends(require_permissions(["students.read"]))])
def list_students(
    db: Session = Depends(get_tenant_db), 
    user_id: int = Depends(get_current_user_id),
    class_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None)
):
    # Determine roles for scoping
    roles = db.execute(text(
        """
        SELECT r.name FROM roles r
        JOIN user_roles ur ON ur.role_id = r.id
        WHERE ur.user_id = :uid
        """
    ), {"uid": user_id}).scalars().all()

    query = "SELECT * FROM students WHERE 1=1"
    params: dict = {}
    
    if class_name:
        query += " AND class_name = :class"
        params["class"] = class_name
    if status:
        query += " AND status = :status"
        params["status"] = status
    if q:
        query += " AND (LOWER(first_name || ' ' || last_name) LIKE :q OR LOWER(admission_no) LIKE :q OR LOWER(COALESCE(student_number,'')) LIKE :q)"
        params["q"] = f"%{q.lower()}%"
    
    # Scope: if Teacher and not an admin role, limit to classes they teach
    if "Teacher" in roles and not ("Administrator" in roles or "Head Teacher" in roles or "Tenant Admin" in roles or "School Administrator" in roles):
        class_rows = db.execute(text(
            """
            SELECT c.name
            FROM teacher_assignments ta
            JOIN classes c ON ta.class_id = c.id
            WHERE ta.teacher_id = :uid
            """
        ), {"uid": user_id}).scalars().all()
        if not class_rows:
            return []
        placeholders = ", ".join([f":c{i}" for i, _ in enumerate(class_rows)])
        for i, cname in enumerate(class_rows):
            params[f"c{i}"] = cname
        query += f" AND class_name IN ({placeholders})"

    query += " ORDER BY first_name, last_name"
    
    rows = db.execute(text(query), params).mappings().all()
    return [StudentRead(**dict(r)) for r in rows]


@router.get("/{student_id}", response_model=StudentRead, dependencies=[Depends(require_permissions(["students.read"]))])
def get_student(student_id: int, db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    row = db.execute(text("SELECT * FROM students WHERE id = :id"), {"id": student_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Student not found")
    return StudentRead(**dict(row))


@router.post("", response_model=StudentRead, dependencies=[Depends(require_permissions(["students.create"]))])
def create_student(payload: StudentCreate, db: Session = Depends(get_tenant_db)):
    try:
        # Auto-generate admission number if not provided
        admission_no = payload.admission_no
        if not admission_no:
            # Get current year using database-agnostic approach
            try:
                # Try PostgreSQL first
                current_year = db.execute(text("SELECT EXTRACT(YEAR FROM CURRENT_DATE)")).scalar()
            except:
                try:
                    # Fallback to SQLite
                    current_year = db.execute(text("SELECT strftime('%Y', 'now')")).scalar()
                except:
                    # Final fallback
                    current_year = "2025"
            
            # Get next sequence number for this year
            try:
                # PostgreSQL approach
                last_seq = db.execute(text("""
                    SELECT COALESCE(MAX(CAST(SUBSTRING(admission_no FROM 6) AS INTEGER)), 0) + 1
                    FROM students 
                    WHERE admission_no LIKE :year_pattern
                """), {"year_pattern": f"{current_year}-%"}).scalar()
            except:
                try:
                    # SQLite approach
                    last_seq = db.execute(text("""
                        SELECT COALESCE(MAX(CAST(SUBSTR(admission_no, 6) AS INTEGER)), 0) + 1
                        FROM students 
                        WHERE admission_no LIKE :year_pattern
                    """), {"year_pattern": f"{current_year}-%"}).scalar()
                except:
                    last_seq = 1
            
            admission_no = f"{current_year}-{last_seq:04d}"
        
        # Check if admission number already exists
        existing = db.execute(text("SELECT id FROM students WHERE admission_no = :adm"), {"adm": admission_no}).scalar()
        if existing:
            raise HTTPException(status_code=400, detail="Admission number already exists")

        db.execute(
            text("""
                INSERT INTO students(
                    first_name, last_name, gender, date_of_birth, admission_no, class_name,
                    parent_name, parent_phone, parent_email, address, student_number
                )
                VALUES (:fn, :ln, :g, :dob, :adm, :cls, :pn, :pp, :pe, :addr, :sn)
            """),
            {
                "fn": payload.first_name,
                "ln": payload.last_name,
                "g": payload.gender,
                "dob": payload.date_of_birth,
                "adm": admission_no,
                "cls": payload.class_name,
                "pn": payload.parent_name,
                "pp": payload.parent_phone,
                "pe": payload.parent_email,
                "addr": payload.address,
                "sn": payload.student_number,
            },
        )
        
        # Get the created student
        row = db.execute(
            text("SELECT * FROM students WHERE admission_no = :adm"), 
            {"adm": admission_no}
        ).mappings().first()
        db.commit()
        return StudentRead(**dict(row))
    except IntegrityError as ex:
        db.rollback()
        # Surface underlying DB error message for tests (e.g., UNIQUE constraint failed on SQLite)
        detail_msg = str(getattr(ex, "orig", ex))
        raise HTTPException(status_code=400, detail=detail_msg)
    except HTTPException as ex:
        # Pass through HTTP errors unchanged
        raise ex
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ex))


@router.delete("/{student_id}", dependencies=[Depends(require_permissions(["students.delete"]))])
def delete_student(student_id: int, db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    try:
        db.execute(text("DELETE FROM students WHERE id = :id"), {"id": student_id})
        db.commit()
        return {"status": "deleted"}
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail="Unable to delete student. They may have linked records.")


@router.put("/{student_id}", response_model=StudentRead, dependencies=[Depends(require_permissions(["students.update"]))])
def update_student(student_id: int, payload: StudentUpdate, db: Session = Depends(get_tenant_db)):
    try:
        # Ensure student exists
        existing = db.execute(text("SELECT id FROM students WHERE id = :id"), {"id": student_id}).scalar()
        if not existing:
            raise HTTPException(status_code=404, detail="Student not found")
        # Build dynamic update query
        update_fields = []
        params = {"id": student_id}
        
        if payload.first_name is not None:
            update_fields.append("first_name = :fn")
            params["fn"] = payload.first_name
        if payload.last_name is not None:
            update_fields.append("last_name = :ln")
            params["ln"] = payload.last_name
        if payload.gender is not None:
            update_fields.append("gender = :g")
            params["g"] = payload.gender
        if payload.date_of_birth is not None:
            update_fields.append("date_of_birth = :dob")
            params["dob"] = payload.date_of_birth
        if payload.class_name is not None:
            update_fields.append("class_name = :cls")
            params["cls"] = payload.class_name
        if payload.parent_name is not None:
            update_fields.append("parent_name = :pn")
            params["pn"] = payload.parent_name
        if payload.parent_phone is not None:
            update_fields.append("parent_phone = :pp")
            params["pp"] = payload.parent_phone
        if payload.parent_email is not None:
            update_fields.append("parent_email = :pe")
            params["pe"] = payload.parent_email
        if payload.address is not None:
            update_fields.append("address = :addr")
            params["addr"] = payload.address
        if payload.student_number is not None:
            update_fields.append("student_number = :sn")
            params["sn"] = payload.student_number
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE students SET {', '.join(update_fields)} WHERE id = :id"
        
        db.execute(text(query), params)
        row = db.execute(text("SELECT * FROM students WHERE id = :id"), {"id": student_id}).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Student not found")
        db.commit()
        return StudentRead(**dict(row))
    except HTTPException as ex:
        # Preserve explicit HTTP errors
        raise ex
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/{student_id}/attendance")
def get_student_attendance(
    student_id: int,
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    query = """
        SELECT a.*, c.name as class_name
        FROM attendance a
        JOIN classes c ON a.class_id = c.id
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
    
    rows = db.execute(text(query), params).mappings().all()
    return [dict(r) for r in rows]


@router.get("/classes/available")
def get_available_classes(db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    """Get list of available classes for student assignment."""
    rows = db.execute(text("SELECT id, name, grade_level FROM classes ORDER BY grade_level, name")).mappings().all()
    return [{"id": r.id, "name": r.name, "grade_level": r.grade_level} for r in rows]


