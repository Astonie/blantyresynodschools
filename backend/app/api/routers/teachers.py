from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
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


# Teacher Dashboard - Current User (must come before parameterized routes)
@router.get("/dashboard", response_model=dict)
def get_current_teacher_dashboard(db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    """Get dashboard data for the currently logged-in teacher"""
    # Get teacher info
    teacher = db.execute(text("""
        SELECT u.id, u.full_name, u.email, t.subject_specialty
        FROM users u
        LEFT JOIN teachers t ON u.email = t.email
        WHERE u.id = :id
    """), {"id": user_id}).mappings().first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Get current assignments with student counts
    assignments = db.execute(text("""
        SELECT ta.id, ta.class_id, ta.subject_id,
               c.name as class_name, s.name as subject_name, s.code as subject_code,
               COUNT(DISTINCT st.id) as student_count
        FROM teacher_assignments ta
        JOIN classes c ON ta.class_id = c.id
        JOIN subjects s ON ta.subject_id = s.id
        JOIN teachers t ON ta.teacher_id = t.id
        LEFT JOIN students st ON st.class_name = c.name
        WHERE t.email = (SELECT email FROM users WHERE id = :user_id)
        GROUP BY ta.id, ta.class_id, ta.subject_id, c.name, s.name, s.code
        ORDER BY c.name, s.name
    """), {"user_id": user_id}).mappings().all()
    
    # Get statistics
    total_students = sum(a.student_count for a in assignments)
    classes_today = len(assignments)  # Simplified - could be enhanced with actual schedule
    
    # Get pending grades count
    pending_grades = db.execute(text("""
        SELECT COUNT(DISTINCT st.id)
        FROM students st
        JOIN classes c ON st.class_name = c.name
        JOIN teacher_assignments ta ON c.id = ta.class_id
        JOIN teachers t ON ta.teacher_id = t.id
        LEFT JOIN academic_records ar ON st.id = ar.student_id AND ta.subject_id = ar.subject_id 
            AND ar.term = 'Term 1 Final' AND ar.academic_year = '2024'
        WHERE t.email = (SELECT email FROM users WHERE id = :user_id) AND ar.id IS NULL
    """), {"user_id": user_id}).scalar() or 0
    
    # Calculate attendance rate (simplified)
    attendance_rate = 85.0  # Placeholder
    
    # Get recent activities (placeholder)
    recent_activities = []
    
    # Get upcoming classes (placeholder)
    upcoming_classes = []
    
    # Get notifications (placeholder)
    notifications = []
    
    return {
        "teacher_info": {
            "id": teacher.id,
            "full_name": teacher.full_name,
            "email": teacher.email,
            "specialization": teacher.subject_specialty,
            "classes_assigned": len(assignments),
            "subjects_taught": len(set(a.subject_name for a in assignments))
        },
        "assignments": [dict(a) for a in assignments],
        "statistics": {
            "total_students": total_students,
            "classes_today": classes_today,
            "pending_grades": pending_grades,
            "attendance_rate": attendance_rate
        },
        "recent_activities": recent_activities,
        "upcoming_classes": upcoming_classes,
        "notifications": notifications
    }


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
               t.phone, t.first_name, t.last_name, t.hire_date, t.subject_specialty
        FROM users u
        LEFT JOIN teachers t ON u.email = t.email
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
               t.phone, t.first_name, t.last_name, t.hire_date, t.subject_specialty
        FROM users u
        LEFT JOIN teachers t ON u.email = t.email
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
                INSERT INTO teachers(
                    email, first_name, last_name, phone, hire_date, 
                    subject_specialty
                )
                VALUES (:email, :fname, :lname, :phone, :hire, :spec)
            """),
            {
                "email": payload.email,
                "fname": payload.full_name.split()[0] if payload.full_name else "",
                "lname": " ".join(payload.full_name.split()[1:]) if payload.full_name and len(payload.full_name.split()) > 1 else "",
                "phone": payload.phone,
                "hire": payload.hire_date,
                "spec": payload.specialization,
                "salary": payload.salary,
            }
        )
        
        # Get the complete teacher record
        row = db.execute(text("""
            SELECT u.id, u.email, u.full_name, u.is_active, u.created_at, u.updated_at,
                   t.phone, t.first_name, t.last_name, t.hire_date, t.subject_specialty
            FROM users u
            LEFT JOIN teachers t ON u.email = t.email
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
            profile_query = f"UPDATE teachers SET {', '.join(profile_update_fields)} WHERE email = (SELECT email FROM users WHERE id = :user_id)"
            db.execute(text(profile_query), profile_params)
        
        # Get updated record
        row = db.execute(text("""
            SELECT u.id, u.email, u.full_name, u.is_active, u.created_at, u.updated_at,
                   t.phone, t.first_name, t.last_name, t.hire_date, t.subject_specialty
            FROM users u
            LEFT JOIN teachers t ON u.email = t.email
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


# Get students in a class for the teacher
@router.get("/classes/{class_name}/students", response_model=List[dict], dependencies=[Depends(require_permissions(["students.read"]))])
def get_class_students(
    class_name: str,
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get all students in a specific class that the teacher is assigned to"""
    # Verify teacher is assigned to this class
    assignment = db.execute(text("""
        SELECT ta.id
        FROM teacher_assignments ta
        JOIN classes c ON ta.class_id = c.id
        JOIN teachers t ON ta.teacher_id = t.id
        JOIN users u ON t.email = u.email
        WHERE u.id = :user_id AND c.name = :class_name
    """), {"user_id": user_id, "class_name": class_name}).first()
    
    if not assignment:
        raise HTTPException(status_code=403, detail="You are not assigned to this class")
    
    # Get students
    students = db.execute(text("""
        SELECT s.id, s.student_number, s.first_name || ' ' || s.last_name as full_name, s.class_name
        FROM students s
        WHERE s.class_name = :class_name
        ORDER BY s.first_name, s.last_name
    """), {"class_name": class_name}).mappings().all()
    
    return [dict(student) for student in students]


# Grade Management Routes
@router.get("/grades/{class_name}/{subject_code}", response_model=dict, dependencies=[Depends(require_permissions(["academic.read"]))])
def get_class_grades(
    class_name: str,
    subject_code: str,
    term: str = Query("Term 1 Final"),
    academic_year: str = Query("2024"),
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get grades for a specific class and subject"""
    # Verify teacher assignment
    assignment = db.execute(text("""
        SELECT ta.id, s.id as subject_id
        FROM teacher_assignments ta
        JOIN classes c ON ta.class_id = c.id
        JOIN subjects s ON ta.subject_id = s.id
        JOIN teachers t ON ta.teacher_id = t.id
        JOIN users u ON t.email = u.email
        WHERE u.id = :user_id AND c.name = :class_name AND s.code = :subject_code
    """), {"user_id": user_id, "class_name": class_name, "subject_code": subject_code}).mappings().first()
    
    if not assignment:
        raise HTTPException(status_code=403, detail="You are not assigned to teach this subject in this class")
    
    # Get academic records
    records = db.execute(text("""
        SELECT ar.*, st.first_name || ' ' || st.last_name as student_name, st.student_number as student_id_number
        FROM academic_records ar
        JOIN students st ON ar.student_id = st.id
        WHERE ar.subject_id = :subject_id AND ar.term = :term AND ar.academic_year = :year
        ORDER BY st.first_name, st.last_name
    """), {
        "subject_id": assignment.subject_id,
        "term": term,
        "year": academic_year
    }).mappings().all()
    
    # Convert records and map 'remarks' to 'comments' for frontend
    formatted_records = []
    for record in records:
        record_dict = dict(record)
        record_dict['comments'] = record_dict.get('remarks', '')  # Map remarks to comments
        formatted_records.append(record_dict)
    
    return {
        "records": formatted_records,
        "assignment_id": assignment.id,
        "subject_id": assignment.subject_id
    }


@router.post("/grades", response_model=dict, dependencies=[Depends(require_permissions(["academic.create", "academic.update"]))])
def create_or_update_grade(
    payload: dict,
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    """Create or update a student's grade"""
    try:
        # Get subject_id from class_name and subject_code
        subject_info = db.execute(text("""
            SELECT s.id as subject_id, ta.id as assignment_id
            FROM teacher_assignments ta
            JOIN classes c ON ta.class_id = c.id
            JOIN subjects s ON ta.subject_id = s.id
            JOIN teachers t ON ta.teacher_id = t.id
            JOIN users u ON t.email = u.email
            WHERE u.id = :user_id AND c.name = :class_name AND s.code = :subject_code
        """), {
            "user_id": user_id,
            "class_name": payload["class_name"],
            "subject_code": payload["subject_code"]
        }).mappings().first()
        
        if not subject_info:
            raise HTTPException(status_code=403, detail="You are not authorized to grade this subject")
        
        # Check if record exists
        existing = db.execute(text("""
            SELECT id FROM academic_records 
            WHERE student_id = :student_id AND subject_id = :subject_id 
            AND term = :term AND academic_year = :year
        """), {
            "student_id": payload["student_id"],
            "subject_id": subject_info.subject_id,
            "term": payload["term"],
            "year": payload["academic_year"]
        }).scalar()
        
        # Use the compute grade function from academic.py
        from app.api.routers.academic import _compute_grade_for_scores
        overall, grade, points = _compute_grade_for_scores(
            db, 
            payload.get("ca_score"), 
            payload.get("exam_score"), 
            payload.get("overall_score")
        )
        
        if existing:
            # Update existing record
            db.execute(text("""
                UPDATE academic_records 
                SET ca_score = :ca, exam_score = :exam, overall_score = :overall,
                    grade = :grade, grade_points = :points, remarks = :remarks,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """), {
                "id": existing,
                "ca": payload.get("ca_score"),
                "exam": payload.get("exam_score"),
                "overall": overall,
                "grade": grade,
                "points": points,
                "remarks": payload.get("comments")
            })
        else:
            # Create new record
            db.execute(text("""
                INSERT INTO academic_records 
                (student_id, subject_id, ca_score, exam_score, overall_score, 
                 grade, grade_points, term, academic_year, remarks)
                VALUES (:student_id, :subject_id, :ca, :exam, :overall, 
                        :grade, :points, :term, :year, :remarks)
            """), {
                "student_id": payload["student_id"],
                "subject_id": subject_info.subject_id,
                "ca": payload.get("ca_score"),
                "exam": payload.get("exam_score"),
                "overall": overall,
                "grade": grade,
                "points": points,
                "term": payload["term"],
                "year": payload["academic_year"],
                "remarks": payload.get("comments")
            })
        
        db.commit()
        return {"message": "Grade saved successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/grades/{class_name}/{subject_code}/stats", response_model=dict, dependencies=[Depends(require_permissions(["academic.read"]))])
def get_class_grade_stats(
    class_name: str,
    subject_code: str,
    term: str = Query("Term 1 Final"),
    academic_year: str = Query("2024"),
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get statistics for class grades"""
    # Verify teacher assignment
    assignment = db.execute(text("""
        SELECT s.id as subject_id
        FROM teacher_assignments ta
        JOIN classes c ON ta.class_id = c.id
        JOIN subjects s ON ta.subject_id = s.id
        JOIN teachers t ON ta.teacher_id = t.id
        JOIN users u ON t.email = u.email
        WHERE u.id = :user_id AND c.name = :class_name AND s.code = :subject_code
    """), {"user_id": user_id, "class_name": class_name, "subject_code": subject_code}).mappings().first()
    
    if not assignment:
        raise HTTPException(status_code=403, detail="You are not assigned to this class")
    
    # Get total students in class
    total_students = db.execute(text("""
        SELECT COUNT(*) FROM students WHERE class_name = :class_name
    """), {"class_name": class_name}).scalar() or 0
    
    # Get graded students count and statistics
    stats = db.execute(text("""
        SELECT 
            COUNT(*) as graded_count,
            COALESCE(AVG(overall_score), 0) as avg_score,
            COALESCE(MAX(overall_score), 0) as max_score,
            COALESCE(MIN(overall_score), 0) as min_score
        FROM academic_records ar
        WHERE ar.subject_id = :subject_id AND ar.term = :term AND ar.academic_year = :year
    """), {
        "subject_id": assignment.subject_id,
        "term": term,
        "year": academic_year
    }).mappings().first()
    
    # Get grade distribution
    grade_dist = db.execute(text("""
        SELECT grade, COUNT(*) as count
        FROM academic_records ar
        WHERE ar.subject_id = :subject_id AND ar.term = :term AND ar.academic_year = :year
            AND grade IS NOT NULL
        GROUP BY grade
    """), {
        "subject_id": assignment.subject_id,
        "term": term,
        "year": academic_year
    }).mappings().all()
    
    return {
        "total_students": total_students,
        "graded_students": stats.graded_count or 0,
        "average_score": float(stats.avg_score) if stats.avg_score else 0.0,
        "highest_score": float(stats.max_score) if stats.max_score else 0.0,
        "lowest_score": float(stats.min_score) if stats.min_score else 0.0,
        "grade_distribution": {g.grade: g.count for g in grade_dist}
    }


# Attendance Management Routes
@router.get("/attendance/{class_name}/{date_str}", response_model=dict, dependencies=[Depends(require_permissions(["attendance.read"]))])
def get_class_attendance(
    class_name: str,
    date_str: str,
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get attendance records for a specific class and date"""
    # Verify teacher can access this class
    class_check = db.execute(text("""
        SELECT c.id as class_id, c.name as class_name
        FROM classes c
        WHERE c.name = :class_name
    """), {"class_name": class_name}).mappings().first()
    
    if not class_check:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Get all students in this class and their attendance for the date
    records = db.execute(text("""
        SELECT s.id as student_id, s.first_name || ' ' || s.last_name as student_name, 
               s.admission_no as student_number, s.class_name,
               a.id as attendance_id, a.status, a.created_at,
               COALESCE(a.status, 'not_marked') as attendance_status
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id 
                               AND a.class_id = :class_id 
                               AND a.date = :date
        WHERE s.class_name = :class_name
        ORDER BY s.first_name, s.last_name
    """), {
        "class_id": class_check.class_id,
        "class_name": class_name,
        "date": date_str
    }).mappings().all()
    
    return {
        "records": [dict(record) for record in records],
        "class_id": class_check.class_id,
        "date": date_str
    }


@router.post("/attendance", response_model=dict, dependencies=[Depends(require_permissions(["attendance.create", "attendance.update"]))])
def mark_attendance(
    payload: dict,
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    """Mark attendance for a student"""
    try:
        # Get class_id from class_name
        class_info = db.execute(text("""
            SELECT id as class_id FROM classes WHERE name = :class_name
        """), {
            "class_name": payload["class_name"]
        }).mappings().first()
        
        if not class_info:
            raise HTTPException(status_code=404, detail="Class not found")
        
        # Get student_id from student identifier
        if "student_id" in payload:
            student_id = payload["student_id"]
        elif "student_number" in payload or "admission_no" in payload:
            # Look up student by admission number
            student_lookup = payload.get("student_number") or payload.get("admission_no")
            student_record = db.execute(text("""
                SELECT id FROM students WHERE admission_no = :admission_no OR id = :student_id
            """), {
                "admission_no": student_lookup,
                "student_id": student_lookup if str(student_lookup).isdigit() else None
            }).scalar()
            
            if not student_record:
                raise HTTPException(status_code=404, detail=f"Student not found with identifier: {student_lookup}")
            student_id = student_record
        else:
            raise HTTPException(status_code=400, detail="Must provide student_id, student_number, or admission_no")
        
        # Check if record exists
        existing = db.execute(text("""
            SELECT id FROM attendance 
            WHERE student_id = :student_id AND class_id = :class_id AND date = :date
        """), {
            "student_id": student_id,
            "class_id": class_info.class_id,
            "date": payload["date"]
        }).scalar()
        
        if existing:
            # Update existing record
            db.execute(text("""
                UPDATE attendance 
                SET status = :status
                WHERE id = :id
            """), {
                "id": existing,
                "status": payload["status"]
            })
        else:
            # Create new record
            db.execute(text("""
                INSERT INTO attendance (student_id, class_id, date, status)
                VALUES (:student_id, :class_id, :date, :status)
            """), {
                "student_id": student_id,
                "class_id": class_info.class_id,
                "date": payload["date"],
                "status": payload["status"]
            })
        
        db.commit()
        return {"message": "Attendance marked successfully", "student_id": student_id, "class_id": class_info.class_id}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/attendance/{class_name}/stats", response_model=dict, dependencies=[Depends(require_permissions(["attendance.read"]))])
def get_attendance_stats(
    class_name: str,
    date: str = Query(...),
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get attendance statistics for a class"""
    # Verify teacher assignment
    assignment = db.execute(text("""
        SELECT c.id as class_id
        FROM teacher_assignments ta
        JOIN classes c ON ta.class_id = c.id
        JOIN teachers t ON ta.teacher_id = t.id
        JOIN users u ON t.email = u.email
        WHERE u.id = :user_id AND c.name = :class_name
    """), {"user_id": user_id, "class_name": class_name}).mappings().first()
    
    if not assignment:
        raise HTTPException(status_code=403, detail="You are not assigned to this class")
    
    # Get total students
    total_students = db.execute(text("""
        SELECT COUNT(*) FROM students WHERE class_name = :class_name
    """), {"class_name": class_name}).scalar() or 0
    
    # Get today's attendance stats
    today_stats = db.execute(text("""
        SELECT 
            status,
            COUNT(*) as count
        FROM attendance a
        WHERE a.class_id = :class_id AND a.date = :date
        GROUP BY status
    """), {
        "class_id": assignment.class_id,
        "date": date
    }).mappings().all()
    
    # Convert to dict
    stats_dict = {stat.status: stat.count for stat in today_stats}
    
    # Calculate overall attendance rate (last 30 days)
    overall_rate = db.execute(text("""
        SELECT 
            (COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0)) as rate
        FROM attendance a
        WHERE a.class_id = :class_id AND a.date >= DATE(:date, '-30 days')
    """), {
        "class_id": assignment.class_id,
        "date": date
    }).scalar() or 0
    
    return {
        "total_students": total_students,
        "present_today": stats_dict.get("present", 0),
        "absent_today": stats_dict.get("absent", 0),
        "late_today": stats_dict.get("late", 0),
        "overall_rate": float(overall_rate),
        "weekly_rate": float(overall_rate),  # Simplified
        "monthly_rate": float(overall_rate)  # Simplified
    }


# Alternative attendance endpoint that matches frontend expectation (with query parameter)
@router.get("/attendance/{class_name}", response_model=dict, dependencies=[Depends(require_permissions(["attendance.read"]))])
def get_class_attendance_query(
    class_name: str,
    date: str = Query(...),
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get attendance records for a specific class and date (query parameter version)"""
    # Verify teacher can access this class
    class_check = db.execute(text("""
        SELECT c.id as class_id, c.name as class_name
        FROM classes c
        WHERE c.name = :class_name
    """), {"class_name": class_name}).mappings().first()
    
    if not class_check:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Get all students in the class with their attendance status for the date
    records = db.execute(text("""
        SELECT 
            s.id as student_id,
            s.first_name || ' ' || s.last_name as student_name,
            s.student_number,
            :class_name as class_name,
            a.id as attendance_id,
            a.status,
            a.created_at,
            COALESCE(a.status, 'not_marked') as attendance_status
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id 
            AND a.class_id = :class_id 
            AND a.date = :date
        WHERE s.class_name = :class_name
        ORDER BY s.first_name, s.last_name
    """), {
        "class_id": class_check.class_id,
        "class_name": class_name,
        "date": date
    }).mappings().all()
    
    return {
        "records": [dict(record) for record in records],
        "class_id": class_check.class_id,
        "date": date
    }


# Grades stats endpoint
@router.get("/grades/{class_name}/{subject}/stats", response_model=dict, dependencies=[Depends(require_permissions(["academic.read"]))])
def get_grades_stats(
    class_name: str,
    subject: str,
    term: str = Query("Term 1 Final"),
    academic_year: str = Query("2024"),
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get grade statistics for a class and subject"""
    # Get subject_id and class_id
    subject_info = db.execute(text("""
        SELECT s.id as subject_id, s.name as subject_name
        FROM subjects s
        WHERE s.code = :subject OR s.name = :subject
    """), {"subject": subject}).mappings().first()
    
    class_info = db.execute(text("""
        SELECT id as class_id FROM classes WHERE name = :class_name
    """), {"class_name": class_name}).mappings().first()
    
    if not subject_info or not class_info:
        raise HTTPException(status_code=404, detail="Subject or class not found")
    
    # Get grade statistics
    stats = db.execute(text("""
        SELECT 
            COUNT(*) as total_students,
            AVG(CAST(overall_score AS DECIMAL)) as average_score,
            MIN(CAST(overall_score AS DECIMAL)) as min_score,
            MAX(CAST(overall_score AS DECIMAL)) as max_score,
            COUNT(CASE WHEN CAST(overall_score AS DECIMAL) >= 50 THEN 1 END) as passing_students,
            COUNT(CASE WHEN grade_points = '4.00' THEN 1 END) as distinction_count,
            COUNT(CASE WHEN grade_points = '3.00' THEN 1 END) as credit_count,
            COUNT(CASE WHEN grade_points = '2.00' THEN 1 END) as pass_count,
            COUNT(CASE WHEN grade_points IN ('1.00', '0.00') THEN 1 END) as fail_count
        FROM academic_records
        WHERE class_id = :class_id 
        AND subject_id = :subject_id 
        AND term = :term 
        AND academic_year = :academic_year
    """), {
        "class_id": class_info.class_id,
        "subject_id": subject_info.subject_id,
        "term": term,
        "academic_year": academic_year
    }).mappings().first()
    
    if not stats or stats.total_students == 0:
        return {
            "total_students": 0,
            "average_score": 0,
            "pass_rate": 0,
            "class_performance": "No data",
            "grade_distribution": {}
        }
    
    pass_rate = (stats.passing_students / stats.total_students) * 100 if stats.total_students > 0 else 0
    
    # Determine class performance level
    avg_score = float(stats.average_score) if stats.average_score else 0
    if avg_score >= 80:
        performance = "Excellent"
    elif avg_score >= 70:
        performance = "Good"
    elif avg_score >= 60:
        performance = "Average"
    elif avg_score >= 50:
        performance = "Below Average"
    else:
        performance = "Poor"
    
    return {
        "total_students": stats.total_students,
        "average_score": round(avg_score, 2),
        "min_score": float(stats.min_score) if stats.min_score else 0,
        "max_score": float(stats.max_score) if stats.max_score else 0,
        "pass_rate": round(pass_rate, 1),
        "class_performance": performance,
        "grade_distribution": {
            "distinction": stats.distinction_count or 0,
            "credit": stats.credit_count or 0,
            "pass": stats.pass_count or 0,
            "fail": stats.fail_count or 0
        }
    }
