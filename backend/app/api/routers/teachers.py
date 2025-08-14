from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.schemas.teachers import (
    TeacherCreate, TeacherRead, TeacherUpdate,
    TeacherAssignmentCreate, TeacherAssignmentRead,
    TeacherPerformanceCreate, TeacherPerformanceRead,
    TeacherDashboard
)
from app.tenancy.deps import get_tenant_db
from app.api.deps import require_roles, require_permissions, get_current_user_id
from app.services.security import hash_password


router = APIRouter()


# Teacher Profile Management
@router.get("", response_model=List[TeacherRead], dependencies=[Depends(require_permissions(["teachers.read"]))])
def list_teachers(
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id),
    is_active: Optional[bool] = Query(None)
):
    # Determine roles for scoping
    user_roles = db.execute(text(
        """
        SELECT r.name FROM roles r
        JOIN user_roles ur ON ur.role_id = r.id
        WHERE ur.user_id = :uid
        """
    ), {"uid": user_id}).scalars().all()

    query = """
        SELECT u.id, u.email, u.full_name, u.is_active, u.created_at, u.updated_at,
               tp.phone, tp.address, tp.date_of_birth, tp.hire_date, tp.qualification, 
               tp.specialization, tp.salary
        FROM users u
        LEFT JOIN teacher_profiles tp ON u.id = tp.user_id
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN roles r ON ur.role_id = r.id
        WHERE r.name = 'Teacher'
    """
    params = {}
    
    if is_active is not None:
        query += " AND u.is_active = :active"
        params["active"] = is_active
    
    # If the requester is a Teacher (and not Admin/Head) limit to self
    if "Teacher" in user_roles and not ("Administrator" in user_roles or "Head Teacher" in user_roles or "Tenant Admin" in user_roles or "School Administrator" in user_roles):
        query += " AND u.id = :uid"
        params["uid"] = user_id

    query += " ORDER BY u.full_name"
    
    rows = db.execute(text(query), params).mappings().all()
    return [TeacherRead(**dict(r)) for r in rows]


@router.get("/{teacher_id}", response_model=TeacherRead)
def get_teacher(teacher_id: int, db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    row = db.execute(text("""
        SELECT u.id, u.email, u.full_name, u.is_active, u.created_at, u.updated_at,
               tp.phone, tp.address, tp.date_of_birth, tp.hire_date, tp.qualification, 
               tp.specialization, tp.salary
        FROM users u
        LEFT JOIN teacher_profiles tp ON u.id = tp.user_id
        WHERE u.id = :id
    """), {"id": teacher_id}).mappings().first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return TeacherRead(**dict(row))


@router.post("", dependencies=[Depends(require_permissions(["teachers.create"]))])
def create_teacher(payload: TeacherCreate, db: Session = Depends(get_tenant_db)):
    try:
        # Generate a temporary password for first login
        temp_password = "ChangeMe!"  # could be randomized; kept simple for MVP
        hashed = hash_password(temp_password)

        # First create the user with Teacher role
        db.execute(
            text("INSERT INTO users(email, full_name, hashed_password) VALUES (:email, :name, :pwd)"),
            {"email": payload.email, "name": payload.full_name, "pwd": hashed}
        )
        
        # Get the created user and Teacher role
        user_id = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": payload.email}).scalar()
        teacher_role_id = db.execute(text("SELECT id FROM roles WHERE name = 'Teacher'")).scalar()
        
        # Assign Teacher role
        db.execute(
            text("INSERT INTO user_roles(user_id, role_id) VALUES (:user, :role)"),
            {"user": user_id, "role": teacher_role_id}
        )
        
        # Create teacher profile
        db.execute(
            text("""
                INSERT INTO teacher_profiles(
                    user_id, phone, address, date_of_birth, hire_date, 
                    qualification, specialization, salary
                )
                VALUES (:user, :phone, :addr, :dob, :hire, :qual, :spec, :salary)
            """),
            {
                "user": user_id,
                "phone": payload.phone,
                "addr": payload.address,
                "dob": payload.date_of_birth,
                "hire": payload.hire_date,
                "qual": payload.qualification,
                "spec": payload.specialization,
                "salary": payload.salary,
            }
        )
        
        # Get the complete teacher record
        row = db.execute(text("""
            SELECT u.id, u.email, u.full_name, u.is_active, u.created_at, u.updated_at,
                   tp.phone, tp.address, tp.date_of_birth, tp.hire_date, tp.qualification, 
                   tp.specialization, tp.salary
            FROM users u
            LEFT JOIN teacher_profiles tp ON u.id = tp.user_id
            WHERE u.id = :id
        """), {"id": user_id}).mappings().first()
        
        db.commit()
        teacher = dict(row)
        # Return the temporary password so the caller can notify the teacher
        return {"teacher": teacher, "temp_password": temp_password}
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ex))


@router.put("/{teacher_id}", response_model=TeacherRead, dependencies=[Depends(require_permissions(["teachers.update"]))])
def update_teacher(teacher_id: int, payload: TeacherUpdate, db: Session = Depends(get_tenant_db)):
    try:
        # Update user table
        update_fields = []
        params = {"id": teacher_id}
        
        if payload.full_name is not None:
            update_fields.append("full_name = :name")
            params["name"] = payload.full_name
        if payload.is_active is not None:
            update_fields.append("is_active = :active")
            params["active"] = payload.is_active
        
        if update_fields:
            update_fields.append("updated_at = now()")
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = :id"
            db.execute(text(query), params)
        
        # Update teacher profile
        profile_update_fields = []
        profile_params = {"user_id": teacher_id}
        
        if payload.phone is not None:
            profile_update_fields.append("phone = :phone")
            profile_params["phone"] = payload.phone
        if payload.address is not None:
            profile_update_fields.append("address = :addr")
            profile_params["addr"] = payload.address
        if payload.date_of_birth is not None:
            profile_update_fields.append("date_of_birth = :dob")
            profile_params["dob"] = payload.date_of_birth
        if payload.hire_date is not None:
            profile_update_fields.append("hire_date = :hire")
            profile_params["hire"] = payload.hire_date
        if payload.qualification is not None:
            profile_update_fields.append("qualification = :qual")
            profile_params["qual"] = payload.qualification
        if payload.specialization is not None:
            profile_update_fields.append("specialization = :spec")
            profile_params["spec"] = payload.specialization
        if payload.salary is not None:
            profile_update_fields.append("salary = :salary")
            profile_params["salary"] = payload.salary
        
        if profile_update_fields:
            profile_update_fields.append("updated_at = now()")
            profile_query = f"UPDATE teacher_profiles SET {', '.join(profile_update_fields)} WHERE user_id = :user_id"
            db.execute(text(profile_query), profile_params)
        
        # Get updated record
        row = db.execute(text("""
            SELECT u.id, u.email, u.full_name, u.is_active, u.created_at, u.updated_at,
                   tp.phone, tp.address, tp.date_of_birth, tp.hire_date, tp.qualification, 
                   tp.specialization, tp.salary
            FROM users u
            LEFT JOIN teacher_profiles tp ON u.id = tp.user_id
            WHERE u.id = :id
        """), {"id": teacher_id}).mappings().first()
        
        db.commit()
        return TeacherRead(**dict(row))
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ex))


# Teacher Assignments
@router.get("/{teacher_id}/assignments", response_model=List[TeacherAssignmentRead])
def get_teacher_assignments(
    teacher_id: int,
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id),
    academic_year: Optional[str] = Query(None)
):
    query = """
        SELECT ta.*, u.full_name as teacher_name, c.name as class_name, s.name as subject_name
        FROM teacher_assignments ta
        JOIN users u ON ta.teacher_id = u.id
        JOIN classes c ON ta.class_id = c.id
        JOIN subjects s ON ta.subject_id = s.id
        WHERE ta.teacher_id = :teacher_id
    """
    params = {"teacher_id": teacher_id}
    
    if academic_year:
        query += " AND ta.academic_year = :year"
        params["year"] = academic_year
    
    query += " ORDER BY ta.academic_year DESC, c.name"
    
    rows = db.execute(text(query), params).mappings().all()
    return [TeacherAssignmentRead(**dict(r)) for r in rows]


@router.post("/assignments", response_model=TeacherAssignmentRead, dependencies=[Depends(require_roles(["Administrator", "Head Teacher"]))])
def create_teacher_assignment(payload: TeacherAssignmentCreate, db: Session = Depends(get_tenant_db)):
    try:
        db.execute(
            text("""
                INSERT INTO teacher_assignments(teacher_id, class_id, subject_id, academic_year, is_primary)
                VALUES (:teacher, :class, :subject, :year, :primary)
            """),
            {
                "teacher": payload.teacher_id,
                "class": payload.class_id,
                "subject": payload.subject_id,
                "year": payload.academic_year,
                "primary": payload.is_primary,
            }
        )
        
        row = db.execute(text("""
            SELECT ta.*, u.full_name as teacher_name, c.name as class_name, s.name as subject_name
            FROM teacher_assignments ta
            JOIN users u ON ta.teacher_id = u.id
            JOIN classes c ON ta.class_id = c.id
            JOIN subjects s ON ta.subject_id = s.id
            WHERE ta.teacher_id = :teacher AND ta.class_id = :class AND ta.subject_id = :subject AND ta.academic_year = :year
        """), {
            "teacher": payload.teacher_id,
            "class": payload.class_id,
            "subject": payload.subject_id,
            "year": payload.academic_year
        }).mappings().first()
        
        db.commit()
        return TeacherAssignmentRead(**dict(r))
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ex))


# Teacher Performance
@router.get("/{teacher_id}/performance", response_model=List[TeacherPerformanceRead])
def get_teacher_performance(
    teacher_id: int,
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id),
    academic_year: Optional[str] = Query(None)
):
    query = """
        SELECT tp.*, t.full_name as teacher_name, e.full_name as evaluator_name
        FROM teacher_performance tp
        JOIN users t ON tp.teacher_id = t.id
        JOIN users e ON tp.evaluator_id = e.id
        WHERE tp.teacher_id = :teacher_id
    """
    params = {"teacher_id": teacher_id}
    
    if academic_year:
        query += " AND tp.academic_year = :year"
        params["year"] = academic_year
    
    query += " ORDER BY tp.evaluation_date DESC"
    
    rows = db.execute(text(query), params).mappings().all()
    return [TeacherPerformanceRead(**dict(r)) for r in rows]


@router.post("/performance", response_model=TeacherPerformanceRead, dependencies=[Depends(require_roles(["Administrator", "Head Teacher"]))])
def create_teacher_performance(payload: TeacherPerformanceCreate, db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    try:
        db.execute(
            text("""
                INSERT INTO teacher_performance(
                    teacher_id, academic_year, term, evaluation_date,
                    teaching_effectiveness, classroom_management, student_engagement,
                    lesson_planning, professional_development, overall_rating,
                    comments, evaluator_id
                )
                VALUES (:teacher, :year, :term, :date, :teach, :class_mgmt, :engagement,
                        :planning, :dev, :rating, :comments, :evaluator)
            """),
            {
                "teacher": payload.teacher_id,
                "year": payload.academic_year,
                "term": payload.term,
                "date": payload.evaluation_date,
                "teach": payload.teaching_effectiveness,
                "class_mgmt": payload.classroom_management,
                "engagement": payload.student_engagement,
                "planning": payload.lesson_planning,
                "dev": payload.professional_development,
                "rating": payload.overall_rating,
                "comments": payload.comments,
                "evaluator": user_id,
            }
        )
        
        row = db.execute(text("""
            SELECT tp.*, t.full_name as teacher_name, e.full_name as evaluator_name
            FROM teacher_performance tp
            JOIN users t ON tp.teacher_id = t.id
            JOIN users e ON tp.evaluator_id = e.id
            WHERE tp.teacher_id = :teacher AND tp.academic_year = :year AND tp.term = :term AND tp.evaluation_date = :date
        """), {
            "teacher": payload.teacher_id,
            "year": payload.academic_year,
            "term": payload.term,
            "date": payload.evaluation_date
        }).mappings().first()
        
        db.commit()
        return TeacherPerformanceRead(**dict(r))
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ex))


# Teacher Dashboard
@router.get("/{teacher_id}/dashboard", response_model=TeacherDashboard)
def get_teacher_dashboard(teacher_id: int, db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    # Get teacher info
    teacher = db.execute(text("""
        SELECT u.id, u.full_name
        FROM users u
        WHERE u.id = :id
    """), {"id": teacher_id}).mappings().first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Get current assignments
    assignments = db.execute(text("""
        SELECT ta.*, u.full_name as teacher_name, c.name as class_name, s.name as subject_name
        FROM teacher_assignments ta
        JOIN users u ON ta.teacher_id = u.id
        JOIN classes c ON ta.class_id = c.id
        JOIN subjects s ON ta.subject_id = s.id
        WHERE ta.teacher_id = :teacher_id
        ORDER BY ta.academic_year DESC, c.name
    """), {"teacher_id": teacher_id}).mappings().all()
    
    # Get subjects taught
    subjects = db.execute(text("""
        SELECT DISTINCT s.name
        FROM teacher_assignments ta
        JOIN subjects s ON ta.subject_id = s.id
        WHERE ta.teacher_id = :teacher_id
    """), {"teacher_id": teacher_id}).scalars().all()
    
    # Get total students
    total_students = db.execute(text("""
        SELECT COUNT(DISTINCT s.id)
        FROM students s
        JOIN classes c ON s.current_class = c.name
        JOIN teacher_assignments ta ON c.id = ta.class_id
        WHERE ta.teacher_id = :teacher_id
    """), {"teacher_id": teacher_id}).scalar() or 0
    
    # Get recent performance
    recent_performance = db.execute(text("""
        SELECT tp.*, t.full_name as teacher_name, e.full_name as evaluator_name
        FROM teacher_performance tp
        JOIN users t ON tp.teacher_id = t.id
        JOIN users e ON tp.evaluator_id = e.id
        WHERE tp.teacher_id = :teacher_id
        ORDER BY tp.evaluation_date DESC
        LIMIT 1
    """), {"teacher_id": teacher_id}).mappings().first()
    
    return TeacherDashboard(
        teacher_id=teacher_id,
        teacher_name=teacher.full_name,
        total_classes=len(assignments),
        total_students=total_students,
        subjects_taught=list(subjects),
        current_assignments=[TeacherAssignmentRead(**dict(a)) for a in assignments],
        recent_performance=TeacherPerformanceRead(**dict(recent_performance)) if recent_performance else None,
        attendance_rate=None  # TODO: Implement attendance tracking for teachers
    )
