#!/usr/bin/env python3
"""
Minimal academic data seeding - only academic records and communications
"""

import sys
import os
sys.path.append('/app')

import random
from datetime import date, datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.db.session import SessionLocal

def main():
    db = SessionLocal()
    
    try:
        print("🏫 Creating academic data for parent portal...")
        
        # Ensure we're in the right schema
        db.execute(text("SET search_path TO ndirande_high, public"))
        
        # Get students
        students = db.execute(text("SELECT id, first_name, last_name FROM students ORDER BY id")).fetchall()
        print(f"📚 Found {len(students)} students")
        
        if not students:
            print("❌ No students found!")
            return
            
        # Clear existing academic data only
        print("🧹 Clearing existing academic and communication data...")
        db.execute(text("DELETE FROM communications WHERE type = 'academic'"))
        db.execute(text("DELETE FROM academic_records"))
        db.commit()
        
        # Subjects (hardcoded since no subjects table)
        subjects = [(1, "English Language"), (2, "Mathematics"), (3, "General Science")]
        print(f"📖 Using {len(subjects)} subjects: {[s[1] for s in subjects]}")
        
        # Performance profiles
        performance_profiles = {
            "excellent": {"ca_range": (85, 100), "exam_range": (85, 100)},
            "good": {"ca_range": (70, 84), "exam_range": (70, 84)},
            "average": {"ca_range": (60, 79), "exam_range": (55, 79)},
            "struggling": {"ca_range": (40, 65), "exam_range": (35, 65)}
        }
        
        # Assign performance to students
        student_profiles = {}
        for i, student in enumerate(students):
            profiles = ["excellent", "good", "average", "struggling"]
            student_profiles[student[0]] = profiles[i % 4]
            print(f"  👤 {student[1]} {student[2]}: {student_profiles[student[0]]} student")
        
        # Terms
        terms = ["Term 1 Mid-term", "Term 1 Final", "Term 2 Mid-term", "Term 2 Final"]
        term_dates = [date(2024, 3, 1), date(2024, 4, 30), date(2024, 7, 15), date(2024, 8, 30)]
        
        print(f"\n📅 Processing academic records...")
        
        # Generate academic records for each term
        for term_idx, (term, term_date) in enumerate(zip(terms, term_dates)):
            print(f"  📝 Creating {term} results...")
            
            for student in students:
                student_id = student[0]
                profile = student_profiles[student_id]
                
                for subject_id, subject_name in subjects:
                    # Generate scores based on profile
                    ca_min, ca_max = performance_profiles[profile]["ca_range"]
                    exam_min, exam_max = performance_profiles[profile]["exam_range"]
                    
                    ca_score = random.randint(ca_min, ca_max)
                    exam_score = random.randint(exam_min, exam_max)
                    overall_score = round((ca_score * 0.4) + (exam_score * 0.6), 1)
                    
                    # Grade points calculation
                    if overall_score >= 80:
                        grade_points = 4.0
                    elif overall_score >= 70:
                        grade_points = 3.0
                    elif overall_score >= 60:
                        grade_points = 2.0
                    elif overall_score >= 50:
                        grade_points = 1.0
                    else:
                        grade_points = 0.0
                    
                    db.execute(text("""
                        INSERT INTO academic_records (
                            student_id, subject_id, academic_year, term,
                            ca_score, exam_score, overall_score, grade_points,
                            is_finalized, class_id
                        ) VALUES (
                            :student_id, :subject_id, '2024', :term,
                            :ca_score, :exam_score, :overall_score, :grade_points,
                            true, 1
                        )
                    """), {
                        "student_id": student_id,
                        "subject_id": subject_id,
                        "term": term,
                        "ca_score": ca_score,
                        "exam_score": exam_score,
                        "overall_score": overall_score,
                        "grade_points": grade_points
                    })
        
        # Skip communications for now due to foreign key constraints
        print("\n📤 Skipping academic communications (foreign key constraints)...")
        
        db.commit()
        print("\n✅ Academic data seeding completed successfully!")
        print("📊 Generated data:")
        print("   - 4 academic assessment periods (2 terms with mid-term and finals)")
        print("   - Academic records for 3 subjects per student")
        print("   - Realistic performance profiles for all students")
        print(f"   - Total students processed: {len(students)}")
        
        # Let's verify what was created
        total_records = db.execute(text("SELECT COUNT(*) FROM academic_records")).fetchone()[0]
        print(f"   - Total academic records created: {total_records}")
        
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
