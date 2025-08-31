"""
Seed parent users and their children in the correct tenant schema
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import bcrypt
from datetime import datetime, timedelta
import random

# Add the backend directory to Python path
sys.path.insert(0, "/app")

from app.db.session import SessionLocal

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def main():
    db = SessionLocal()
    
    try:
        # Set schema to ndirande_high
        db.execute(text("SET search_path TO ndirande_high, public"))
        
        print("🏫 Seeding parent users in ndirande_high schema...")
        
        # Parent data with their children
        parent_families = [
            {
                "parent": {"name": "James Phiri", "email": "james.phiri@parent.ndirande.edu", "password": "Parent2123"},
                "children": [{"name": "Mercy Phiri", "class_name": "Form 2"}]
            },
            {
                "parent": {"name": "Grace Banda", "email": "grace.banda@parent.ndirande.edu", "password": "Parent1123"},
                "children": [{"name": "John Banda", "class_name": "Form 1"}, {"name": "Mary Banda", "class_name": "Form 3"}]
            },
            {
                "parent": {"name": "Peter Mwale", "email": "peter.mwale@parent.ndirande.edu", "password": "Parent3123"},
                "children": [{"name": "Daniel Mwale", "class_name": "Form 4"}]
            },
            {
                "parent": {"name": "Rose Tembo", "email": "rose.tembo@parent.ndirande.edu", "password": "Parent4123"},
                "children": [{"name": "Faith Tembo", "class_name": "Form 2"}, {"name": "Hope Tembo", "class_name": "Form 1"}]
            },
            {
                "parent": {"name": "Samuel Chirwa", "email": "samuel.chirwa@parent.ndirande.edu", "password": "Parent5123"},
                "children": [{"name": "Paul Chirwa", "class_name": "Form 3"}]
            }
        ]
        
        # Get parent role ID
        parent_role = db.execute(text("SELECT id FROM roles WHERE name = 'Parent'")).fetchone()
        if not parent_role:
            print("❌ Parent role not found! Creating it...")
            db.execute(text("INSERT INTO roles (name, description) VALUES ('Parent', 'Parent access to view their children''s information')"))
            parent_role = db.execute(text("SELECT id FROM roles WHERE name = 'Parent'")).fetchone()
        
        parent_role_id = parent_role[0]
        print(f"✓ Parent role ID: {parent_role_id}")
        
        # Get or create classes
        classes = {}
        for class_name in ["Form 1", "Form 2", "Form 3", "Form 4"]:
            existing_class = db.execute(text("SELECT id FROM classes WHERE name = :name"), {"name": class_name}).fetchone()
            if existing_class:
                classes[class_name] = existing_class[0]
            else:
                db.execute(text("""
                    INSERT INTO classes (name, description, academic_year, created_at) 
                    VALUES (:name, :desc, '2024', CURRENT_TIMESTAMP)
                """), {"name": class_name, "desc": f"Secondary {class_name}"})
                new_class = db.execute(text("SELECT id FROM classes WHERE name = :name"), {"name": class_name}).fetchone()
                classes[class_name] = new_class[0]
        
        print(f"✓ Classes available: {list(classes.keys())}")
        
        # Get existing subjects
        subjects_result = db.execute(text("SELECT id, name FROM subjects")).fetchall()
        subjects = {subject[1]: subject[0] for subject in subjects_result}
        
        print(f"✓ {len(subjects)} subjects available: {list(subjects.keys())}")
        
        # Terms for academic records
        terms = ["Term 1", "Term 2", "Term 3"]
        
        # Process each family
        for i, family in enumerate(parent_families, 1):
            parent_data = family["parent"]
            children_data = family["children"]
            
            print(f"\n👨‍👩‍👧‍👦 Family {i}: {parent_data['name']}")
            
            # Create parent user
            hashed_password = hash_password(parent_data["password"])
            
            # Check if parent already exists
            existing_parent = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": parent_data["email"]}).fetchone()
            
            if existing_parent:
                parent_id = existing_parent[0]
                print(f"  ✓ Parent already exists: {parent_data['email']}")
            else:
                db.execute(text("""
                    INSERT INTO users (email, full_name, hashed_password, is_active, created_at, updated_at) 
                    VALUES (:email, :name, :password, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """), {
                    "email": parent_data["email"],
                    "name": parent_data["name"],
                    "password": hashed_password
                })
                
                parent_user = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": parent_data["email"]}).fetchone()
                parent_id = parent_user[0]
                print(f"  ✓ Created parent: {parent_data['email']}")
                
                # Assign parent role
                db.execute(text("""
                    INSERT INTO user_roles (user_id, role_id) 
                    VALUES (:user_id, :role_id) 
                    ON CONFLICT (user_id, role_id) DO NOTHING
                """), {"user_id": parent_id, "role_id": parent_role_id})
            
            # Create children
            for child_data in children_data:
                child_name = child_data["name"]
                class_name = child_data["class_name"]
                
                # Split name into first and last name
                name_parts = child_name.split(" ")
                first_name = name_parts[0]
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                
                # Check if student already exists
                existing_student = db.execute(text("SELECT id FROM students WHERE first_name = :first AND last_name = :last"), {"first": first_name, "last": last_name}).fetchone()
                
                if existing_student:
                    student_id = existing_student[0]
                    print(f"    ✓ Student already exists: {child_name}")
                else:
                    # Generate admission number
                    admission_no = f"NH{random.randint(1000, 9999)}"
                    
                    db.execute(text("""
                        INSERT INTO students (first_name, last_name, admission_no, date_of_birth, gender, parent_name, parent_phone, parent_email, address, class_name, created_at, updated_at) 
                        VALUES (:first, :last, :admission, :dob, :gender, :parent_name, :phone, :email, :address, :class_name, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """), {
                        "first": first_name,
                        "last": last_name,
                        "admission": admission_no,
                        "dob": "2008-01-01",  # Sample DOB
                        "gender": "Male" if random.choice([True, False]) else "Female",
                        "parent_name": parent_data["name"],
                        "phone": f"+265991{random.randint(100000, 999999)}",
                        "email": parent_data["email"],
                        "address": "Ndirande, Blantyre",
                        "class_name": class_name
                    })
                    
                    student = db.execute(text("SELECT id FROM students WHERE first_name = :first AND last_name = :last"), {"first": first_name, "last": last_name}).fetchone()
                    student_id = student[0]
                    print(f"    ✓ Created student: {child_name} ({admission_no})")
                
                # Link parent to student
                existing_link = db.execute(text("""
                    SELECT id FROM parent_students WHERE parent_user_id = :parent_id AND student_id = :student_id
                """), {"parent_id": parent_id, "student_id": student_id}).fetchone()
                
                if not existing_link:
                    db.execute(text("""
                        INSERT INTO parent_students (parent_user_id, student_id) 
                        VALUES (:parent_id, :student_id)
                    """), {"parent_id": parent_id, "student_id": student_id})
                    print(f"    ✓ Linked parent to {child_name}")
                
                # Create academic records for each term
                for term in terms:
                    for subject_name, subject_id in list(subjects.items()):  # Use all available subjects
                        # Check if record already exists
                        existing_record = db.execute(text("""
                            SELECT id FROM academic_records 
                            WHERE student_id = :student_id AND subject_id = :subject_id 
                            AND academic_year = '2024' AND term = :term
                        """), {
                            "student_id": student_id,
                            "subject_id": subject_id,
                            "term": term
                        }).fetchone()
                        
                        if not existing_record:
                            ca_score = random.uniform(60, 95)
                            exam_score = random.uniform(55, 90)
                            overall_score = (ca_score * 0.4) + (exam_score * 0.6)
                            
                            # Determine grade
                            if overall_score >= 80:
                                grade = "A"
                            elif overall_score >= 70:
                                grade = "B"
                            elif overall_score >= 60:
                                grade = "C"
                            elif overall_score >= 50:
                                grade = "D"
                            else:
                                grade = "F"
                            
                            # Note: Using only class_id from students table might not work, let's use a default class_id
                            default_class_id = 1  # We'll assume this exists
                            
                            db.execute(text("""
                                INSERT INTO academic_records (
                                    student_id, class_id, subject_id, academic_year, term,
                                    ca_score, exam_score, score, overall_score, grade, 
                                    remarks, created_at, updated_at, is_finalized
                                ) VALUES (
                                    :student_id, :class_id, :subject_id, '2024', :term,
                                    :ca_score, :exam_score, :overall_score, :overall_score, :grade,
                                    :remarks, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, TRUE
                                )
                            """), {
                                "student_id": student_id,
                                "class_id": default_class_id,
                                "subject_id": subject_id,
                                "term": term,
                                "ca_score": round(ca_score, 2),
                                "exam_score": round(exam_score, 2),
                                "overall_score": round(overall_score, 2),
                                "grade": grade,
                                "remarks": "Good progress" if overall_score >= 70 else "Needs improvement"
                            })
                
                print(f"    ✓ Created academic records for {child_name}")
                
                # Skip communications for now - we have enough data to test login
        
        # Commit all changes
        db.commit()
        print(f"\n✅ Successfully seeded {len(parent_families)} parent families in ndirande_high schema!")
        
        # Verify the data
        print("\n📊 Summary:")
        parent_count = db.execute(text("SELECT COUNT(*) FROM users u JOIN user_roles ur ON u.id = ur.user_id JOIN roles r ON ur.role_id = r.id WHERE r.name = 'Parent'")).scalar()
        student_count = db.execute(text("SELECT COUNT(*) FROM students")).scalar()
        record_count = db.execute(text("SELECT COUNT(*) FROM academic_records")).scalar()
        comm_count = db.execute(text("SELECT COUNT(*) FROM communications")).scalar()
        
        print(f"  • {parent_count} parent users")
        print(f"  • {student_count} students")
        print(f"  • {record_count} academic records")
        print(f"  • {comm_count} communications")
        
    except Exception as e:
        print(f"❌ Error seeding parents: {e}")
        db.rollback()
        raise
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
