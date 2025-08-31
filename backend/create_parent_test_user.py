import os
os.environ['TENANT'] = 'ndirande'

from app.db.session import tenant_session
from sqlalchemy import text
import hashlib

# Create connection
with tenant_session('ndirande') as tenant_db:
    try:
        print("Creating parent user for UI testing...")
        
        # Get the Parent (Restricted) role ID
        parent_role = tenant_db.execute(text("SELECT id FROM roles WHERE name = 'Parent (Restricted)'")).scalar()
        if not parent_role:
            print("❌ Parent (Restricted) role not found! Run enhance_security.py first.")
            exit(1)
        print(f"✅ Found Parent (Restricted) role with ID: {parent_role}")
        
        # Create a test parent user
        parent_email = "parent.test@ndirande.edu"
        parent_password = "ParentTest123"
        hashed_password = hashlib.sha256(parent_password.encode()).hexdigest()
        
        # Check if parent user already exists
        existing_parent = tenant_db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": parent_email}).scalar()
        
        if existing_parent:
            print(f"✅ Parent user already exists with ID: {existing_parent}")
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
                "name": "Maria Ndirande"
            })
            parent_id = parent_result.scalar()
            print(f"✅ Created parent user with ID: {parent_id}")
        
        # Ensure parent role is assigned
        existing_role = tenant_db.execute(text("SELECT 1 FROM user_roles WHERE user_id = :user_id AND role_id = :role_id"), {
            "user_id": parent_id, "role_id": parent_role
        }).scalar()
        
        if not existing_role:
            tenant_db.execute(text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"), {
                "user_id": parent_id, "role_id": parent_role
            })
            print(f"✅ Assigned Parent (Restricted) role to user {parent_id}")
        else:
            print(f"✅ User {parent_id} already has Parent (Restricted) role")
        
        # Find existing students to create relationships
        students = tenant_db.execute(text("SELECT id, first_name, last_name, admission_no FROM students ORDER BY first_name LIMIT 2")).fetchall()
        print(f"✅ Found {len(students)} students to associate with parent")
        
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
                    print(f"✅ Associated parent with student: {student[1]} {student[2]} (Admission: {student[3]})")
                else:
                    print(f"✅ Parent already associated with: {student[1]} {student[2]} (Admission: {student[3]})")
        
        print(f"\n{'='*50}")
        print(f"🎯 PARENT TEST ACCOUNT READY!")
        print(f"{'='*50}")
        print(f"📧 Email: {parent_email}")
        print(f"🔑 Password: {parent_password}")
        print(f"🏢 Tenant: ndirande")
        print(f"👶 Children: {len(students)}")
        print(f"🌐 URL: http://localhost:5174")
        print(f"{'='*50}")
        print(f"📱 TESTING STEPS:")
        print(f"1. Go to http://localhost:5174")
        print(f"2. Login with the credentials above")
        print(f"3. You should be redirected to /app/parent")
        print(f"4. Test the parent-only features!")
        print(f"{'='*50}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
