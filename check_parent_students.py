from app.db.session import SessionLocal
import sqlalchemy as sa

session = SessionLocal()
try:
    session.execute(sa.text("SET search_path TO ndirande_high, public"))
    
    print("🔍 Checking parent-student associations in ndirande_high schema...")
    
    # Check parent users
    result = session.execute(sa.text("""
        SELECT u.id, u.email, u.full_name 
        FROM users u 
        JOIN user_roles ur ON u.id = ur.user_id 
        JOIN roles r ON ur.role_id = r.id 
        WHERE r.name = 'Parent'
        ORDER BY u.id
    """))
    parents = result.fetchall()
    print(f"\n📋 Found {len(parents)} parent users:")
    for parent in parents:
        print(f"  ID: {parent[0]}, Email: {parent[1]}, Name: {parent[2]}")
    
    # Check students
    result = session.execute(sa.text("SELECT id, first_name, last_name, admission_no FROM students ORDER BY id"))
    students = result.fetchall()
    print(f"\n👥 Found {len(students)} students:")
    for student in students:
        print(f"  ID: {student[0]}, Name: {student[1]} {student[2]}, Admission: {student[3]}")
    
    # Check parent-student relationships
    result = session.execute(sa.text("""
        SELECT ps.id, ps.parent_user_id, ps.student_id, 
               u.email as parent_email, u.full_name as parent_name,
               s.first_name, s.last_name, s.admission_no
        FROM parent_students ps
        JOIN users u ON ps.parent_user_id = u.id
        JOIN students s ON ps.student_id = s.id
        ORDER BY ps.parent_user_id, ps.student_id
    """))
    relationships = result.fetchall()
    print(f"\n👨‍👩‍👧‍👦 Found {len(relationships)} parent-student relationships:")
    for rel in relationships:
        print(f"  Parent: {rel[4]} ({rel[3]}) -> Student: {rel[5]} {rel[6]} ({rel[7]})")
    
    # Check academic records count for each student
    print(f"\n📚 Academic records per student:")
    for student in students:
        result = session.execute(sa.text("""
            SELECT COUNT(*) FROM academic_records WHERE student_id = :student_id
        """), {"student_id": student[0]})
        count = result.scalar()
        print(f"  {student[1]} {student[2]}: {count} academic records")
    
    # Test specific parent login data
    print(f"\n🔍 Checking James Phiri specifically:")
    result = session.execute(sa.text("""
        SELECT u.id, u.email, u.full_name, u.is_active
        FROM users u 
        WHERE u.email = 'james.phiri@parent.ndirande.edu'
    """))
    james = result.fetchone()
    if james:
        print(f"  James Phiri found: ID {james[0]}, Active: {james[3]}")
        
        # Check his children
        result = session.execute(sa.text("""
            SELECT s.id, s.first_name, s.last_name, s.admission_no
            FROM parent_students ps
            JOIN students s ON ps.student_id = s.id
            WHERE ps.parent_user_id = :parent_id
        """), {"parent_id": james[0]})
        children = result.fetchall()
        print(f"  James' children: {len(children)}")
        for child in children:
            print(f"    - {child[1]} {child[2]} (ID: {child[0]}, Admission: {child[3]})")
    else:
        print("  James Phiri not found!")
        
finally:
    session.close()
