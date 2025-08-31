"""
Comprehensive Parent Portal Data Seeding Script
Creates realistic academic data for parents including:
- Two complete terms (Term 1 & Term 2) with mid-term and final exams
- Detailed attendance records
- Progress tracking and communications
- Real-world academic scenarios
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import bcrypt
from datetime import datetime, timedelta, date
import random

sys.path.insert(0, "/app")
from app.db.session import SessionLocal

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def generate_realistic_grade(base_performance="average", exam_type="midterm"):
    """Generate realistic grades based on student performance profile"""
    profiles = {
        "excellent": {"midterm": (85, 95), "final": (88, 98), "ca": (80, 95)},
        "good": {"midterm": (70, 85), "final": (75, 88), "ca": (68, 85)},
        "average": {"midterm": (55, 75), "final": (58, 78), "ca": (50, 75)},
        "struggling": {"midterm": (35, 60), "final": (40, 65), "ca": (30, 60)},
    }
    
    min_score, max_score = profiles[base_performance][exam_type]
    return round(random.uniform(min_score, max_score), 1)

def get_grade_from_score(score):
    """Convert numerical score to letter grade"""
    if score >= 90: return "A+"
    elif score >= 85: return "A"
    elif score >= 80: return "B+"
    elif score >= 75: return "B"
    elif score >= 70: return "C+"
    elif score >= 65: return "C"
    elif score >= 60: return "D+"
    elif score >= 55: return "D"
    elif score >= 50: return "E"
    else: return "F"

def get_attendance_status(attendance_profile="regular"):
    """Generate attendance status based on student profile"""
    profiles = {
        "excellent": {"present": 95, "late": 4, "absent": 1},
        "regular": {"present": 88, "late": 8, "absent": 4},
        "irregular": {"present": 75, "late": 12, "absent": 13},
    }
    
    rand = random.randint(1, 100)
    if rand <= profiles[attendance_profile]["present"]:
        return "present"
    elif rand <= profiles[attendance_profile]["present"] + profiles[attendance_profile]["late"]:
        return "late"
    else:
        return "absent"

def main():
    db = SessionLocal()
    
    try:
        # Set schema to ndirande_high
        db.execute(text("SET search_path TO ndirande_high, public"))
        
        print("🏫 Creating comprehensive academic data for parent portal...")
        
        # Academic year and terms setup
        academic_year = "2024"
        terms = [
            {"name": "Term 1", "start": date(2024, 1, 15), "mid": date(2024, 3, 15), "end": date(2024, 4, 30)},
            {"name": "Term 2", "start": date(2024, 5, 6), "mid": date(2024, 7, 15), "end": date(2024, 8, 30)},
        ]
        
        # Get all parent families we created
        parent_families = db.execute(text("""
            SELECT u.id as parent_id, u.full_name as parent_name, u.email,
                   s.id as student_id, s.first_name, s.last_name, s.admission_no, s.class_name
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            JOIN parent_students ps ON u.id = ps.parent_user_id
            JOIN students s ON ps.student_id = s.id
            WHERE r.name = 'Parent' AND u.email LIKE '%@parent.ndirande.edu'
            ORDER BY u.id, s.first_name
        """)).fetchall()
        
        print(f"📚 Found {len(parent_families)} parent-student relationships to process")
        
        # Get subjects
        subjects = db.execute(text("SELECT id, name FROM subjects ORDER BY name")).fetchall()
        subject_list = [(s[0], s[1]) for s in subjects]
        print(f"📖 Working with {len(subject_list)} subjects: {[s[1] for s in subject_list]}")
        
        # Clear existing academic records and attendance
        print("🧹 Clearing existing academic and attendance data...")
        db.execute(text("DELETE FROM attendance"))
        db.execute(text("DELETE FROM academic_records"))
        db.execute(text("DELETE FROM communications WHERE type IN ('academic', 'attendance', 'report')"))
        
        # Student performance profiles (for realistic variation)
        student_profiles = {}
        attendance_profiles = {}
        
        for family in parent_families:
            student_id = family[3]
            student_name = f"{family[4]} {family[5]}"
            
            # Assign random performance and attendance profiles
            perf_profile = random.choice(["excellent", "good", "average", "struggling"])
            att_profile = random.choice(["excellent", "regular", "irregular"])
            
            student_profiles[student_id] = perf_profile
            attendance_profiles[student_id] = att_profile
            
            print(f"  👤 {student_name}: {perf_profile} student, {att_profile} attendance")
        
        # Process each term
        for term_info in terms:
            term_name = term_info["name"]
            term_start = term_info["start"]
            term_mid = term_info["mid"]
            term_end = term_info["end"]
            
            print(f"\n📅 Processing {term_name} ({term_start} to {term_end})")
            
            # Generate attendance records for each school day
            current_date = term_start
            school_days = []
            
            while current_date <= term_end:
                # Skip weekends (Saturday=5, Sunday=6)
                if current_date.weekday() < 5:
                    school_days.append(current_date)
                current_date += timedelta(days=1)
            
            print(f"  📊 Generating attendance for {len(school_days)} school days")
            
            # Create attendance records
            for family in parent_families:
                student_id = family[3]
                student_name = f"{family[4]} {family[5]}"
                att_profile = attendance_profiles[student_id]
                
                # Use default class_id
                default_class_id = 1
                
                for school_day in school_days:
                    status = get_attendance_status(att_profile)
                    
                    # Insert attendance record
                    db.execute(text("""
                        INSERT INTO attendance (student_id, class_id, date, status, created_at)
                        VALUES (:student_id, :class_id, :date, :status, CURRENT_TIMESTAMP)
                        ON CONFLICT DO NOTHING
                    """), {
                        "student_id": student_id,
                        "class_id": default_class_id,
                        "date": school_day,
                        "status": status
                    })
            
            # Create mid-term exam records
            print(f"  📝 Creating mid-term exam results...")
            for family in parent_families:
                student_id = family[3]
                student_name = f"{family[4]} {family[5]}"
                perf_profile = student_profiles[student_id]
                
                # Get a default class_id (we'll use 1 as default)
                default_class_id = 1
                
                for subject_id, subject_name in subject_list:
                    midterm_score = generate_realistic_grade(perf_profile, "midterm")
                    ca_score = generate_realistic_grade(perf_profile, "ca")
                    overall_score = round((ca_score * 0.4) + (midterm_score * 0.6), 1)
                    
                    # Insert mid-term record
                    db.execute(text("""
                        INSERT INTO academic_records (
                            student_id, class_id, subject_id, academic_year, term, 
                            ca_score, exam_score, overall_score, score, grade,
                            remarks, is_finalized, created_at, updated_at
                        ) VALUES (
                            :student_id, :class_id, :subject_id, :academic_year, :term,
                            :ca_score, :exam_score, :overall_score, :overall_score, :grade,
                            :remarks, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                    """), {
                        "student_id": student_id,
                        "class_id": default_class_id,
                        "subject_id": subject_id,
                        "academic_year": academic_year,
                        "term": f"{term_name} - Midterm",
                        "ca_score": ca_score,
                        "exam_score": midterm_score,
                        "overall_score": overall_score,
                        "grade": get_grade_from_score(overall_score),
                        "remarks": "Midterm assessment completed" if midterm_score >= 60 else "Needs improvement in midterm"
                    })
            
            # Create final exam records
            print(f"  🎯 Creating final exam results...")
            for family in parent_families:
                student_id = family[3]
                student_name = f"{family[4]} {family[5]}"
                perf_profile = student_profiles[student_id]
                
                # Get a default class_id
                default_class_id = 1
                
                total_points = 0
                subject_count = 0
                
                for subject_id, subject_name in subject_list:
                    final_score = generate_realistic_grade(perf_profile, "final")
                    ca_score = generate_realistic_grade(perf_profile, "ca")
                    overall_score = round((ca_score * 0.4) + (final_score * 0.6), 1)
                    grade = get_grade_from_score(overall_score)
                    
                    # Convert grade to points for GPA calculation
                    grade_points = {"A+": 4.0, "A": 3.7, "B+": 3.3, "B": 3.0, "C+": 2.7, "C": 2.3, "D+": 2.0, "D": 1.7, "E": 1.0, "F": 0.0}
                    points = grade_points.get(grade, 0.0)
                    
                    total_points += points
                    subject_count += 1
                    
                    # Insert final exam record
                    db.execute(text("""
                        INSERT INTO academic_records (
                            student_id, class_id, subject_id, academic_year, term, 
                            ca_score, exam_score, overall_score, score, grade, grade_points,
                            remarks, is_finalized, created_at, updated_at
                        ) VALUES (
                            :student_id, :class_id, :subject_id, :academic_year, :term,
                            :ca_score, :exam_score, :overall_score, :overall_score, :grade, :grade_points,
                            :remarks, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                    """), {
                        "student_id": student_id,
                        "class_id": default_class_id,
                        "subject_id": subject_id,
                        "academic_year": academic_year,
                        "term": f"{term_name} - Final",
                        "ca_score": ca_score,
                        "exam_score": final_score,
                        "overall_score": overall_score,
                        "grade": grade,
                        "grade_points": points,
                        "remarks": f"Final exam: {grade} grade achieved" if overall_score >= 60 else "Requires additional support"
                    })
                
                # Calculate term GPA
                term_gpa = round(total_points / subject_count, 2) if subject_count > 0 else 0.0
                
                # Create term summary communication
                db.execute(text("""
                    INSERT INTO communications (
                        student_id, title, content, type, priority, created_at
                    ) VALUES (
                        :student_id, :title, :content, 'academic', 'high', :created_at
                    )
                """), {
                    "student_id": student_id,
                    "title": f"{term_name} Academic Report - {student_name}",
                    "content": f"Dear Parent,\n\n{student_name} has completed {term_name} with a GPA of {term_gpa}. "
                              f"Performance level: {perf_profile.title()}.\n\n"
                              f"Attendance: {attendance_profiles[student_id].title()}\n\n"
                              f"Please review the detailed results in the academic section.\n\n"
                              f"Best regards,\nNdirande High School Academic Office",
                    "created_at": term_end
                })
        
        # Create additional communications
        print(f"\n📢 Creating additional communications...")
        communication_templates = [
            {
                "title": "Parent-Teacher Conference Invitation",
                "content": "Dear Parent,\n\nYou are invited to attend a parent-teacher conference to discuss {student_name}'s academic progress and development. Please contact the school office to schedule an appointment.\n\nBest regards,\nAcademic Office",
                "type": "meeting",
                "priority": "medium"
            },
            {
                "title": "Mid-Year Progress Update",
                "content": "Dear Parent,\n\n{student_name} is showing {progress} in their studies this year. We encourage continued support at home to maintain this momentum.\n\nBest regards,\nClass Teacher",
                "type": "progress",
                "priority": "medium"
            },
            {
                "title": "Attendance Notice",
                "content": "Dear Parent,\n\nWe've noticed {student_name}'s attendance pattern and wanted to keep you informed. Regular attendance is crucial for academic success.\n\nPlease contact us if there are any concerns.\n\nBest regards,\nSchool Administration",
                "type": "attendance",
                "priority": "high"
            }
        ]
        
        for family in parent_families:
            student_id = family[3]
            student_name = f"{family[4]} {family[5]}"
            perf_profile = student_profiles[student_id]
            att_profile = attendance_profiles[student_id]
            
            # Send 2-3 additional communications per student
            selected_comms = random.sample(communication_templates, random.randint(2, 3))
            
            for i, comm_template in enumerate(selected_comms):
                progress_words = {"excellent": "excellent progress", "good": "good progress", "average": "steady progress", "struggling": "some challenges but is working hard"}
                
                content = comm_template["content"].format(
                    student_name=student_name,
                    progress=progress_words.get(perf_profile, "progress")
                )
                
                # Create communication with varied dates
                comm_date = datetime.now() - timedelta(days=random.randint(5, 45))
                
                db.execute(text("""
                    INSERT INTO communications (
                        student_id, title, content, type, priority, created_at
                    ) VALUES (
                        :student_id, :title, :content, :type, :priority, :created_at
                    )
                """), {
                    "student_id": student_id,
                    "title": comm_template["title"],
                    "content": content,
                    "type": comm_template["type"],
                    "priority": comm_template["priority"],
                    "created_at": comm_date
                })
        
        # Commit all changes
        db.commit()
        print(f"\n✅ Successfully created comprehensive academic data!")
        
        # Generate summary report
        print(f"\n📊 DATA SUMMARY:")
        
        # Count records
        academic_count = db.execute(text("SELECT COUNT(*) FROM academic_records")).scalar()
        attendance_count = db.execute(text("SELECT COUNT(*) FROM attendance")).scalar()
        comm_count = db.execute(text("SELECT COUNT(*) FROM communications")).scalar()
        
        print(f"  • {len(set([f[3] for f in parent_families]))} students with complete academic profiles")
        print(f"  • {academic_count} academic records (midterm + final exams)")
        print(f"  • {attendance_count} attendance records")
        print(f"  • {comm_count} communications")
        
        # Show student performance distribution
        print(f"\n👥 STUDENT PERFORMANCE PROFILES:")
        for profile in ["excellent", "good", "average", "struggling"]:
            count = sum(1 for p in student_profiles.values() if p == profile)
            print(f"  • {profile.title()}: {count} students")
        
        print(f"\n🎯 PARENT LOGIN CREDENTIALS:")
        unique_parents = {}
        for family in parent_families:
            parent_id = family[0]
            if parent_id not in unique_parents:
                unique_parents[parent_id] = {
                    'name': family[1],
                    'email': family[2],
                    'children': []
                }
            unique_parents[parent_id]['children'].append(f"{family[4]} {family[5]}")
        
        passwords = ["Parent2123", "Parent1123", "Parent3123", "Parent4123", "Parent5123"]
        for i, (parent_id, parent_info) in enumerate(unique_parents.items()):
            password = passwords[i] if i < len(passwords) else f"Parent{i+1}123"
            children_list = ", ".join(parent_info['children'])
            print(f"  • {parent_info['email']} / {password}")
            print(f"    Children: {children_list}")
        
        print(f"\n🌟 All data ready for realistic parent portal testing!")
        
    except Exception as e:
        print(f"❌ Error creating academic data: {e}")
        db.rollback()
        raise
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
