from app.db.session import SessionLocal
import sqlalchemy as sa

# Create database session
session = SessionLocal()
try:
    result = session.execute(sa.text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
    tables = result.fetchall()
    print('Tables in public schema:')
    for table in tables:
        print(f'  {table[0]}')
        
    # Let's also check if there's a different schools table structure
    try:
        result = session.execute(sa.text("SELECT column_name FROM information_schema.columns WHERE table_name = 'schools' AND table_schema = 'public'"))
        columns = result.fetchall()
        if columns:
            print('\nColumns in public.schools:')
            for column in columns:
                print(f'  {column[0]}')
    except Exception as e:
        print(f'\nNo schools table or error: {e}')
        
finally:
    session.close()
