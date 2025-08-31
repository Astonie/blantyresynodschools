from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    db.execute(text('SET search_path TO ndirande_high, public'))
    
    # Check users table columns
    columns = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND table_schema = 'ndirande_high' ORDER BY ordinal_position;")).fetchall()
    print('Users table columns:')
    for col in columns:
        print(f'  - {col[0]}')
        
finally:
    db.close()
