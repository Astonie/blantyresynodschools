from app.db.session import SessionLocal
import sqlalchemy as sa

session = SessionLocal()
try:
    session.execute(sa.text("SET search_path TO ndirande_high, public"))
    result = session.execute(sa.text("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'subjects' AND table_schema = 'ndirande_high' ORDER BY ordinal_position"))
    columns = result.fetchall()
    print('Subjects table structure:')
    for col in columns:
        print(f'  {col[0]} ({col[1]}) - Nullable: {col[2]}')
    
    # Also check existing subjects
    result = session.execute(sa.text("SELECT id, name, code FROM subjects LIMIT 5"))
    subjects = result.fetchall()
    print('\nExisting subjects:')
    for subj in subjects:
        print(f'  ID: {subj[0]}, Name: {subj[1]}, Code: {subj[2]}')
        
finally:
    session.close()
