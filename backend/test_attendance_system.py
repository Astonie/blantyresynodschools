#!/usr/bin/env python3
"""
Test attendance API and identify permission issues
"""
import sys
sys.path.append('/app')

from app.db.session import SessionLocal
from app.api.deps import require_permissions, get_current_user_id
from sqlalchemy import text

def test_attendance_system():
    print('🧪 TESTING ATTENDANCE SYSTEM')
    print('=' * 40)
    
    db = SessionLocal()
    try:
        # Use ndirande_high as test schema
        db.execute(text('SET search_path TO "ndirande_high"'))
        
        print('\n1️⃣ Checking attendance table structure...')
        
        # Check if attendance table exists
        attendance_check = db.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = 'attendance' AND table_schema = current_schema()
        """)).scalar()
        
        if attendance_check:
            print('   ✅ Attendance table exists')
            
            # Check columns
            columns = db.execute(text("""
                SELECT column_name, data_type FROM information_schema.columns 
                WHERE table_name = 'attendance' ORDER BY ordinal_position
            """)).fetchall()
            
            print('   📋 Table structure:')
            for col_name, data_type in columns:
                print(f'      {col_name}: {data_type}')
        else:
            print('   ❌ Attendance table does not exist')
            return
        
        print('\n2️⃣ Checking existing attendance data...')
        attendance_count = db.execute(text('SELECT COUNT(*) FROM attendance')).scalar()
        print(f'   📊 Records in attendance table: {attendance_count}')
        
        print('\n3️⃣ Checking permissions for attendance...')
        # Check what permissions exist
        perms = db.execute(text("""
            SELECT name, description FROM permissions 
            WHERE name LIKE '%attendance%' ORDER BY name
        """)).fetchall()
        
        if perms:
            print('   📋 Attendance-related permissions:')
            for perm_name, description in perms:
                print(f'      {perm_name}: {description or "No description"}')
        else:
            print('   ❌ No attendance permissions found!')
            
        print('\n4️⃣ Checking user permissions...')
        # Check what permissions the admin user has
        admin_perms = db.execute(text("""
            SELECT p.name FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            JOIN user_roles ur ON rp.role_id = ur.role_id
            JOIN users u ON ur.user_id = u.id
            WHERE u.email = 'admin@ndirande-high.edu'
            ORDER BY p.name
        """)).scalars().all()
        
        print(f'   📋 Admin user permissions ({len(admin_perms)}):')
        attendance_perms = [p for p in admin_perms if 'attendance' in p.lower()]
        if attendance_perms:
            print('   📋 Attendance permissions:')
            for perm in attendance_perms:
                print(f'      ✅ {perm}')
        else:
            print('   ❌ No attendance permissions for admin user')
            
        print(f'   📋 All permissions: {admin_perms[:10]}...')  # Show first 10
            
    finally:
        db.close()

if __name__ == "__main__":
    test_attendance_system()
