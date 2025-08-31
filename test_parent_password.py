from app.db.session import SessionLocal
from sqlalchemy import text
from app.services.security import verify_password

db = SessionLocal()
try:
    db.execute(text('SET search_path TO ndirande_high, public'))
    
    # Get a parent and their password
    parent = db.execute(text("SELECT u.id, u.email, u.full_name, u.hashed_password FROM users u JOIN user_roles ur ON u.id = ur.user_id JOIN roles r ON ur.role_id = r.id WHERE r.name = 'Parent' AND u.email LIKE '%isaac%' LIMIT 1;")).fetchone()
    
    if parent:
        print(f'Testing parent: {parent[1]} ({parent[2]})')
        
        # Test different passwords that might have been used
        test_passwords = ['parentpass123', 'password123', 'defaultpass']
        
        for pwd in test_passwords:
            is_valid = verify_password(pwd, parent[3])
            print(f'  Password "{pwd}": {is_valid}')
            if is_valid:
                print(f'  ✅ Correct password found: {pwd}')
                break
    else:
        print('No parent found with isaac in email')
        
finally:
    db.close()
