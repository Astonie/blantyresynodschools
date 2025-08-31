from sqlalchemy import text, create_engine
from app.core.config import settings
import os
import hashlib

engine = create_engine(settings.database_url)

print('=== CREATING PARENT TEST USER IN TENANT SCHEMA ===')
with engine.connect() as conn:
    # Set schema to ndirande tenant
    conn.execute(text("SET search_path TO ndirande, public"))
    
    # Create basic user tables for tenant if they don't exist
    try:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''))
        
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS roles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT
            )
        '''))
        
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
                PRIMARY KEY (user_id, role_id)
            )
        '''))
        
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                admission_no VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255),
                class_name VARCHAR(100),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''))
        
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS parent_students (
                parent_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
                relationship VARCHAR(50) DEFAULT 'parent',
                PRIMARY KEY (parent_user_id, student_id)
            )
        '''))
        
        print('✅ Created basic tenant tables')
        
        # Create Parent role
        conn.execute(text("INSERT INTO roles (name, description) VALUES ('Parent (Restricted)', 'Restricted parent access') ON CONFLICT (name) DO NOTHING"))
        
        # Get parent role ID
        parent_role_result = conn.execute(text("SELECT id FROM roles WHERE name = 'Parent (Restricted)'"))
        parent_role_id = parent_role_result.scalar()
        print(f'✅ Parent role ID: {parent_role_id}')
        
        # Create sample students
        students_data = [
            ('John', 'Banda', 'ND2025001', 'john.banda@student.ndirande.edu', 'Form 1A'),
            ('Mary', 'Phiri', 'ND2025002', 'mary.phiri@student.ndirande.edu', 'Form 2B'),
            ('Peter', 'Mwale', 'ND2025003', 'peter.mwale@student.ndirande.edu', 'Form 1A')
        ]
        
        for student in students_data:
            conn.execute(text('''
                INSERT INTO students (first_name, last_name, admission_no, email, class_name) 
                VALUES (:first_name, :last_name, :admission_no, :email, :class_name)
                ON CONFLICT (admission_no) DO NOTHING
            '''), {
                'first_name': student[0],
                'last_name': student[1], 
                'admission_no': student[2],
                'email': student[3],
                'class_name': student[4]
            })
        
        print('✅ Created sample students')
        
        # Create parent user
        parent_email = 'parent@ndirande.edu'
        parent_password = 'ParentPass123'
        hashed_password = hashlib.sha256(parent_password.encode()).hexdigest()
        
        conn.execute(text('''
            INSERT INTO users (email, hashed_password, full_name, is_active)
            VALUES (:email, :password, :full_name, true)
            ON CONFLICT (email) DO NOTHING
        '''), {
            'email': parent_email,
            'password': hashed_password,
            'full_name': 'Maria Ndirande (Parent)'
        })
        
        # Get parent user ID
        parent_user_result = conn.execute(text("SELECT id FROM users WHERE email = :email"), {'email': parent_email})
        parent_user_id = parent_user_result.scalar()
        print(f'✅ Parent user ID: {parent_user_id}')
        
        # Assign parent role
        conn.execute(text('''
            INSERT INTO user_roles (user_id, role_id) 
            VALUES (:user_id, :role_id)
            ON CONFLICT (user_id, role_id) DO NOTHING
        '''), {'user_id': parent_user_id, 'role_id': parent_role_id})
        
        print('✅ Assigned parent role')
        
        # Associate parent with students
        student_results = conn.execute(text("SELECT id FROM students ORDER BY id LIMIT 2"))
        student_ids = [row[0] for row in student_results.fetchall()]
        
        for student_id in student_ids:
            conn.execute(text('''
                INSERT INTO parent_students (parent_user_id, student_id, relationship)
                VALUES (:parent_id, :student_id, 'parent')
                ON CONFLICT (parent_user_id, student_id) DO NOTHING
            '''), {'parent_id': parent_user_id, 'student_id': student_id})
        
        print(f'✅ Associated parent with {len(student_ids)} students')
        
        conn.commit()
        
        print('\\n' + '='*60)
        print('🎯 PARENT TEST ACCOUNT CREATED!')
        print('='*60)
        print(f'📧 Email: {parent_email}')
        print(f'🔑 Password: {parent_password}')
        print(f'🏢 Tenant: ndirande')
        print(f'👶 Children: {len(student_ids)}')
        print('🌐 URL: http://localhost:5174')
        print('='*60)
        print('📝 TESTING INSTRUCTIONS:')
        print('1. Go to http://localhost:5174')
        print('2. Login with parent credentials above')
        print('3. Should auto-redirect to /app/parent')
        print('4. Test the parent-only features!')
        print('='*60)
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
