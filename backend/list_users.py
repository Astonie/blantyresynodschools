import sys
sys.path.append('/app')
from sqlalchemy import text
from app.db.session import SessionLocal

db = SessionLocal()
db.execute(text('SET search_path TO "ndirande_high", public'))
result = db.execute(text("SELECT u.email, u.full_name, r.name as role FROM users u JOIN user_roles ur ON u.id = ur.user_id JOIN roles r ON ur.role_id = r.id WHERE r.name IN ('Teacher', 'Parent') ORDER BY u.email"))
users = result.fetchall()
print('Existing Teacher and Parent users:')
for user in users:
    print(f'  {user[0]} - {user[1]} - {user[2]}')
db.close()
