import os
os.environ['TENANT'] = 'ndirande'

from app.db.session import tenant_session
from sqlalchemy import text
import hashlib

# Create connection
with tenant_session('ndirande') as tenant_db:
    try:
        print("Creating parent user for testing...")
        
        # Check if Parent role exists
        parent_role = tenant_db.execute(text("SELECT id FROM roles WHERE name = 'Parent (Restricted)'")).scalar()
        if not parent_role:
            print("Creating Parent (Restricted) role...")
            parent_role_result = tenant_db.execute(text("INSERT INTO roles (name) VALUES ('Parent (Restricted)') RETURNING id"))
            parent_role = parent_role_result.scalar()
            tenant_db.commit()
            print(f"Created Parent (Restricted) role with ID: {parent_role}")
        else:
            print(f"Found existing Parent (Restricted) role with ID: {parent_role}")
        
        # Create a test parent user
        parent_email = "parent@test.com"
        parent_password = "password123"
        hashed_password = hashlib.sha256(parent_password.encode()).hexdigest()
        
        # Check if parent user already exists
        existing_parent = tenant_db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": parent_email}).scalar()
        
        if existing_parent:
            print(f"Parent user already exists with ID: {existing_parent}")
            parent_id = existing_parent
        else:
            # Create parent user
            parent_result = tenant_db.execute(text("""
                INSERT INTO users (email, hashed_password, full_name, is_active) 
                VALUES (:email, :password, :name, true) 
                RETURNING id
            """), {
                "email": parent_email,
                "password": hashed_password,
                "name": "Test Parent"
            })
            parent_id = parent_result.scalar()
            tenant_db.commit()
            print(f"Created parent user with ID: {parent_id}")
        
        # Assign parent role
        existing_role = tenant_db.execute(text("SELECT 1 FROM user_roles WHERE user_id = :user_id AND role_id = :role_id"), {
            "user_id": parent_id, "role_id": parent_role
        }).scalar()
        
        if not existing_role:
            tenant_db.execute(text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"), {
                "user_id": parent_id, "role_id": parent_role
            })
            tenant_db.commit()
            print(f"Assigned Parent (Restricted) role to user {parent_id}")
        else:
            print(f"User {parent_id} already has Parent (Restricted) role")
        
        # Find existing students to create relationships
        students = tenant_db.execute(text("SELECT id, first_name, last_name, admission_no FROM students LIMIT 3")).fetchall()
        print(f"Found {len(students)} students to associate with parent")
        
        if students:
            # Create parent-student relationships
            for student in students:
                existing_relationship = tenant_db.execute(text("""
                    SELECT 1 FROM parent_students WHERE parent_user_id = :parent_id AND student_id = :student_id
                """), {"parent_id": parent_id, "student_id": student[0]}).scalar()
                
                if not existing_relationship:
                    tenant_db.execute(text("""
                        INSERT INTO parent_students (parent_user_id, student_id) 
                        VALUES (:parent_id, :student_id)
                    """), {"parent_id": parent_id, "student_id": student[0]})
                    print(f"Associated parent with student: {student[1]} {student[2]} (ID: {student[0]})")
            
            tenant_db.commit()
            print("Parent-student relationships created successfully")
        
        print(f"\n=== TEST PARENT ACCOUNT CREATED ===")
        print(f"Email: {parent_email}")
        print(f"Password: {parent_password}")
        print(f"Tenant: ndirande")
        print(f"Associated with {len(students)} children")
        print("You can now test the parent portal!")

    except Exception as e:
        print(f"Error: {e}")
        tenant_db.rollback()
