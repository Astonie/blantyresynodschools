from app.db.session import SessionLocal
import sqlalchemy as sa

session = SessionLocal()
try:
    session.execute(sa.text('SET search_path TO ndirande_high, public'))
    
    # Check James Phiri's roles specifically
    user_id = 17
    result = session.execute(sa.text('''
        SELECT r.id, r.name FROM roles r
        JOIN user_roles ur ON ur.role_id = r.id
        WHERE ur.user_id = :uid
    '''), {'uid': user_id})
    roles = result.fetchall()
    print(f'James Phiri (ID {user_id}) roles:')
    for role in roles:
        print(f'  Role ID: {role[0]}, Role Name: "{role[1]}"')
        
    # Check all available roles
    result = session.execute(sa.text('SELECT id, name FROM roles ORDER BY id'))
    all_roles = result.fetchall()
    print(f'\nAll available roles:')
    for role in all_roles:
        print(f'  Role ID: {role[0]}, Role Name: "{role[1]}"')
        
    # Test the exact query from require_roles
    result = session.execute(sa.text("""
        SELECT r.name FROM roles r
        JOIN user_roles ur ON ur.role_id = r.id
        WHERE ur.user_id = :uid
    """), {"uid": user_id})
    role_names = result.scalars().all()
    print(f'\nRole names for require_roles check: {role_names}')
    print(f'Does "Parent" in role names? {"Parent" in role_names}')
        
finally:
    session.close()
