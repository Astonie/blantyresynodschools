import sys
sys.path.append('/app')
from sqlalchemy import text
from app.db.session import SessionLocal
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
hashed_password = pwd_context.hash('teacher123')

db = SessionLocal()

try:
    db.execute(text('SET search_path TO "ndirande_high", public'))
    
    result = db.execute(text("""
        INSERT INTO users (email, full_name, hashed_password, is_active, created_at, updated_at)
        VALUES (:email, :full_name, :hashed_password, true, NOW(), NOW())
        RETURNING id
    """), {
        'email': 'john.banda@teacher.ndirande-high.edu',
        'full_name': 'John Banda (Teacher)',
        'hashed_password': hashed_password
    })
    
    user_id = result.scalar()
    print(f'Created user with ID: {user_id}')
    
    teacher_role_id = db.execute(text('SELECT id FROM roles WHERE name = \'Teacher\'')).scalar()
    print(f'Teacher role ID: {teacher_role_id}')
    
    if teacher_role_id and user_id:
        db.execute(text("""
            INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)
            ON CONFLICT DO NOTHING
        """), {'user_id': user_id, 'role_id': teacher_role_id})
        
        # Link teacher to a class
        db.execute(text("""
            INSERT INTO teachers (user_id, employee_id, subject, hire_date, created_at, updated_at)
            VALUES (:user_id, 'EMP001', 'Mathematics', NOW(), NOW(), NOW())
            ON CONFLICT DO NOTHING
        """), {'user_id': user_id})
        
        db.commit()
        print('SUCCESS: Teacher user created and teacher record added!')
    else:
        print('ERROR: Failed to get required IDs')
        
except Exception as e:
    print(f'ERROR: {e}')
    db.rollback()
finally:
    db.close()
