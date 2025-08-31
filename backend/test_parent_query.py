from app.db.session import SessionLocal
import sqlalchemy as sa

session = SessionLocal()
try:
    session.execute(sa.text("SET search_path TO ndirande_high, public"))
    
    print("🔍 Testing the exact query from the parents endpoint...")
    
    # Use James Phiri's ID (17) from our earlier check
    parent_id = 17
    
    result = session.execute(sa.text("""
        SELECT s.id, s.first_name, s.last_name, s.admission_no, s.class_name
        FROM parent_students ps
        JOIN students s ON ps.student_id = s.id
        WHERE ps.parent_user_id = :parent_id
        ORDER BY s.first_name, s.last_name
    """), {"parent_id": parent_id})
    
    children = result.fetchall()
    print(f"Direct query result for parent_id {parent_id}:")
    if children:
        for child in children:
            print(f"  ID: {child[0]}, Name: {child[1]} {child[2]}, Admission: {child[3]}, Class: {child[4]}")
    else:
        print("  No children found!")
    
    # Also test the full API query with LEFT JOIN
    print(f"\nTesting with LEFT JOIN to classes table:")
    result = session.execute(sa.text("""
        SELECT s.id, s.first_name, s.last_name, s.admission_no, c.name as class_name
        FROM parent_students ps
        JOIN students s ON ps.student_id = s.id
        LEFT JOIN classes c ON s.class_name = c.name
        WHERE ps.parent_user_id = :parent_id
        ORDER BY s.first_name, s.last_name
    """), {"parent_id": parent_id})
    
    children_with_class = result.fetchall()
    if children_with_class:
        for child in children_with_class:
            print(f"  ID: {child[0]}, Name: {child[1]} {child[2]}, Admission: {child[3]}, Class: {child[4]}")
    else:
        print("  No children found with LEFT JOIN!")
    
    # Check if classes table exists and what data it has
    print(f"\nChecking classes table:")
    try:
        result = session.execute(sa.text("SELECT id, name, description FROM classes LIMIT 5"))
        classes = result.fetchall()
        print("Classes found:")
        for cls in classes:
            print(f"  ID: {cls[0]}, Name: {cls[1]}, Description: {cls[2]}")
    except Exception as e:
        print(f"Error accessing classes table: {e}")
        
finally:
    session.close()
