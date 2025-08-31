from sqlalchemy import text, create_engine
from app.core.config import settings
import hashlib
import random
from datetime import datetime

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
    ("Francis", "Mvula", "francis.mvula@parent.ndirande.edu")
]

STUDENT_FIRST_NAMES = [
    "Abel", "Blessings", "Caroline", "Daniel", "Emmanuel", "Faith", "George", "Hope",
    "Isaac", "Joyce", "Kenneth", "Linda", "Moses", "Nancy", "Oscar", "Precious"
]

CLASSES = ["Form 1A", "Form 1B", "Form 2A", "Form 2B", "Form 3A", "Form 3B"]

SUBJECTS = [
    "Mathematics", "English", "Chichewa", "Biology", "Chemistry", "Physics", 
    "History", "Geography", "Life Skills", "Religious Studies"
]

def generate_grades():
    """Generate realistic grades for a student"""
    performance = random.choice([0.6, 0.7, 0.8, 0.85, 0.9])
    grades = []
    
    for subject in SUBJECTS:
        modifier = random.uniform(0.9, 1.1)
        actual_perf = min(0.95, performance * modifier)
        
        ca_score = random.uniform(20, 40) * actual_perf
        exam_score = random.uniform(30, 60) * actual_perf
        overall = ca_score + exam_score
        
        if overall >= 80: grade, points = "A", 4.0
        elif overall >= 70: grade, points = "B", 3.0
        elif overall >= 60: grade, points = "C", 2.0
        elif overall >= 50: grade, points = "D", 1.0
        else: grade, points = "F", 0.0
        
        grades.append({
            'subject': subject, 'ca': round(ca_score, 1), 'exam': round(exam_score, 1),
            'overall': round(overall, 1), 'grade': grade, 'points': points
        })
    return grades

print('🏫 SEEDING COMPREHENSIVE PARENT DATA')
print('='*50)

with engine.connect() as conn:
    conn.execute(text("SET search_path TO ndirande, public"))
    
    try:
        # Setup tables
        print('📋 Setting up tables...')
        
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS academic_records (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES students(id),
                subject_name VARCHAR(100),
                ca_score DECIMAL(5,2), exam_score DECIMAL(5,2),
                overall_score DECIMAL(5,2), grade VARCHAR(5),
                grade_points DECIMAL(3,2), term VARCHAR(20),
                academic_year VARCHAR(10), is_finalized BOOLEAN DEFAULT TRUE,
                teacher_comment TEXT
            )
        '''))
        
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS communications (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200), content TEXT, type VARCHAR(50),
                priority VARCHAR(20), student_id INTEGER REFERENCES students(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''))
        
        # Clear existing data
        print('🧹 Clearing old data...')
        conn.execute(text("DELETE FROM academic_records"))
        conn.execute(text("DELETE FROM communications"))  
        conn.execute(text("DELETE FROM parent_students"))
        conn.execute(text("DELETE FROM students WHERE id > 2"))
        conn.execute(text("DELETE FROM user_roles WHERE user_id > 1"))
        conn.execute(text("DELETE FROM users WHERE id > 1"))
        conn.commit()
        
        # Get parent role
        role_result = conn.execute(text("SELECT id FROM roles WHERE name = 'Parent (Restricted)'"))
        parent_role_id = role_result.scalar()
        
        print('👨‍👩‍👧‍👦 Creating families...')
        
        admission_num = 2000
        total_students = 0
        
        for i, (first_name, last_name, email) in enumerate(PARENT_NAMES, 1):
            # Create parent
            password = f"Parent{i}123"
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            parent_result = conn.execute(text('''
                INSERT INTO users (email, hashed_password, full_name, is_active)
                VALUES (:email, :password, :name, true) RETURNING id
            '''), {
                'email': email,
                'password': hashed_password,
                'name': f"{first_name} {last_name}"
            })
            parent_id = parent_result.scalar()
            
            # Assign role
            conn.execute(text("INSERT INTO user_roles VALUES (:uid, :rid)"), 
                        {'uid': parent_id, 'rid': parent_role_id})
            
            # Create 1-2 children
            num_children = random.choice([1, 2])
            children_info = []
            
            for child_num in range(num_children):
                total_students += 1
                admission_num += 1
                
                child_first = random.choice(STUDENT_FIRST_NAMES)
                child_class = random.choice(CLASSES)
                admission_no = f"ND2025{admission_num}"
                
                # Create student
                student_result = conn.execute(text('''
                    INSERT INTO students (first_name, last_name, admission_no, class_name)
                    VALUES (:first, :last, :admission, :class) RETURNING id
                '''), {
                    'first': child_first, 'last': last_name,
                    'admission': admission_no, 'class': child_class
                })
                student_id = student_result.scalar()
                
                # Link parent-student
                conn.execute(text("INSERT INTO parent_students VALUES (:pid, :sid, 'parent')"),
                           {'pid': parent_id, 'sid': student_id})
                
                children_info.append(f"{child_first} {last_name}")
                
                # Create academic records
                for year in ["2024", "2025"]:
                    for term in ["Term 1", "Term 2", "Term 3"]:
                        grades = generate_grades()
                        for grade in grades:
                            comment = None
                            if year == "2025" and term == "Term 3":
                                if grade['grade'] in ['A', 'B']:
                                    comment = "Excellent work this term!"
                                elif grade['grade'] == 'C':
                                    comment = "Good progress, keep improving."
                                else:
                                    comment = "Needs extra attention."
                            
                            conn.execute(text('''
                                INSERT INTO academic_records 
                                (student_id, subject_name, ca_score, exam_score, overall_score,
                                 grade, grade_points, term, academic_year, teacher_comment)
                                VALUES (:sid, :subj, :ca, :exam, :overall, :grade, :points, :term, :year, :comment)
                            '''), {
                                'sid': student_id, 'subj': grade['subject'],
                                'ca': grade['ca'], 'exam': grade['exam'], 'overall': grade['overall'],
                                'grade': grade['grade'], 'points': grade['points'],
                                'term': term, 'year': year, 'comment': comment
                            })
                
                # Create communications
                communications = [
                    (f"Progress Report - {child_first}", f"Dear parent, {child_first} is doing well this term.", "report"),
                    (f"Parent Meeting - {child_first}", f"Please attend the parent meeting for {child_first}.", "meeting"),
                    ("School Event", f"{child_first} is invited to the school sports day.", "event")
                ]
                
                for title, content, comm_type in communications:
                    conn.execute(text('''
                        INSERT INTO communications (title, content, type, priority, student_id)
                        VALUES (:title, :content, :type, 'medium', :sid)
                    '''), {'title': title, 'content': content, 'type': comm_type, 'sid': student_id})
            
            print(f"✅ {i:2d}. {first_name} {last_name:<12} → {', '.join(children_info)} (Pass: {password})")
        
        conn.commit()
        
        # Summary
        user_count = conn.execute(text("SELECT COUNT(*) FROM users WHERE id > 1")).scalar()
        student_count = conn.execute(text("SELECT COUNT(*) FROM students WHERE id > 2")).scalar()
        record_count = conn.execute(text("SELECT COUNT(*) FROM academic_records")).scalar()
        comm_count = conn.execute(text("SELECT COUNT(*) FROM communications")).scalar()
        
        print('\n' + '='*50)
        print('📊 SEEDING COMPLETED!')
        print('='*50)
        print(f"👨‍👩‍👧‍👦 Parents Created: {user_count}")
        print(f"🎓 Students Created: {student_count}")
        print(f"📚 Academic Records: {record_count}")
        print(f"📧 Communications: {comm_count}")
        
        print('\n🔑 TEST CREDENTIALS:')
        print('🌐 URL: http://localhost:5174')
        print('📧 Sample Logins:')
        for i in range(1, 6):
            email = PARENT_NAMES[i-1][2]
            print(f"   {email:<35} Password: Parent{i}123")
        
        print('\n✅ Ready to test parent portal with full data!')
        print('='*50)
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        conn.rollback()
