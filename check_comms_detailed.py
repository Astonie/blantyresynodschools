from app.db.session import SessionLocal
import sqlalchemy as sa

session = SessionLocal()
try:
    session.execute(sa.text("SET search_path TO ndirande_high, public"))
    
    # Get column information from information schema
    result = session.execute(sa.text("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'communications' AND table_schema = 'ndirande_high' 
        ORDER BY ordinal_position
    """))
    columns = result.fetchall()
    print('Communications table columns:')
    for col in columns:
        print(f'  {col[0]} ({col[1]}) - Nullable: {col[2]}, Default: {col[3]}')
    
    # Get a sample row
    result = session.execute(sa.text("SELECT * FROM communications LIMIT 1"))
    row = result.fetchone()
    if row:
        print(f'\nSample row: {row}')
        print(f'Row keys: {list(row._asdict().keys())}')
        
finally:
    session.close()
