#!/usr/bin/env python3
"""
Check the actual structure of the students table vs the StudentRead schema expectations
"""
from app.db.session import SessionLocal
from sqlalchemy import text

def check_student_table_structure():
    db = SessionLocal()
    try:
        # Use ndirande_high as test schema
        db.execute(text('SET search_path TO "ndirande_high"'))
        
        print('🔍 STUDENTS TABLE STRUCTURE ANALYSIS')
        print('=' * 60)
        
        # Get actual columns
        columns_result = db.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'students' 
            ORDER BY ordinal_position
        """))
        
        actual_columns = {}
        print('\n📋 ACTUAL DATABASE COLUMNS:')
        for row in columns_result:
            col_name, data_type, nullable, default = row
            actual_columns[col_name] = {
                'type': data_type, 
                'nullable': nullable, 
                'default': default
            }
            print(f'   {col_name}: {data_type} {"NULL" if nullable == "YES" else "NOT NULL"}')
        
        # Expected columns based on StudentRead schema
        expected_columns = {
            'id': 'integer',
            'first_name': 'text',
            'last_name': 'text', 
            'gender': 'text',
            'date_of_birth': 'date',
            'admission_no': 'text',
            'current_class': 'text',
            'parent_phone': 'text',
            'parent_email': 'text',
            'address': 'text',
            'emergency_contact': 'text',
            'emergency_phone': 'text',
            'enrollment_date': 'date',
            'status': 'text',
            'created_at': 'timestamp',
            'updated_at': 'timestamp'
        }
        
        print('\n📝 SCHEMA EXPECTATIONS:')
        for col, expected_type in expected_columns.items():
            print(f'   {col}: {expected_type}')
        
        print('\n🔍 COMPATIBILITY ANALYSIS:')
        missing_cols = set(expected_columns.keys()) - set(actual_columns.keys())
        extra_cols = set(actual_columns.keys()) - set(expected_columns.keys())
        
        if missing_cols:
            print(f'   ❌ Missing columns: {sorted(list(missing_cols))}')
        if extra_cols:
            print(f'   ➕ Extra columns: {sorted(list(extra_cols))}')
        
        if not missing_cols and not extra_cols:
            print('   ✅ Perfect match!')
        
        # Test a sample query to see if it works
        print('\n🧪 SAMPLE QUERY TEST:')
        try:
            sample = db.execute(text('SELECT * FROM students LIMIT 1')).mappings().first()
            if sample:
                print(f'   ✅ Sample record retrieved: {dict(sample).keys()}')
            else:
                print('   ⚠️ No records found')
        except Exception as e:
            print(f'   ❌ Query failed: {e}')
            
    finally:
        db.close()

if __name__ == "__main__":
    check_student_table_structure()
