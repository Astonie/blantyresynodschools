#!/usr/bin/env python3
"""
Quick fix for seeding comprehensive academic data - simplified version
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
        print("🏫 Creating comprehensive academic data for parent portal...")
        
        # First, let's check what we have
        students_query = """
            SELECT s.id, s.first_name, s.last_name, s.admission_no, s.class_name
            FROM students s
            ORDER BY s.id
        """
        students = db.execute(text(students_query)).fetchall()
        print(f"📚 Found {len(students)} students")
        for student in students:
            print(f"  Student ID: {student[0]}, Name: {student[1]} {student[2]}")
        
        # Get subjects - using hardcoded subjects since subjects table doesn't exist
        subjects = [(1, "English Language"), (2, "Mathematics"), (3, "General Science")]
        print(f"📖 Using {len(subjects)} subjects: {[s[1] for s in subjects]}")
        
        if not students or not subjects:
            print("❌ No students or subjects found!")
            return
            
        # Clear existing academic data
        print("🧹 Clearing existing academic and attendance data...")
        db.execute(text("DELETE FROM communications WHERE type = 'academic'"))
        db.execute(text("DELETE FROM attendance"))
        db.execute(text("DELETE FROM academic_records"))
        db.commit()
        
        # Academic year terms
        terms = [
            {"name": "Term 1", "start": date(2024, 1, 15), "mid": date(2024, 3, 1), "end": date(2024, 4, 30)},
            {"name": "Term 2", "start": date(2024, 5, 6), "mid": date(2024, 7, 15), "end": date(2024, 8, 30)},
        ]
        
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
            student_profiles[student[0]] = profiles[i % 4]  # Cycle through profiles
            print(f"  👤 {student[1]} {student[2]}: {student_profiles[student[0]]} student")
        
        # Process each term
        for term in terms:
            print(f"\n📅 Processing {term['name']} ({term['start']} to {term['end']})")
            
            # Generate attendance (school days only - no weekends)
            school_days = []
            current_date = term["start"]
            while current_date <= term["end"]:
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    school_days.append(current_date)
                current_date += timedelta(days=1)
            
            print(f"  📊 Generating attendance for {len(school_days)} school days")
            
            # Generate attendance for each student
            for student in students:
                student_id = student[0]
                profile = student_profiles[student_id]
                
                # Attendance pattern based on profile
                attendance_rate = {"excellent": 0.95, "good": 0.88, "average": 0.85, "struggling": 0.75}
                
                for day in school_days:
                    if random.random() < attendance_rate[profile]:
                        status = "present" if random.random() < 0.95 else "late"
                    else:
                        status = "absent"
                    
                    db.execute(text("""
                        INSERT INTO attendance (student_id, date, status, class_id)
                        VALUES (:student_id, :date, :status, 1)
                    """), {
                        "student_id": student_id,
                        "date": day,
                        "status": status
                    })
            
            # Generate academic records for mid-term and final
            exam_periods = [
                {"type": "mid", "date": term["mid"]},
                {"type": "final", "date": term["end"]}
            ]
            
            for exam_period in exam_periods:
                print(f"  📝 Creating {exam_period['type']}-term exam results...")
                
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
                            "term": f"{term['name']} {exam_period['type'].title()}-term",
                            "ca_score": ca_score,
                            "exam_score": exam_score,
                            "overall_score": overall_score,
                            "grade_points": grade_points
                        })
            
            # Create term report communications
            for student in students:
                student_id = student[0]
                student_name = f"{student[1]} {student[2]}"
                profile = student_profiles[student_id]
                
                # Calculate term GPA
                gpa_map = {"excellent": 3.8, "good": 2.9, "average": 2.3, "struggling": 1.2}
                term_gpa = gpa_map[profile] + random.uniform(-0.3, 0.3)
                
                content = f"""Dear Parent,

{student_name} has completed {term['name']} with a GPA of {term_gpa:.1f}. Performance level: {profile.title()}.

Attendance: {'Excellent' if profile == 'excellent' else 'Good' if profile in ['good', 'average'] else 'Needs Improvement'}

Please review the detailed results in the academic section.

Best regards,
Ndirande High School Academic Office"""
                
                db.execute(text("""
                    INSERT INTO communications (
                        student_id, title, content, type, priority, created_at
                    ) VALUES (
                        :student_id, :title, :content, 'academic', 'high', :created_at
                    )
                """), {
                    "student_id": student_id,
                    "title": f"{term['name']} Academic Report - {student_name}",
                    "content": content,
                    "created_at": term["end"]
                })
        
        db.commit()
        print("\n✅ Academic data seeding completed successfully!")
        print("📊 Generated data:")
        print("   - 2 terms of academic records")
        print("   - Mid-term and final exam results for each term")
        print("   - Daily attendance records")
        print("   - Academic performance communications")
        print("   - Realistic performance profiles for all students")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
