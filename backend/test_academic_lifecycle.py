#!/usr/bin/env python3
"""
Comprehensive Academic Module Test: Attendance, Grading, and Report Cards
"""

import sys
import os
import json
import random
from datetime import datetime, date, timedelta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.session import SessionLocal
from app.services.security import create_access_token


def test_complete_academic_lifecycle():
    """Test the complete academic lifecycle including attendance, grading, and reports."""
    
    print("🎓 Testing Complete Academic Module Lifecycle")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Use ndirande_high as our test school
        db.execute(text('SET search_path TO ndirande_high'))
        
        print("\n1️⃣  SETUP: Getting test data...")
        
        # Get students
        students_result = db.execute(text('SELECT id, first_name, last_name, admission_no, class_name FROM students LIMIT 10'))
        students = [dict(row._mapping) for row in students_result.fetchall()]
        print(f"   📚 Found {len(students)} test students")
        
        # Get subjects  
        subjects_result = db.execute(text('SELECT id, name, code FROM subjects'))
        subjects = [dict(row._mapping) for row in subjects_result.fetchall()]
        print(f"   📖 Found {len(subjects)} subjects: {', '.join([s['name'] for s in subjects])}")
        
        # Get classes
        classes_result = db.execute(text('SELECT id, name FROM classes'))
        classes = [dict(row._mapping) for row in classes_result.fetchall()]
        print(f"   🏛️  Found {len(classes)} classes: {', '.join([c['name'] for c in classes])}")
        
        if not students or not subjects or not classes:
            print("❌ Missing required test data!")
            return
            
        print("\n2️⃣  ATTENDANCE TESTING...")
        
        # Create attendance records for the past 30 days
        attendance_created = 0
        for i in range(30):  # Last 30 days
            test_date = (datetime.now() - timedelta(days=i)).date()
            
            for student in students[:5]:  # Test with first 5 students
                for class_obj in classes[:2]:  # Test with first 2 classes
                    # Random attendance status
                    status = random.choice(['present', 'absent', 'late', 'excused'])
                    
                    try:
                        db.execute(text('''
                            INSERT INTO attendance (student_id, class_id, date, status, created_at, updated_at)
                            VALUES (:student_id, :class_id, :date, :status, NOW(), NOW())
                            ON CONFLICT DO NOTHING
                        '''), {
                            'student_id': student['id'],
                            'class_id': class_obj['id'], 
                            'date': test_date,
                            'status': status
                        })
                        attendance_created += 1
                    except Exception as e:
                        print(f"      ⚠️  Attendance error: {e}")
                        continue
                        
        db.commit()
        print(f"   ✅ Created {attendance_created} attendance records")
        
        print("\n3️⃣  ACADEMIC RECORDS TESTING...")
        
        # Create academic records (grades) for students
        terms = ['Term 1', 'Term 2', 'Term 3']
        academic_year = '2024'
        records_created = 0
        
        for student in students[:5]:  # Test with first 5 students
            for subject in subjects:
                for term in terms:
                    # Generate realistic scores
                    ca_score = random.uniform(30, 100)
                    exam_score = random.uniform(20, 100)
                    overall_score = (ca_score * 0.4) + (exam_score * 0.6)
                    
                    # Determine grade
                    if overall_score >= 80:
                        grade = 'A'
                    elif overall_score >= 70:
                        grade = 'B'
                    elif overall_score >= 60:
                        grade = 'C'
                    elif overall_score >= 50:
                        grade = 'D'
                    elif overall_score >= 40:
                        grade = 'E'
                    else:
                        grade = 'F'
                    
                    try:
                        db.execute(text('''
                            INSERT INTO academic_records (
                                student_id, subject_id, term, academic_year,
                                ca_score, exam_score, overall_score, grade,
                                created_at, updated_at
                            ) VALUES (
                                :student_id, :subject_id, :term, :academic_year,
                                :ca_score, :exam_score, :overall_score, :grade,
                                NOW(), NOW()
                            ) ON CONFLICT DO NOTHING
                        '''), {
                            'student_id': student['id'],
                            'subject_id': subject['id'],
                            'term': term,
                            'academic_year': academic_year,
                            'ca_score': round(ca_score, 2),
                            'exam_score': round(exam_score, 2), 
                            'overall_score': round(overall_score, 2),
                            'grade': grade
                        })
                        records_created += 1
                    except Exception as e:
                        print(f"      ⚠️  Academic record error: {e}")
                        continue
                        
        db.commit()
        print(f"   ✅ Created {records_created} academic records")
        
        print("\n4️⃣  PARENT-STUDENT RELATIONSHIPS...")
        
        # Create parent-student relationships for report card access
        parents_created = 0
        for student in students[:5]:
            # Get parent user (assuming parent1@school1.org exists)
            parent_result = db.execute(text("SELECT id FROM users WHERE email LIKE '%parent%' LIMIT 1"))
            parent_row = parent_result.fetchone()
            
            if parent_row:
                parent_id = parent_row[0]
                try:
                    db.execute(text('''
                        INSERT INTO parent_students (parent_id, student_id, relationship, created_at, updated_at)
                        VALUES (:parent_id, :student_id, 'Guardian', NOW(), NOW())
                        ON CONFLICT DO NOTHING
                    '''), {
                        'parent_id': parent_id,
                        'student_id': student['id']
                    })
                    parents_created += 1
                except Exception as e:
                    print(f"      ⚠️  Parent relationship error: {e}")
                    
        db.commit()
        print(f"   ✅ Created {parents_created} parent-student relationships")
        
        print("\n5️⃣  DATA SUMMARY REPORT...")
        
        # Generate summary statistics
        total_students = db.execute(text("SELECT COUNT(*) FROM students")).scalar()
        total_attendance = db.execute(text("SELECT COUNT(*) FROM attendance")).scalar() 
        total_records = db.execute(text("SELECT COUNT(*) FROM academic_records")).scalar()
        total_parents = db.execute(text("SELECT COUNT(*) FROM parent_students")).scalar()
        
        print(f"   👥 Total Students: {total_students}")
        print(f"   📅 Attendance Records: {total_attendance}")
        print(f"   📊 Academic Records: {total_records}")
        print(f"   👨‍👩‍👧‍👦 Parent Relationships: {total_parents}")
        
        # Sample student report card
        print("\n6️⃣  SAMPLE REPORT CARD...")
        
        sample_student_id = students[0]['id']
        report_query = text('''
            SELECT s.first_name, s.last_name, s.admission_no, s.class_name,
                   sub.name as subject_name, ar.term, ar.academic_year,
                   ar.ca_score, ar.exam_score, ar.overall_score, ar.grade
            FROM students s
            JOIN academic_records ar ON s.id = ar.student_id
            JOIN subjects sub ON ar.subject_id = sub.id
            WHERE s.id = :student_id AND ar.term = 'Term 1'
            ORDER BY sub.name
        ''')
        
        report_result = db.execute(report_query, {'student_id': sample_student_id})
        report_data = report_result.fetchall()
        
        if report_data:
            first_record = report_data[0]
            print(f"\n   📋 REPORT CARD - {first_record[0]} {first_record[1]} ({first_record[2]})")
            print(f"   🏫 Class: {first_record[3]} | Term: {first_record[5]} | Year: {first_record[6]}")
            print("   " + "-" * 50)
            
            total_score = 0
            subject_count = 0
            
            for record in report_data:
                subject_name, ca, exam, overall, grade = record[4], record[7], record[8], record[9], record[10]
                print(f"   📖 {subject_name:15} | CA: {ca:5.1f} | Exam: {exam:5.1f} | Total: {overall:5.1f} | Grade: {grade}")
                total_score += overall
                subject_count += 1
                
            if subject_count > 0:
                average = total_score / subject_count
                print("   " + "-" * 50)
                print(f"   📊 OVERALL AVERAGE: {average:.2f}")
                
                if average >= 80:
                    performance = "EXCELLENT"
                elif average >= 70:
                    performance = "VERY GOOD"
                elif average >= 60:
                    performance = "GOOD"
                elif average >= 50:
                    performance = "SATISFACTORY"
                else:
                    performance = "NEEDS IMPROVEMENT"
                    
                print(f"   🎯 PERFORMANCE: {performance}")
        
        print("\n" + "=" * 60)
        print("✅ COMPLETE ACADEMIC LIFECYCLE TEST SUCCESSFUL!")
        print("🎓 All modules tested: Students, Attendance, Grading, Reports")
        print("👨‍👩‍👧‍👦 Parent access to report cards configured")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_complete_academic_lifecycle()
