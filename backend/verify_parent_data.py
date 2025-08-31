from sqlalchemy import text, create_engine
from app.core.config import settings

engine = create_engine(settings.database_url)

print('🔍 VERIFYING SEEDED PARENT DATA')
print('='*60)

with engine.connect() as conn:
    conn.execute(text("SET search_path TO ndirande, public"))
    
    try:
        # Show parent summary
        parents = conn.execute(text('''
            SELECT u.id, u.full_name, u.email,
                   COUNT(DISTINCT ps.student_id) as children_count
            FROM users u 
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            LEFT JOIN parent_students ps ON u.id = ps.parent_user_id
            WHERE r.name = 'Parent (Restricted)'
            GROUP BY u.id, u.full_name, u.email
            ORDER BY u.id
        ''')).fetchall()
        
        print(f'👨‍👩‍👧‍👦 PARENTS WITH CHILDREN ({len(parents)} families)')
        print('-'*60)
        
        total_children = 0
        for parent in parents:
            total_children += parent[3]
            print(f'{parent[1]:<20} → {parent[3]} child(ren) | {parent[2]}')
        
        print(f'\nTotal Children: {total_children}')
        
        # Show sample student with academic records
        print(f'\n🎓 SAMPLE STUDENT ACADEMIC RECORDS')
        print('-'*60)
        
        sample_student = conn.execute(text('''
            SELECT s.id, s.first_name, s.last_name, s.admission_no, s.class_name,
                   u.full_name as parent_name
            FROM students s
            JOIN parent_students ps ON s.id = ps.student_id
            JOIN users u ON ps.parent_user_id = u.id
            LIMIT 1
        ''')).fetchone()
        
        if sample_student:
            student_id, first_name, last_name, admission_no, class_name, parent_name = sample_student
            print(f'Student: {first_name} {last_name} ({admission_no}) - {class_name}')
            print(f'Parent: {parent_name}')
            
            # Show current term grades
            grades = conn.execute(text('''
                SELECT subject_name, ca_score, exam_score, overall_score, grade, grade_points, teacher_comment
                FROM academic_records
                WHERE student_id = :sid AND academic_year = '2025' AND term = 'Term 3'
                ORDER BY subject_name
            '''), {'sid': student_id}).fetchall()
            
            print(f'\n📚 Current Term (Term 3, 2025) Results:')
            print('-'*60)
            total_points = 0
            for grade in grades:
                subject, ca, exam, overall, letter_grade, points, comment = grade
                total_points += points
                comment_text = f' | {comment}' if comment else ''
                print(f'{subject:<15} CA:{ca:5.1f} Exam:{exam:5.1f} Total:{overall:5.1f} Grade:{letter_grade} ({points:.1f} pts){comment_text}')
            
            gpa = total_points / len(grades) if grades else 0
            print(f'\nGPA: {gpa:.2f} | Total Subjects: {len(grades)}')
        
        # Show sample communications
        print(f'\n📧 SAMPLE COMMUNICATIONS')
        print('-'*60)
        
        communications = conn.execute(text('''
            SELECT c.title, c.content, c.type, c.priority, 
                   s.first_name || ' ' || s.last_name as student_name,
                   u.full_name as parent_name
            FROM communications c
            LEFT JOIN students s ON c.student_id = s.id
            LEFT JOIN parent_students ps ON s.id = ps.student_id
            LEFT JOIN users u ON ps.parent_user_id = u.id
            ORDER BY c.created_at DESC
            LIMIT 5
        ''')).fetchall()
        
        for comm in communications:
            title, content, comm_type, priority, student_name, parent_name = comm
            target = f'→ {student_name} (Parent: {parent_name})' if student_name else '→ General'
            print(f'[{priority.upper()}] {title}')
            print(f'   {content[:60]}... {target}')
            print()
        
        # Performance statistics
        print(f'📊 ACADEMIC PERFORMANCE STATISTICS (Current Term)')
        print('-'*60)
        
        performance = conn.execute(text('''
            SELECT grade, COUNT(*) as count, 
                   ROUND(AVG(overall_score), 1) as avg_score,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
            FROM academic_records
            WHERE academic_year = '2025' AND term = 'Term 3'
            GROUP BY grade
            ORDER BY grade
        ''')).fetchall()
        
        for perf in performance:
            grade, count, avg_score, percentage = perf
            print(f'Grade {grade}: {count:3d} records ({percentage:5.1f}%) | Avg Score: {avg_score}%')
        
        print('\n' + '='*60)
        print('✅ DATA VERIFICATION COMPLETE!')
        print('🚀 Parent portal is ready with realistic academic data!')
        print('='*60)
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
