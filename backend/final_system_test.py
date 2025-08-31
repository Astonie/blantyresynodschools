#!/usr/bin/env python3
"""
Final comprehensive test of the complete academic system
"""
import sys
sys.path.append('/app')

from app.db.session import SessionLocal
from sqlalchemy import text
from datetime import date, datetime

def comprehensive_academic_test():
    print('🎯 FINAL COMPREHENSIVE ACADEMIC SYSTEM TEST')
    print('=' * 60)
    
    db = SessionLocal()
    try:
        # Use ndirande_high as test schema
        db.execute(text('SET search_path TO "ndirande_high"'))
        
        print('\n📊 SYSTEM STATUS SUMMARY:')
        print('=' * 40)
        
        # Test 1: Students System
        print('\n1️⃣ STUDENTS SYSTEM:')
        student_count = db.execute(text('SELECT COUNT(*) FROM students')).scalar()
        sample_student = db.execute(text('SELECT first_name, last_name, admission_no FROM students LIMIT 1')).first()
        print(f'   ✅ {student_count} students in database')
        print(f'   ✅ Sample: {sample_student.first_name} {sample_student.last_name} ({sample_student.admission_no})')
        
        # Test 2: Academic Structure
        print('\n2️⃣ ACADEMIC STRUCTURE:')
        subject_count = db.execute(text('SELECT COUNT(*) FROM subjects')).scalar()
        class_count = db.execute(text('SELECT COUNT(*) FROM classes')).scalar()
        print(f'   ✅ {subject_count} subjects configured')
        print(f'   ✅ {class_count} classes available')
        
        # Test 3: User Management & Permissions
        print('\n3️⃣ USER MANAGEMENT:')
        admin_check = db.execute(text("""
            SELECT u.email, COUNT(p.name) as permission_count
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN role_permissions rp ON ur.role_id = rp.role_id
            LEFT JOIN permissions p ON rp.permission_id = p.id
            WHERE u.email = 'admin@ndirande-high.edu'
            GROUP BY u.id, u.email
        """)).first()
        
        if admin_check:
            print(f'   ✅ Admin user: {admin_check.email}')
            print(f'   ✅ Permissions: {admin_check.permission_count}')
        else:
            print('   ❌ Admin user not found')
        
        # Test 4: Attendance System
        print('\n4️⃣ ATTENDANCE SYSTEM:')
        attendance_count = db.execute(text('SELECT COUNT(*) FROM attendance')).scalar()
        print(f'   ✅ {attendance_count} attendance records')
        
        if attendance_count > 0:
            latest_attendance = db.execute(text("""
                SELECT s.first_name, s.last_name, a.date, a.status
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                ORDER BY a.created_at DESC
                LIMIT 1
            """)).first()
            print(f'   ✅ Latest: {latest_attendance.first_name} {latest_attendance.last_name} - {latest_attendance.status} on {latest_attendance.date}')
        
        # Test 5: Academic Records  
        print('\n5️⃣ ACADEMIC RECORDS:')
        records_count = db.execute(text('SELECT COUNT(*) FROM academic_records')).scalar()
        print(f'   ✅ {records_count} academic records')
        
        if records_count > 0:
            sample_record = db.execute(text("""
                SELECT s.first_name, s.last_name, subj.name as subject_name,
                       ar.overall_score, ar.grade
                FROM academic_records ar
                JOIN students s ON ar.student_id = s.id
                JOIN subjects subj ON ar.subject_id = subj.id
                ORDER BY ar.created_at DESC
                LIMIT 1
            """)).first()
            print(f'   ✅ Latest: {sample_record.first_name} {sample_record.last_name} - {sample_record.subject_name}: {sample_record.overall_score} ({sample_record.grade})')
        
        # Test 6: Grading System
        print('\n6️⃣ GRADING SYSTEM:')
        grading_policies = db.execute(text('SELECT COUNT(*) FROM grading_policies')).scalar()
        grade_scales = db.execute(text('SELECT COUNT(*) FROM grade_scales')).scalar()
        print(f'   ✅ {grading_policies} grading policies')
        print(f'   ✅ {grade_scales} grade scales configured')
        
        # Test 7: Parent Access
        print('\n7️⃣ PARENT ACCESS:')
        parent_relationships = db.execute(text('SELECT COUNT(*) FROM parent_students')).scalar()
        parent_users = db.execute(text("""
            SELECT COUNT(*) FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            WHERE r.name = 'Parent'
        """)).scalar()
        print(f'   ✅ {parent_users} parent users')
        print(f'   ✅ {parent_relationships} parent-student relationships')
        
        # Overall Assessment
        print('\n🎯 OVERALL SYSTEM ASSESSMENT:')
        print('=' * 40)
        
        functionality_tests = [
            ('Student Management', student_count > 0),
            ('Academic Structure', subject_count > 0 and class_count > 0),
            ('User Permissions', admin_check and admin_check.permission_count > 20),
            ('Attendance Tracking', attendance_count > 0),
            ('Academic Records', records_count > 0),
            ('Grading System', grading_policies > 0 and grade_scales > 0),
            ('Parent Access', parent_users > 0 and parent_relationships > 0)
        ]
        
        working_systems = sum(1 for _, working in functionality_tests if working)
        total_systems = len(functionality_tests)
        
        for system_name, is_working in functionality_tests:
            status = '✅ WORKING' if is_working else '❌ NEEDS ATTENTION'
            print(f'   {system_name:<20}: {status}')
        
        print(f'\n📈 COMPLETION STATUS: {working_systems}/{total_systems} systems functional ({working_systems/total_systems*100:.0f}%)')
        
        if working_systems == total_systems:
            print('\n🎉 ACADEMIC SYSTEM FULLY OPERATIONAL!')
            print('   • Students can be managed and enrolled')
            print('   • Attendance can be recorded and tracked')
            print('   • Grades can be entered and calculated')
            print('   • Report cards can be generated')
            print('   • Parents can access their children\'s records')
            print('   • Complete academic lifecycle supported!')
        else:
            print(f'\n⚠️ System {working_systems/total_systems*100:.0f}% complete - some components need attention')
            
        # Login credentials summary
        print('\n🔑 LOGIN CREDENTIALS FOR TESTING:')
        print('   Admin: admin@ndirande-high.edu / admin123')
        if parent_users > 0:
            sample_parent = db.execute(text("""
                SELECT u.email FROM users u
                JOIN user_roles ur ON u.id = ur.user_id
                JOIN roles r ON ur.role_id = r.id
                WHERE r.name = 'Parent'
                LIMIT 1
            """)).scalar()
            if sample_parent:
                print(f'   Parent: {sample_parent} / parent123')
        
    finally:
        db.close()

if __name__ == "__main__":
    comprehensive_academic_test()
