#!/usr/bin/env python3
"""
Check and fix parent_students table structure for parent access system
"""
import sys
sys.path.append('/app')

from app.db.session import SessionLocal
from sqlalchemy import text
from datetime import datetime

def check_and_fix_parent_students_table():
    print('👨‍👩‍👧‍👦 CHECKING PARENT_STUDENTS TABLE')
    print('=' * 45)
    
    db = SessionLocal()
    try:
        # Use ndirande_high as test schema
        db.execute(text('SET search_path TO "ndirande_high"'))
        
        print('\n1️⃣ Checking if parent_students table exists...')
        
        # Check if table exists
        table_exists = db.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = 'parent_students' AND table_schema = current_schema()
        """)).scalar()
        
        if table_exists:
            print('   ✅ parent_students table exists')
            
            # Check structure
            columns = db.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'parent_students' 
                ORDER BY ordinal_position
            """)).fetchall()
            
            print('   📋 Current structure:')
            for col_name, data_type, nullable in columns:
                print(f'      {col_name}: {data_type} {"NULL" if nullable == "YES" else "NOT NULL"}')
                
        else:
            print('   ❌ parent_students table does not exist')
            print('   🔧 Creating parent_students table...')
            
            # Create the table
            db.execute(text("""
                CREATE TABLE parent_students (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                    relationship VARCHAR(50) DEFAULT 'parent',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, student_id)
                )
            """))
            
            print('   ✅ parent_students table created successfully')
            db.commit()
            
        print('\n2️⃣ Creating parent users for existing students...')
        
        # Get first 5 students to create parents for
        students = db.execute(text("""
            SELECT id, first_name, last_name, admission_no 
            FROM students 
            ORDER BY id 
            LIMIT 5
        """)).fetchall()
        
        print(f'   📊 Creating parents for {len(students)} students')
        
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        for student_id, first_name, last_name, admission_no in students:
            # Create parent email and credentials
            parent_email = f'parent.{first_name.lower()}.{last_name.lower()}@parent.ndirande-high.edu'
            parent_name = f'Parent of {first_name} {last_name}'
            hashed_password = pwd_context.hash('parent123')
            
            try:
                # Check if parent already exists
                existing_parent = db.execute(text('SELECT id FROM users WHERE email = :email'), 
                                           {'email': parent_email}).scalar()
                
                if not existing_parent:
                    # Create parent user
                    db.execute(text("""
                        INSERT INTO users (email, full_name, hashed_password, is_active)
                        VALUES (:email, :name, :pwd, :active)
                    """), {
                        'email': parent_email,
                        'name': parent_name,
                        'pwd': hashed_password,
                        'active': True
                    })
                    
                    # Get the created parent ID
                    parent_id = db.execute(text('SELECT id FROM users WHERE email = :email'), 
                                         {'email': parent_email}).scalar()
                    
                    # Assign Parent role (ID 7)
                    db.execute(text("""
                        INSERT INTO user_roles (user_id, role_id)
                        VALUES (:uid, :rid)
                        ON CONFLICT (user_id, role_id) DO NOTHING
                    """), {'uid': parent_id, 'rid': 7})
                    
                else:
                    parent_id = existing_parent
                
                # Create parent-student relationship
                db.execute(text("""
                    INSERT INTO parent_students (user_id, student_id, relationship, created_at)
                    VALUES (:pid, :sid, :rel, :created)
                    ON CONFLICT (user_id, student_id) DO NOTHING
                """), {
                    'pid': parent_id,
                    'sid': student_id,
                    'rel': 'parent',
                    'created': datetime.now()
                })
                
                print(f'   ✅ {parent_email} → {first_name} {last_name}')
                
            except Exception as e:
                print(f'   ⚠️ Error creating parent for {first_name} {last_name}: {e}')
        
        db.commit()
        
        print('\n3️⃣ Verifying parent access...')
        
        # Test parent relationships
        parent_relationships = db.execute(text("""
            SELECT u.email, u.full_name, s.first_name, s.last_name, s.admission_no
            FROM parent_students ps
            JOIN users u ON ps.user_id = u.id
            JOIN students s ON ps.student_id = s.id
            ORDER BY u.email
        """)).fetchall()
        
        print(f'   📊 Found {len(parent_relationships)} parent-student relationships:')
        for parent_email, parent_name, student_fname, student_lname, admission_no in parent_relationships:
            print(f'      {parent_email} → {student_fname} {student_lname} ({admission_no})')
        
        print('\n🎯 PARENT ACCESS INFRASTRUCTURE STATUS:')
        print('   ✅ parent_students table created/verified')
        print('   ✅ Parent users created with credentials')
        print('   ✅ Parent-student relationships established')
        print('   ✅ Ready for parent login and report card access!')
        
    finally:
        db.close()

if __name__ == "__main__":
    check_and_fix_parent_students_table()
