from app.db.session import SessionLocal
import sqlalchemy as sa

session = SessionLocal()
try:
    session.execute(sa.text("SET search_path TO ndirande_high, public"))
    result = session.execute(sa.text("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'attendance' AND table_schema = 'ndirande_high' 
        ORDER BY ordinal_position
    """))
    columns = result.fetchall()
    print('Attendance table structure:')
    for col in columns:
        print(f'  {col[0]} ({col[1]}) - Nullable: {col[2]}')
        
finally:
    session.close()
