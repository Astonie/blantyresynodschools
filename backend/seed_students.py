#!/usr/bin/env python3
"""
Script to seed sample students across all tenant schools.
"""

import sys
import os
import random
from datetime import datetime, date
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.session import SessionLocal


# Sample student data templates
FIRST_NAMES = [
    "John", "Mary", "Peter", "Grace", "James", "Faith", "Michael", "Mercy", 
    "David", "Ruth", "Paul", "Sarah", "Joseph", "Elizabeth", "Daniel", "Rose",
    "Samuel", "Martha", "Benjamin", "Hannah", "Isaac", "Rebecca", "Moses", "Rachel",
    "Emmanuel", "Esther", "Joshua", "Naomi", "Caleb", "Lydia"
]

LAST_NAMES = [
    "Banda", "Phiri", "Mwale", "Tembo", "Nyirenda", "Chirwa", "Kachingwe", "Moyo",
    "Kumwenda", "Mbewe", "Gondwe", "Mhone", "Lungu", "Zimba", "Chisale", "Msiska",
    "Kalulu", "Chikonde", "Makoko", "Mvula", "Chidothi", "Namalenga", "Kathumba", "Masamba"
]

GENDERS = ["Male", "Female"]
CLASSES = ["Form 1", "Form 2", "Form 3", "Form 4", "Standard 1", "Standard 2", "Standard 3", 
           "Standard 4", "Standard 5", "Standard 6", "Standard 7", "Standard 8"]


def generate_student_data(school_name: str, count: int = 50):
    """Generate sample student data for a school."""
    students = []
    used_admission_numbers = set()
    
    # Get school prefix for admission numbers
    school_prefix = "".join([word[0].upper() for word in school_name.split()[:2]])
    
    for i in range(count):
        # Generate unique admission number
        while True:
            admission_no = f"{school_prefix}{random.randint(1000, 9999)}"
            if admission_no not in used_admission_numbers:
                used_admission_numbers.add(admission_no)
                break
        
        # Generate birth date (age 6-18)
        birth_year = datetime.now().year - random.randint(6, 18)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        birth_date = date(birth_year, birth_month, birth_day)
        
        # Generate parent contact
        parent_phone = f"+265-{random.randint(800000000, 999999999)}"
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        parent_email = f"{first_name.lower()}.{last_name.lower()}.parent@gmail.com"
        
        student = {
            "first_name": first_name,
            "last_name": last_name,
            "admission_no": admission_no,
            "date_of_birth": birth_date.isoformat(),
            "gender": random.choice(GENDERS),
            "parent_name": f"{random.choice(FIRST_NAMES)} {last_name}",
            "parent_phone": parent_phone,
            "parent_email": parent_email,
            "address": f"{random.choice(['Area 1', 'Area 2', 'Area 3', 'Area 25', 'Area 47'])}, Lilongwe",
            "class_name": random.choice(CLASSES)
        }
        students.append(student)
    
    return students


def seed_students_for_all_schools():
    """Seed students for all tenant schools."""
    db = SessionLocal()
    try:
        # Get all tenant schools
        tenants_result = db.execute(text("SELECT name, slug FROM public.tenants ORDER BY name"))
        tenants = tenants_result.fetchall()
        
        print(f"🎓 Seeding students for {len(tenants)} schools...")
        print("=" * 60)
        
        total_students_created = 0
        
        for tenant in tenants:
            school_name, slug = tenant
            print(f"\n🏫 {school_name} ({slug})")
            
            try:
                # Switch to tenant schema (using underscore version)
                schema_name = slug.replace('-', '_')
                db.execute(text(f'SET search_path TO "{schema_name}", public'))
                
                # Check if students already exist
                existing_count = db.execute(text("SELECT COUNT(*) FROM students")).scalar()
                if existing_count > 0:
                    print(f"   ℹ️  Already has {existing_count} students. Skipping...")
                    continue
                
                # Generate student data
                students_data = generate_student_data(school_name, count=30)  # 30 students per school
                
                # Insert students
                for student in students_data:
                    try:
                        db.execute(text("""
                            INSERT INTO students (
                                first_name, last_name, admission_no, date_of_birth, gender,
                                parent_name, parent_phone, parent_email, address, class_name
                            ) VALUES (
                                :first_name, :last_name, :admission_no, :date_of_birth, :gender,
                                :parent_name, :parent_phone, :parent_email, :address, :class_name
                            )
                        """), student)
                        
                    except Exception as e:
                        print(f"   ⚠️  Error inserting student {student['admission_no']}: {e}")
                        continue
                
                db.commit()
                
                # Verify insertion
                final_count = db.execute(text("SELECT COUNT(*) FROM students")).scalar()
                students_created = final_count - existing_count
                total_students_created += students_created
                
                print(f"   ✅ Successfully created {students_created} students")
                
            except Exception as e:
                print(f"   ❌ Error seeding {school_name}: {e}")
                db.rollback()
                continue
        
        print("\n" + "=" * 60)
        print(f"🎉 Student seeding completed!")
        print(f"📊 Total students created: {total_students_created}")
        print(f"🏫 Schools processed: {len(tenants)}")
        
        # Show summary
        print("\n📋 Summary by school:")
        for tenant in tenants:
            school_name, slug = tenant
            schema_name = slug.replace('-', '_')
            db.execute(text(f'SET search_path TO "{schema_name}", public'))
            count = db.execute(text("SELECT COUNT(*) FROM students")).scalar()
            print(f"   • {school_name}: {count} students")
            
    except Exception as e:
        print(f"❌ Error during student seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Starting student seeding process...")
    seed_students_for_all_schools()
    print("✨ Student seeding process completed!")
