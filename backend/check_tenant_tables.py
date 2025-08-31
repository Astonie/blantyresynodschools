#!/usr/bin/env python3
"""
Check which tables exist vs what should exist in all tenant schemas
"""
from app.db.session import SessionLocal
from sqlalchemy import text

def check_tenant_tables():
    # Check which tables exist vs what should exist in all tenant schemas
    db = SessionLocal()
    try:
        # Get all tenants
        tenants_result = db.execute(text('SELECT slug FROM public.tenants'))
        tenants = [row[0] for row in tenants_result.fetchall()]
        
        expected_tables = [
            'users', 'roles', 'permissions', 'role_permissions', 'user_roles',
            'students', 'classes', 'subjects', 'class_subjects', 'teachers', 
            'teacher_assignments', 'attendance', 'academic_records', 
            'grading_policies', 'grade_scales', 'parent_students',
            'invoices', 'payments', 'exam_schedules', 'library_resources'
        ]
        
        print('🔍 TENANT SCHEMA ANALYSIS')
        print('=' * 60)
        
        for tenant_slug in tenants:
            schema_name = tenant_slug.replace('-', '_')
            print(f'\n🏫 {tenant_slug} ({schema_name}):')
            
            db.execute(text(f'SET search_path TO "{schema_name}"'))
            
            # Get actual tables
            actual_result = db.execute(text('SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema() ORDER BY table_name'))
            actual_tables = {row[0] for row in actual_result.fetchall()}
            
            # Check what's missing
            missing_tables = set(expected_tables) - actual_tables
            extra_tables = actual_tables - set(expected_tables)
            
            print(f'   ✅ Has {len(actual_tables)} tables')
            if missing_tables:
                print(f'   ❌ Missing: {sorted(list(missing_tables))}')
            if extra_tables:
                print(f'   ➕ Extra: {sorted(list(extra_tables))}')
            
            # Specifically check academic_records table
            if 'academic_records' not in actual_tables:
                print(f'   🚨 PRIORITY FIX: academic_records table missing!')
                
    finally:
        db.close()

if __name__ == "__main__":
    check_tenant_tables()
