from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    db.execute(text('SET search_path TO ndirande_high, public'))
    # Check parent accounts
    parents = db.execute(text("SELECT u.id, u.email, u.full_name FROM users u JOIN user_roles ur ON u.id = ur.user_id JOIN roles r ON ur.role_id = r.id WHERE r.name = 'Parent' LIMIT 5;")).fetchall()
    print('Available parent accounts:')
    for p in parents:
        print(f'  - {p[1]} ({p[2]})')
finally:
    db.close()
