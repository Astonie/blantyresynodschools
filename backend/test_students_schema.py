#!/usr/bin/env python3
"""
Test the fixed students API using direct database and schema validation
"""
import sys
sys.path.append('/app')

from app.db.session import SessionLocal
from app.schemas.students import StudentRead
from sqlalchemy import text
from pydantic import ValidationError

def test_students_schema_compatibility():
    print('🧪 TESTING STUDENTS API SCHEMA COMPATIBILITY')
    print('=' * 55)
    
    db = SessionLocal()
    try:
        # Use ndirande_high as test schema
        db.execute(text('SET search_path TO "ndirande_high"'))
        
        print('\n1️⃣ Testing StudentRead schema with actual data...')
        rows = db.execute(text('SELECT * FROM students LIMIT 3')).mappings().all()
        
        if not rows:
            print('   ⚠️ No student data found')
            return
            
        print(f'   Found {len(rows)} test records')
        
        successful_validations = 0
        for i, row in enumerate(rows):
            try:
                student = StudentRead(**dict(row))
                successful_validations += 1
                print(f'   ✅ Record {i+1}: {student.first_name} {student.last_name} - Schema validation passed')
            except ValidationError as e:
                print(f'   ❌ Record {i+1}: Schema validation failed')
                print(f'      Error: {e}')
                print(f'      Available fields: {list(dict(row).keys())}')
        
        print(f'\n🎯 RESULT: {successful_validations}/{len(rows)} records validated successfully')
        
        if successful_validations == len(rows):
            print('   ✅ Students API should now work correctly!')
        else:
            print('   ❌ Schema issues still exist')
            
        # Test the actual API query pattern
        print('\n2️⃣ Testing API query pattern...')
        try:
            # Simulate the API query
            query = "SELECT * FROM students WHERE 1=1 ORDER BY first_name, last_name"
            api_rows = db.execute(text(query)).mappings().all()
            
            api_students = []
            for row in api_rows[:5]:  # Test first 5
                try:
                    student = StudentRead(**dict(row))
                    api_students.append(student)
                except ValidationError as e:
                    print(f'   ❌ API pattern validation failed: {e}')
                    return
            
            print(f'   ✅ API query pattern working! {len(api_students)} students would be returned')
            
        except Exception as e:
            print(f'   ❌ API query pattern failed: {e}')
            
    finally:
        db.close()

if __name__ == "__main__":
    test_students_schema_compatibility()
