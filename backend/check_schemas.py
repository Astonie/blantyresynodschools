from app.db.session import SessionLocal
import sqlalchemy as sa

# Create database session
session = SessionLocal()
try:
    # Query for available schemas
    result = session.execute(sa.text("SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast', 'pg_toast_temp_1', 'pg_statistic', 'pg_temp_1')"))
    schemas = result.fetchall()
    print('Available schemas:')
    for schema in schemas:
        print(f'  {schema[0]}')
    
    # Also check if there's a schools table in public schema
    try:
        result = session.execute(sa.text("SELECT slug, name FROM public.schools"))
        schools = result.fetchall()
        print('\nSchools in public schema:')
        for school in schools:
            print(f'  Slug: {school[0]}, Name: {school[1]}')
    except Exception as e:
        print(f'\nNo schools table or error: {e}')
        
finally:
    session.close()
