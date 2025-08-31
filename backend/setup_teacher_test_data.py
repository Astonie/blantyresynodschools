#!/usr/bin/env python3

import sys
import os
import asyncio
import traceback
from sqlalchemy import text

# Add the parent directory to the path so we can import the app
sys.path.append('/app')

from app.tenancy.service import TenantService
from app.services.security import hash_password
from app.db.session import get_db

async def setup_teacher_data():
    """Set up test teacher data"""
    try:
        # Get database session
        db = next(get_db())
        tenant_service = TenantService(db)
        
        schema_name = 'ndirande_high'
        print(f"Setting up teacher data for schema: {schema_name}")
        
        async with tenant_service.tenant_session(schema_name) as session:
            # Create a test teacher user if not exists
            teacher_email = 'teacher.john.banda@teacher.ndirande-high.edu'
            existing_teacher = session.execute(text(
                "SELECT id FROM users WHERE email = :email"
            ), {"email": teacher_email}).scalar()
            
            if not existing_teacher:
                # Create teacher user
                hashed_password = hash_password('teacher123')
                teacher_id = session.execute(text("""
                    INSERT INTO users (email, hashed_password, full_name, is_active)
                    VALUES (:email, :password, :name, true)
                    RETURNING id
                """), {
                    "email": teacher_email,
                    "password": hashed_password,
                    "name": "John Banda"
                }).scalar()
                
                # Get Teacher role
                teacher_role_id = session.execute(text(
                    "SELECT id FROM roles WHERE name = 'Teacher'"
                )).scalar()
                
                if teacher_role_id:
                    # Assign Teacher role
                    session.execute(text("""
                        INSERT INTO user_roles (user_id, role_id)
                        VALUES (:user_id, :role_id)
                    """), {
                        "user_id": teacher_id,
                        "role_id": teacher_role_id
                    })
                
                print(f"Created teacher user: {teacher_email} with ID: {teacher_id}")
            else:
                teacher_id = existing_teacher
                print(f"Teacher user already exists: {teacher_email} with ID: {teacher_id}")
            
            # Get available classes and subjects
            classes = session.execute(text("SELECT id, name FROM classes LIMIT 3")).mappings().all()
            subjects = session.execute(text("SELECT id, name, code FROM subjects LIMIT 5")).mappings().all()
            
            print(f"Found {len(classes)} classes and {len(subjects)} subjects")
            
            # Create teacher assignments if they don't exist
            for i, class_info in enumerate(classes):
                for j, subject in enumerate(subjects):
                    if j < 2 or (i == 0 and j < 4):  # Assign 2 subjects per class, plus extra for first class
                        existing_assignment = session.execute(text("""
                            SELECT id FROM teacher_assignments 
                            WHERE teacher_id = :teacher_id AND class_id = :class_id AND subject_id = :subject_id
                        """), {
                            "teacher_id": teacher_id,
                            "class_id": class_info.id,
                            "subject_id": subject.id
                        }).scalar()
                        
                        if not existing_assignment:
                            is_primary = (i == 0 and j == 0)  # Make first assignment as form teacher
                            session.execute(text("""
                                INSERT INTO teacher_assignments (teacher_id, class_id, subject_id, academic_year, is_primary)
                                VALUES (:teacher_id, :class_id, :subject_id, '2024', :is_primary)
                            """), {
                                "teacher_id": teacher_id,
                                "class_id": class_info.id,
                                "subject_id": subject.id,
                                "is_primary": is_primary
                            })
                            
                            primary_text = " (Form Teacher)" if is_primary else ""
                            print(f"Created assignment: {class_info.name} - {subject.name} ({subject.code}){primary_text}")
            
            session.commit()
            print("Teacher setup completed successfully!")
            
            # Show summary
            assignments = session.execute(text("""
                SELECT c.name as class_name, s.name as subject_name, s.code as subject_code, ta.is_primary
                FROM teacher_assignments ta
                JOIN classes c ON ta.class_id = c.id
                JOIN subjects s ON ta.subject_id = s.id
                WHERE ta.teacher_id = :teacher_id
                ORDER BY c.name, s.name
            """), {"teacher_id": teacher_id}).mappings().all()
            
            print(f"\nTeacher assignments for {teacher_email}:")
            for assignment in assignments:
                primary_text = " (Form Teacher)" if assignment.is_primary else ""
                print(f"- {assignment.class_name}: {assignment.subject_name} ({assignment.subject_code}){primary_text}")
    
    except Exception as e:
        print(f"Error setting up teacher data: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(setup_teacher_data())
