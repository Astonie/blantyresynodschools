from sqlalchemy import text, create_engine
from app.core.config import settings
import os
import hashlib
import random
from datetime import datetime, date

engine = create_engine(settings.database_url)

# Sample data for realistic names and academic results
PARENT_NAMES = [
    ("Grace", "Banda", "grace.banda@parent.ndirande.edu"),
    ("James", "Phiri", "james.phiri@parent.ndirande.edu"), 
    ("Mary", "Mwale", "mary.mwale@parent.ndirande.edu"),
    ("Peter", "Chisale", "peter.chisale@parent.ndirande.edu"),
    ("Susan", "Nyirenda", "susan.nyirenda@parent.ndirande.edu"),
    ("David", "Tembo", "david.tembo@parent.ndirande.edu"),
    ("Alice", "Kachingwe", "alice.kachingwe@parent.ndirande.edu"),
    ("John", "Chirwa", "john.chirwa@parent.ndirande.edu"),
    ("Rose", "Nkomo", "rose.nkomo@parent.ndirande.edu"),
    ("Francis", "Mvula", "francis.mvula@parent.ndirande.edu"),
    ("Elizabeth", "Gondwe", "elizabeth.gondwe@parent.ndirande.edu"),
    ("Michael", "Lungu", "michael.lungu@parent.ndirande.edu"),
    ("Agnes", "Msiska", "agnes.msiska@parent.ndirande.edu"),
    ("Charles", "Zimba", "charles.zimba@parent.ndirande.edu"),
    ("Lucy", "Maseko", "lucy.maseko@parent.ndirande.edu")
]

STUDENT_FIRST_NAMES = [
    "Abel", "Blessings", "Caroline", "Daniel", "Emmanuel", "Faith", "George", "Hope",
    "Isaac", "Joyce", "Kenneth", "Linda", "Moses", "Nancy", "Oscar", "Precious",
    "Queen", "Robert", "Sarah", "Thoko", "Violet", "William", "Xavier", "Yolanda", "Zion"
]

CLASSES = ["Form 1A", "Form 1B", "Form 2A", "Form 2B", "Form 3A", "Form 3B", "Form 4A", "Form 4B"]

SUBJECTS = [
    ("Mathematics", 4.0),
    ("English", 3.5),
    ("Chichewa", 3.0),
    ("Biology", 4.0),
    ("Chemistry", 4.5),
    ("Physics", 4.5),
    ("History", 3.0),
    ("Geography", 3.5),
    ("Life Skills", 2.5),
    ("Religious Studies", 2.5),
    ("Agriculture", 3.0),
    ("Business Studies", 3.5)
]

TERMS = ["Term 1", "Term 2", "Term 3"]
ACADEMIC_YEARS = ["2024", "2025"]

def generate_realistic_grades():
    """Generate realistic academic grades for a student"""
    # Base performance level (some students perform better than others)
    performance_level = random.choice([
        0.6,  # Struggling student
        0.7,  # Below average 
        0.8,  # Average
        0.85, # Above average
        0.9,  # Good student
        0.95  # Excellent student
    ])
    
    grades = []
    for subject_name, max_points in SUBJECTS:
        # Add some subject-specific variation
        subject_modifier = random.uniform(0.85, 1.15)
        actual_performance = min(0.98, performance_level * subject_modifier)
        
        # Generate CA and Exam scores
        total_possible = 100
        ca_score = random.uniform(25, 40) * actual_performance
        exam_score = random.uniform(35, 60) * actual_performance
        overall_score = ca_score + exam_score
        
        # Determine grade and points based on overall score
        if overall_score >= 80:
            grade = "A"
            grade_points = 4.0
        elif overall_score >= 70:
            grade = "B"
            grade_points = 3.0
        elif overall_score >= 60:
            grade = "C"
            grade_points = 2.0
        elif overall_score >= 50:
            grade = "D"
            grade_points = 1.0
        else:
            grade = "F"
            grade_points = 0.0
            
        grades.append({
            'subject_name': subject_name,
            'ca_score': round(ca_score, 1),
            'exam_score': round(exam_score, 1),
            'overall_score': round(overall_score, 1),
            'grade': grade,
            'grade_points': grade_points,
            'is_finalized': True
        })
    
    return grades

print('🏫 SEEDING PARENTS WITH CHILDREN AND ACADEMIC RESULTS')
print('='*70)

with engine.connect() as conn:
    # Set schema to ndirande tenant
    conn.execute(text("SET search_path TO ndirande, public"))
    
    try:
        # Ensure we have the necessary tables
        print('📋 Setting up database tables...')
        
        # Create academic records table
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS academic_records (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
                subject_name VARCHAR(100) NOT NULL,
                ca_score DECIMAL(5,2) DEFAULT 0,
                exam_score DECIMAL(5,2) DEFAULT 0,
                overall_score DECIMAL(5,2) DEFAULT 0,
                grade VARCHAR(5),
                grade_points DECIMAL(3,2) DEFAULT 0,
                term VARCHAR(20) NOT NULL,
                academic_year VARCHAR(10) NOT NULL,
                is_finalized BOOLEAN DEFAULT FALSE,
                teacher_comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, subject_name, term, academic_year)
            )
        '''))
        
        # Create subjects table
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS subjects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                code VARCHAR(20),
                description TEXT,
                credit_hours INTEGER DEFAULT 3,
                is_active BOOLEAN DEFAULT TRUE
            )
        '''))
        
        # Create communications table
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS communications (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                type VARCHAR(50) DEFAULT 'general',
                priority VARCHAR(20) DEFAULT 'medium',
                target_audience VARCHAR(50) DEFAULT 'all',
                student_id INTEGER REFERENCES students(id) ON DELETE CASCADE NULL,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        '''))
        
        print('✅ Database tables ready')
        
        # Insert subjects
        print('📚 Creating subjects...')
        for subject_name, _ in SUBJECTS:
            conn.execute(text('''
                INSERT INTO subjects (name, code, is_active) 
                VALUES (:name, :code, true)
                ON CONFLICT (name) DO NOTHING
            '''), {
                'name': subject_name,
                'code': subject_name[:4].upper()
            })
        
        # Clear existing data for fresh seeding
        print('🧹 Clearing existing test data...')
        conn.execute(text("DELETE FROM academic_records"))
        conn.execute(text("DELETE FROM parent_students"))
        conn.execute(text("DELETE FROM communications"))
        conn.execute(text("DELETE FROM students"))
        conn.execute(text("DELETE FROM user_roles WHERE user_id != 1"))  # Keep first parent
        conn.execute(text("DELETE FROM users WHERE id != 1"))  # Keep first parent
        conn.commit()
        
        # Get parent role ID
        parent_role_result = conn.execute(text("SELECT id FROM roles WHERE name = 'Parent (Restricted)'"))
        parent_role_id = parent_role_result.scalar()
        
        if not parent_role_id:
            conn.execute(text("INSERT INTO roles (name, description) VALUES ('Parent (Restricted)', 'Restricted parent access')"))
            parent_role_result = conn.execute(text("SELECT id FROM roles WHERE name = 'Parent (Restricted)'"))
            parent_role_id = parent_role_result.scalar()
            conn.commit()
        
        print(f'✅ Parent role ID: {parent_role_id}')
        
        # Create parents with children and academic records
        print('👨‍👩‍👧‍👦 Creating parents and children with academic data...')
        
        admission_counter = 1000
        parent_count = 0
        student_count = 0
        
        for first_name, last_name, email in PARENT_NAMES:
            parent_count += 1
            
            # Create parent user
            parent_password = f"Parent{parent_count}123"
            hashed_password = hashlib.sha256(parent_password.encode()).hexdigest()
            
            parent_result = conn.execute(text('''
                INSERT INTO users (email, hashed_password, full_name, is_active)
                VALUES (:email, :password, :full_name, true)
                RETURNING id
            '''), {
                'email': email,
                'password': hashed_password,
                'full_name': f"{first_name} {last_name}"
            })
            parent_id = parent_result.scalar()
            
            # Assign parent role
            conn.execute(text('''
                INSERT INTO user_roles (user_id, role_id) 
                VALUES (:user_id, :role_id)
            '''), {'user_id': parent_id, 'role_id': parent_role_id})
            
            # Create 1-2 children for each parent
            num_children = random.choice([1, 2])
            children_names = []
            
            for child_num in range(num_children):
                student_count += 1
                admission_counter += 1
                
                # Generate child name (could be related to parent surname)
                child_first_name = random.choice(STUDENT_FIRST_NAMES)
                child_last_name = last_name  # Same surname as parent
                child_class = random.choice(CLASSES)
                child_email = f"{child_first_name.lower()}.{child_last_name.lower()}{student_count}@student.ndirande.edu"
                admission_no = f"ND2025{admission_counter:03d}"
                
                # Create student
                student_result = conn.execute(text('''
                    INSERT INTO students (first_name, last_name, admission_no, email, class_name, is_active)
                    VALUES (:first_name, :last_name, :admission_no, :email, :class_name, true)
                    RETURNING id
                '''), {
                    'first_name': child_first_name,
                    'last_name': child_last_name,
                    'admission_no': admission_no,
                    'email': child_email,
                    'class_name': child_class
                })
                student_id = student_result.scalar()
                
                # Associate parent with student
                conn.execute(text('''
                    INSERT INTO parent_students (parent_user_id, student_id, relationship)
                    VALUES (:parent_id, :student_id, 'parent')
                '''), {'parent_id': parent_id, 'student_id': student_id})
                
                children_names.append(f"{child_first_name} {child_last_name}")
                
                # Create academic records for multiple terms and years
                for academic_year in ACADEMIC_YEARS:
                    for term in TERMS:
                        grades = generate_realistic_grades()
                        
                        for grade_data in grades:
                            # Add some teacher comments for recent records
                            teacher_comment = None
                            if academic_year == "2025" and term == "Term 3":
                                if grade_data['grade'] in ['A', 'B']:
                                    comments = [
                                        "Excellent performance, keep it up!",
                                        "Shows great understanding of concepts.",
                                        "Consistent improvement noted.",
                                        "Outstanding work this term."
                                    ]
                                elif grade_data['grade'] == 'C':
                                    comments = [
                                        "Good effort, room for improvement.",
                                        "Needs more practice with assignments.",
                                        "Showing steady progress."
                                    ]
                                else:
                                    comments = [
                                        "Needs extra support in this subject.",
                                        "Requires more attention to homework.",
                                        "Please see me for additional help."
                                    ]
                                teacher_comment = random.choice(comments)
                            
                            conn.execute(text('''
                                INSERT INTO academic_records (
                                    student_id, subject_name, ca_score, exam_score, overall_score,
                                    grade, grade_points, term, academic_year, is_finalized, teacher_comment
                                ) VALUES (
                                    :student_id, :subject_name, :ca_score, :exam_score, :overall_score,
                                    :grade, :grade_points, :term, :academic_year, :is_finalized, :teacher_comment
                                )
                            '''), {
                                'student_id': student_id,
                                'subject_name': grade_data['subject_name'],
                                'ca_score': grade_data['ca_score'],
                                'exam_score': grade_data['exam_score'],
                                'overall_score': grade_data['overall_score'],
                                'grade': grade_data['grade'],
                                'grade_points': grade_data['grade_points'],
                                'term': term,
                                'academic_year': academic_year,
                                'is_finalized': grade_data['is_finalized'],
                                'teacher_comment': teacher_comment
                            })
                
                # Create some communications for each student
                communication_types = [
                    ("Parent-Teacher Meeting Invitation", "general", "medium", 
                     f"Dear Parent, we would like to invite you to discuss {child_first_name}'s progress this term."),
                    ("Academic Performance Update", "notification", "high",
                     f"{child_first_name} has shown excellent improvement in Mathematics this term."),
                    ("School Event Notification", "announcement", "low",
                     f"Annual Sports Day is coming up. {child_first_name} is encouraged to participate."),
                    ("Fee Reminder", "urgent", "high",
                     f"This is a reminder that school fees for {child_first_name} are due by month end."),
                    ("Homework Reminder", "notification", "medium",
                     f"{child_first_name} has pending assignments in Science. Please ensure completion.")
                ]
                
                # Create 2-3 communications per student
                selected_comms = random.sample(communication_types, random.randint(2, 3))
                for title, comm_type, priority, content in selected_comms:
                    conn.execute(text('''
                        INSERT INTO communications (title, content, type, priority, target_audience, student_id, created_at)
                        VALUES (:title, :content, :type, :priority, 'parents', :student_id, :created_at)
                    '''), {
                        'title': title,
                        'content': content,
                        'type': comm_type,
                        'priority': priority,
                        'student_id': student_id,
                        'created_at': datetime.now()
                    })
            
            print(f"✅ {parent_count:2d}. {first_name} {last_name:<12} → {children_names} (Password: {parent_password})")
        
        # Create some general school communications
        print('📢 Creating general school communications...')
        general_communications = [
            ("Welcome Back to School", "announcement", "high", 
             "Welcome back students and parents! We're excited for the new academic year."),
            ("School Calendar Update", "notification", "medium",
             "Please note the updated school calendar with important dates for this year."),
            ("COVID-19 Safety Protocols", "urgent", "high",
             "Updated safety protocols for all students, staff and visitors."),
            ("PTA Meeting Notice", "general", "medium",
             "All parents are invited to the quarterly PTA meeting next Friday."),
            ("Academic Excellence Awards", "announcement", "low",
             "Congratulations to all students who achieved academic excellence this term!")
        ]
        
        for title, comm_type, priority, content in general_communications:
            conn.execute(text('''
                INSERT INTO communications (title, content, type, priority, target_audience, created_at)
                VALUES (:title, :content, :type, :priority, 'all', :created_at)
            '''), {
                'title': title,
                'content': content,
                'type': comm_type,
                'priority': priority,
                'created_at': datetime.now()
            })
        
        conn.commit()
        
        # Generate summary statistics
        print('\n' + '='*70)
        print('📊 SEEDING SUMMARY')
        print('='*70)
        
        stats = conn.execute(text('''
            SELECT 
                COUNT(DISTINCT u.id) as total_parents,
                COUNT(DISTINCT s.id) as total_students,
                COUNT(DISTINCT ar.id) as total_academic_records,
                COUNT(DISTINCT c.id) as total_communications,
                COUNT(DISTINCT ps.parent_user_id || '-' || ps.student_id) as parent_student_relationships
            FROM users u
            LEFT JOIN parent_students ps ON u.id = ps.parent_user_id
            LEFT JOIN students s ON ps.student_id = s.id
            LEFT JOIN academic_records ar ON s.id = ar.student_id
            LEFT JOIN communications c ON s.id = c.student_id OR c.student_id IS NULL
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            WHERE r.name = 'Parent (Restricted)'
        '')).fetchone()
        
        print(f"👨‍👩‍👧‍👦 Total Parents: {stats[0]}")
        print(f"🎓 Total Students: {stats[1]}")
        print(f"📚 Academic Records: {stats[2]}")
        print(f"📧 Communications: {stats[3]}")
        print(f"🔗 Parent-Child Links: {stats[4]}")
        
        # Sample academic performance
        performance_stats = conn.execute(text('''
            SELECT 
                ar.grade,
                COUNT(*) as count,
                ROUND(AVG(ar.overall_score), 1) as avg_score
            FROM academic_records ar
            WHERE ar.academic_year = '2025' AND ar.term = 'Term 3'
            GROUP BY ar.grade
            ORDER BY ar.grade
        '')).fetchall()
        
        print(f"\n📈 Current Term Grade Distribution:")
        for grade, count, avg_score in performance_stats:
            print(f"   Grade {grade}: {count:3d} records (Avg: {avg_score}%)")
        
        print('\n' + '='*70)
        print('🎯 PARENT LOGIN CREDENTIALS')
        print('='*70)
        print('🌐 URL: http://localhost:5174')
        print('🏢 Tenant: ndirande')
        print('📧 Sample Parent Emails:')
        
        # Show first 5 parent credentials
        sample_parents = conn.execute(text('''
            SELECT u.email, u.full_name
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            WHERE r.name = 'Parent (Restricted)'
            ORDER BY u.id
            LIMIT 5
        ''')).fetchall()
        
        for i, (email, name) in enumerate(sample_parents, 1):
            print(f"   {email:<30} Password: Parent{i}123")
        
        print(f"\n💡 All {len(PARENT_NAMES)} parents have passwords: Parent[N]123 (where N = 1,2,3...)")
        print('='*70)
        print('✅ SEEDING COMPLETED SUCCESSFULLY!')
        print('🚀 Ready to test the parent portal with realistic data!')
        print('='*70)
        
    except Exception as e:
        print(f'❌ Error during seeding: {e}')
        import traceback
        traceback.print_exc()
        conn.rollback()
