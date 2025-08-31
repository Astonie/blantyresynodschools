#!/usr/bin/env python3
"""
Add parent users using the backend's database connection
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

def create_parents():
    # Use the same database connection as the backend
    DATABASE_URL = "postgresql://admin:admin123@localhost:5432/synod_schools"
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Password hashing
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash("parent123")  # Default parent password
    
    try:
        # Set schema
        session.execute(text('SET search_path TO "ndirande_high", public'))
        
        print("=== Creating Parent Users ===")
        
        # Create parent users
        parent_users = [
            ('mary.tembo@parent.ndirande-high.edu', 'Mary Tembo'),
            ('john.banda@parent.ndirande-high.edu', 'John Banda Sr.'),
            ('grace.mwale@parent.ndirande-high.edu', 'Grace Mwale')
        ]
        
        created_users = []
        
        for email, full_name in parent_users:
            try:
                # Check if user already exists
                existing = session.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email}).scalar()
                
                if existing:
                    print(f"User {email} already exists")
                    created_users.append((existing, email, full_name))
                    continue
                
                # Create user
                result = session.execute(text("""
                    INSERT INTO users (email, full_name, hashed_password, is_active, created_at, updated_at)
                    VALUES (:email, :full_name, :hashed_password, true, NOW(), NOW())
                    RETURNING id
                """), {
                    "email": email,
                    "full_name": full_name,
                    "hashed_password": hashed_password
                })
                
                user_id = result.scalar()
                created_users.append((user_id, email, full_name))
                print(f"✅ Created user: {full_name} ({email}) with ID: {user_id}")
                
            except Exception as e:
                print(f"❌ Error creating user {email}: {e}")
                continue
        
        # Get Parent role ID
        parent_role_id = session.execute(text("SELECT id FROM roles WHERE name = 'Parent'")).scalar()
        
        if not parent_role_id:
            print("❌ Parent role not found")
            return
        
        print(f"Parent role ID: {parent_role_id}")
        
        # Assign Parent role to users
        for user_id, email, full_name in created_users:
            try:
                session.execute(text("""
                    INSERT INTO user_roles (user_id, role_id) 
                    VALUES (:user_id, :role_id) 
                    ON CONFLICT DO NOTHING
                """), {
                    "user_id": user_id,
                    "role_id": parent_role_id
                })
                print(f"✅ Assigned Parent role to {full_name}")
                
            except Exception as e:
                print(f"❌ Error assigning role to {email}: {e}")
        
        # Create parent-student relationships
        relationships = [
            ('mary.tembo@parent.ndirande-high.edu', 'Hope', 'Tembo'),
            ('john.banda@parent.ndirande-high.edu', 'John', 'Banda'),
            ('grace.mwale@parent.ndirande-high.edu', 'Joseph', 'Mwale')
        ]
        
        print("\n=== Creating Parent-Student Relationships ===")
        
        for parent_email, student_first, student_last in relationships:
            try:
                result = session.execute(text("""
                    INSERT INTO parent_students (parent_user_id, student_id)
                    SELECT u.id, s.id 
                    FROM users u, students s 
                    WHERE u.email = :parent_email 
                    AND s.first_name = :first_name AND s.last_name = :last_name
                    ON CONFLICT DO NOTHING
                    RETURNING parent_user_id, student_id
                """), {
                    "parent_email": parent_email,
                    "first_name": student_first,
                    "last_name": student_last
                })
                
                relationship = result.fetchone()
                if relationship:
                    print(f"✅ Linked {parent_email} to {student_first} {student_last}")
                else:
                    print(f"⚠️ Could not link {parent_email} to {student_first} {student_last} (student may not exist)")
                
            except Exception as e:
                print(f"❌ Error creating relationship {parent_email} -> {student_first} {student_last}: {e}")
        
        session.commit()
        
        # Show created relationships
        print("\n=== Created Parent-Student Relationships ===")
        
        result = session.execute(text("""
            SELECT 
                u.email, 
                u.full_name as parent_name,
                s.first_name || ' ' || s.last_name as child_name,
                s.admission_no,
                s.class_name
            FROM users u
            JOIN parent_students ps ON u.id = ps.parent_user_id
            JOIN students s ON ps.student_id = s.id
            WHERE u.email LIKE '%@parent.ndirande-high.edu'
            ORDER BY u.email
        """))
        
        relationships = result.fetchall()
        for rel in relationships:
            print(f"👨‍👩‍👧‍👦 {rel.parent_name} -> {rel.child_name} ({rel.admission_no}) in {rel.class_name}")
        
        print(f"\n🎉 Created {len(relationships)} parent-student relationships!")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    create_parents()
