import sys
sys.path.append('/app')
from sqlalchemy import text
from app.db.session import SessionLocal
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
hashed_password = pwd_context.hash('parent123')

db = SessionLocal()

try:
    db.execute(text('SET search_path TO "ndirande_high", public'))
    
    result = db.execute(text("""
        INSERT INTO users (email, full_name, hashed_password, is_active, created_at, updated_at)
        VALUES (:email, :full_name, :hashed_password, true, NOW(), NOW())
        RETURNING id
    """), {
        'email': 'mary.tembo@parent.ndirande-high.edu',
        'full_name': 'Mary Tembo (Parent)',
        'hashed_password': hashed_password
    })
    
    user_id = result.scalar()
    print(f'Created user with ID: {user_id}')
    
    parent_role_id = db.execute(text('SELECT id FROM roles WHERE name = \'Parent\'')).scalar()
    print(f'Parent role ID: {parent_role_id}')
    
    if parent_role_id and user_id:
        db.execute(text("""
            INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)
            ON CONFLICT DO NOTHING
        """), {'user_id': user_id, 'role_id': parent_role_id})
        
        db.execute(text("""
            INSERT INTO parent_students (parent_user_id, student_id)
            SELECT :user_id, s.id 
            FROM students s 
            WHERE s.first_name = 'Hope' AND s.last_name = 'Tembo'
            LIMIT 1
            ON CONFLICT DO NOTHING
        """), {'user_id': user_id})
        
        db.commit()
        print('SUCCESS: Parent user created and linked to student!')
    else:
        print('ERROR: Failed to get required IDs')
        
except Exception as e:
    print(f'ERROR: {e}')
    db.rollback()
finally:
    db.close()
