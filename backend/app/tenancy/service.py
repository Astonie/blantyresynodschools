from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.public import Tenant


TENANT_BASE_SCHEMA_SQL = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        full_name VARCHAR(255) NOT NULL,
        hashed_password VARCHAR(255) NOT NULL,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS roles (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) UNIQUE NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS permissions (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) UNIQUE NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS user_roles (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
        UNIQUE(user_id, role_id)
    );

    CREATE TABLE IF NOT EXISTS role_permissions (
        id SERIAL PRIMARY KEY,
        role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
        permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
        UNIQUE(role_id, permission_id)
    );

    CREATE TABLE IF NOT EXISTS students (
        id SERIAL PRIMARY KEY,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        admission_no VARCHAR(50) UNIQUE NOT NULL,
        date_of_birth DATE,
        gender VARCHAR(10),
        parent_name VARCHAR(200),
        parent_phone VARCHAR(20),
        parent_email VARCHAR(255),
        address TEXT,
        class_name VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS classes (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS subjects (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        code VARCHAR(20) UNIQUE NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS class_subjects (
        id SERIAL PRIMARY KEY,
        class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
        subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
        UNIQUE(class_id, subject_id)
    );

    CREATE TABLE IF NOT EXISTS teachers (
        id SERIAL PRIMARY KEY,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        phone VARCHAR(20),
        subject_specialty VARCHAR(100),
        hire_date DATE,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS teacher_assignments (
        id SERIAL PRIMARY KEY,
        teacher_id INTEGER REFERENCES teachers(id) ON DELETE CASCADE,
        class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
        subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
        academic_year VARCHAR(10),
        UNIQUE(teacher_id, class_id, subject_id, academic_year)
    );

    CREATE TABLE IF NOT EXISTS attendance (
        id SERIAL PRIMARY KEY,
        student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
        class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
        date DATE NOT NULL,
        status VARCHAR(20) NOT NULL, -- present, absent, late
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(student_id, class_id, date)
    );

    CREATE TABLE IF NOT EXISTS academic_records (
        id SERIAL PRIMARY KEY,
        student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
        class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
        subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
        academic_year VARCHAR(10) NOT NULL,
        term VARCHAR(20) NOT NULL,
        score DECIMAL(5,2),
        grade VARCHAR(5),
        remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(student_id, class_id, subject_id, academic_year, term)
    );

    -- Grading configuration tables
    CREATE TABLE IF NOT EXISTS grading_policies (
        id SERIAL PRIMARY KEY,
        policy_type VARCHAR(20) NOT NULL DEFAULT 'percentage', -- percentage | gpa
        ca_weight DECIMAL(5,2) DEFAULT 40.0, -- percent
        exam_weight DECIMAL(5,2) DEFAULT 60.0, -- percent
        pass_mark DECIMAL(5,2) DEFAULT 50.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS grade_scales (
        id SERIAL PRIMARY KEY,
        letter VARCHAR(5) NOT NULL,
        min_score DECIMAL(5,2) NOT NULL,
        max_score DECIMAL(5,2) NOT NULL,
        points DECIMAL(4,2), -- null when using percentage-only
        remarks VARCHAR(255),
        sort_order INTEGER DEFAULT 0
    );

    -- Parent mapping
    CREATE TABLE IF NOT EXISTS parent_students (
        id SERIAL PRIMARY KEY,
        parent_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
        UNIQUE(parent_user_id, student_id)
    );

    CREATE TABLE IF NOT EXISTS invoices (
        id SERIAL PRIMARY KEY,
        student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
        invoice_number VARCHAR(50) UNIQUE NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        description TEXT,
        due_date DATE,
        status VARCHAR(20) DEFAULT 'pending', -- pending, paid, overdue
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS payments (
        id SERIAL PRIMARY KEY,
        invoice_id INTEGER REFERENCES invoices(id) ON DELETE CASCADE,
        amount DECIMAL(10,2) NOT NULL,
        payment_date DATE NOT NULL,
        payment_method VARCHAR(50),
        reference_number VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

            CREATE TABLE IF NOT EXISTS exam_schedules (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
            class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
            exam_date DATE NOT NULL,
            start_time TIME NOT NULL,
            duration INTEGER DEFAULT 60,
            total_marks INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS library_resources (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            author VARCHAR(255),
            publisher VARCHAR(255),
            isbn VARCHAR(50),
            category VARCHAR(100),
            subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
            class_id INTEGER REFERENCES classes(id) ON DELETE SET NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size BIGINT,
            file_type VARCHAR(50),
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            is_active BOOLEAN DEFAULT true,
            download_count INTEGER DEFAULT 0,
            tags TEXT[]
        );

        CREATE TABLE IF NOT EXISTS announcements (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            audience_type VARCHAR(20) NOT NULL DEFAULT 'all', -- all | role | class
            audience_value VARCHAR(100),
            is_published BOOLEAN DEFAULT FALSE,
            scheduled_at TIMESTAMP NULL,
            published_at TIMESTAMP NULL,
            created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
"""

ALTER_TABLES_IF_NEEDED_SQL = """
ALTER TABLE IF EXISTS academic_records ADD COLUMN IF NOT EXISTS ca_score numeric(5,2);
ALTER TABLE IF EXISTS academic_records ADD COLUMN IF NOT EXISTS exam_score numeric(5,2);
ALTER TABLE IF EXISTS academic_records ADD COLUMN IF NOT EXISTS overall_score numeric(5,2);
ALTER TABLE IF EXISTS academic_records ADD COLUMN IF NOT EXISTS grade_points numeric(4,2);
ALTER TABLE IF EXISTS academic_records ADD COLUMN IF NOT EXISTS is_finalized boolean DEFAULT false;
ALTER TABLE IF EXISTS students ADD COLUMN IF NOT EXISTS student_number varchar(64);
CREATE UNIQUE INDEX IF NOT EXISTS uq_students_student_number ON students(student_number) WHERE student_number IS NOT NULL;
"""


class TenantService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_slug(self, slug: str) -> Optional[Tenant]:
        return self.db.query(Tenant).filter(Tenant.slug == slug).first()

    def create(self, name: str, slug: str, schema_name: str) -> Tenant:
        tenant = Tenant(name=name, slug=slug, schema_name=schema_name)
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def ensure_schema(self, schema_name: str) -> None:
        # Create schema (idempotent)
        self.db.execute(text(f"CREATE SCHEMA IF NOT EXISTS \"{schema_name}\""))
        # Set search_path and create tables
        self.db.execute(text(f"SET LOCAL search_path TO \"{schema_name}\", public"))
        statements = [s.strip() for s in TENANT_BASE_SCHEMA_SQL.split(";") if s.strip()]
        for statement in statements:
            if statement:  # Ensure statement is not empty
                self.db.execute(text(statement))
        # Apply non-breaking schema updates if tables already existed
        for statement in [s.strip() for s in ALTER_TABLES_IF_NEEDED_SQL.split(";") if s.strip()]:
            self.db.execute(text(statement))
        self.db.commit()

    def seed_defaults(self):
        """Seed default roles and permissions for a tenant."""
        # First, ensure we're in the correct schema
        schema_name = self.db.execute(text("SELECT current_schema()")).scalar()
        
        # Create permissions if they don't exist
        permissions_data = [
            # Student management permissions
            ("students.read", "View student information"),
            ("students.create", "Create new students"),
            ("students.update", "Update student information"),
            ("students.delete", "Delete students"),
            
            # Finance management permissions
            ("finance.read", "View financial information"),
            ("finance.create", "Create invoices and payments"),
            ("finance.update", "Update financial records"),
            ("finance.delete", "Delete financial records"),
            
            # Academic management permissions
            ("academic.read", "View academic records"),
            ("academic.create", "Create academic records"),
            ("academic.update", "Update academic records"),
            ("academic.delete", "Delete academic records"),
            ("academic.manage", "Manage academic settings and schedules"),
            ("academic.attendance", "Manage student attendance"),
            ("academic.record", "Record academic results"),
            
            # Library permissions
            ("library.read", "Access library resources"),
            ("library.manage", "Manage library resources"),
            ("library.upload", "Upload library materials"),
            
            # Communications permissions
            ("communications.read", "View announcements and communications"),
            ("communications.manage", "Manage communications and announcements"),
            ("communications.send", "Send or publish communications"),
            
            # Teacher management permissions
            ("teachers.read", "View teacher information"),
            ("teachers.create", "Create new teachers"),
            ("teachers.update", "Update teacher information"),
            ("teachers.delete", "Delete teachers"),
            
            # Settings management permissions
            ("settings.manage", "Manage system settings, users, roles, and permissions"),
            
            # Dashboard permissions
            ("dashboard.view", "View dashboard and reports"),
            
            # Attendance permissions
            ("attendance.read", "View attendance records"),
            ("attendance.create", "Create attendance records"),
            ("attendance.update", "Update attendance records"),
            
            # Reports permissions
            ("reports.view", "View system reports"),
            ("reports.generate", "Generate reports"),
        ]
        
        for perm_name, perm_desc in permissions_data:
            existing = self.db.execute(
                text("SELECT id FROM permissions WHERE name = :name"),
                {"name": perm_name}
            ).scalar()
            if not existing:
                self.db.execute(
                    text("INSERT INTO permissions(name, description) VALUES (:name, :description)"),
                    {"name": perm_name, "description": perm_desc}
                )
        
        # Create roles if they don't exist
        roles_data = [
            ("Super Administrator", "Full system access with all permissions"),
            ("School Administrator", "School-level administration with most permissions"),
            ("Administrator", "Legacy admin role with broad permissions"),
            ("Teacher", "Teacher access with student and academic permissions"),
            ("Finance Officer", "Finance management with limited other access"),
            ("Student", "Student access with limited read permissions"),
            ("Parent", "Parent access to view their children's information"),
        ]
        
        for role_name, role_desc in roles_data:
            existing = self.db.execute(
                text("SELECT id FROM roles WHERE name = :name"),
                {"name": role_name}
            ).scalar()
            if not existing:
                self.db.execute(
                    text("INSERT INTO roles(name, description) VALUES (:name, :description)"),
                    {"name": role_name, "description": role_desc}
                )
        
        # Assign permissions to roles (baseline)
        role_permissions = {
            "Super Administrator": [
                "students.read", "students.create", "students.update", "students.delete",
                "finance.read", "finance.create", "finance.update", "finance.delete",
                "academic.read", "academic.create", "academic.update", "academic.delete",
                "academic.manage", "academic.attendance", "academic.record",
                "teachers.read", "teachers.create", "teachers.update", "teachers.delete",
                "settings.manage", "dashboard.view", "attendance.read", "attendance.create",
                "attendance.update", "reports.view", "reports.generate",
                "library.read", "library.manage", "library.upload",
                "communications.read", "communications.manage", "communications.send"
            ],
            "School Administrator": [
                "students.read", "students.create", "students.update", "students.delete",
                "finance.read", "finance.create", "finance.update",
                "academic.read", "academic.create", "academic.update",
                "teachers.read", "teachers.create", "teachers.update",
                "dashboard.view", "attendance.read", "attendance.create",
                "attendance.update", "reports.view", "reports.generate",
                "library.read", "library.manage", "library.upload", "settings.manage",
                "communications.read", "communications.manage", "communications.send"
            ],
            "Administrator": [
                "settings.manage", "dashboard.view",
                "students.read", "students.create", "students.update", "students.delete",
                "teachers.read", "teachers.create", "teachers.update",
                "academic.read", "academic.create", "academic.update",
                "finance.read", "finance.create", "finance.update",
                "library.read", "library.manage", "library.upload",
                "communications.read", "communications.manage", "communications.send"
            ],
            "Teacher": [
                "students.read", "students.update",
                "academic.read", "academic.create", "academic.update",
                "dashboard.view", "attendance.read", "attendance.create",
                "attendance.update", "reports.view",
                "library.read",
                "communications.read"
            ],
            "Finance Officer": [
                "students.read",
                "finance.read", "finance.create", "finance.update", "finance.delete",
                "dashboard.view", "reports.view", "reports.generate",
                "communications.read"
            ],
            "Student": [
                "students.read", "academic.read", "dashboard.view",
                "library.read",
                "communications.read"
            ],
            "Parent": [
                "students.read", "academic.read", "dashboard.view",
                "communications.read"
            ]
        }
        
        for role_name, permissions in role_permissions.items():
            role_id = self.db.execute(
                text("SELECT id FROM roles WHERE name = :name"),
                {"name": role_name}
            ).scalar()
            
            if role_id:
                for perm_name in permissions:
                    perm_id = self.db.execute(
                        text("SELECT id FROM permissions WHERE name = :name"),
                        {"name": perm_name}
                    ).scalar()
                    
                    if perm_id:
                        # Check if assignment already exists
                        existing = self.db.execute(
                            text("SELECT id FROM role_permissions WHERE role_id = :role_id AND permission_id = :perm_id"),
                            {"role_id": role_id, "perm_id": perm_id}
                        ).scalar()
                        
                        if not existing:
                            self.db.execute(
                                text("INSERT INTO role_permissions(role_id, permission_id) VALUES (:role_id, :perm_id)"),
                                {"role_id": role_id, "perm_id": perm_id}
                            )
        
        # Ensure any role that has settings.manage also gets all library permissions (for legacy roles)
        lib_perm_ids = self.db.execute(
            text("SELECT id, name FROM permissions WHERE name IN ('library.read','library.manage','library.upload')")
        ).mappings().all()
        settings_manage_id = self.db.execute(
            text("SELECT id FROM permissions WHERE name = 'settings.manage'")
        ).scalar()
        if settings_manage_id and lib_perm_ids:
            admin_like_role_ids = self.db.execute(
                text(
                    """
                    SELECT DISTINCT r.id
                    FROM roles r
                    JOIN role_permissions rp ON rp.role_id = r.id
                    WHERE rp.permission_id = :pm
                    UNION
                    SELECT id FROM roles WHERE name IN ('Administrator','School Administrator','Super Administrator')
                    """
                ),
                {"pm": settings_manage_id}
            ).scalars().all()
            for rid in admin_like_role_ids:
                for lp in lib_perm_ids:
                    existing = self.db.execute(
                        text("SELECT 1 FROM role_permissions WHERE role_id = :rid AND permission_id = :pid"),
                        {"rid": rid, "pid": lp.id}
                    ).scalar()
                    if not existing:
                        self.db.execute(
                            text("INSERT INTO role_permissions(role_id, permission_id) VALUES (:rid, :pid)"),
                            {"rid": rid, "pid": lp.id}
                        )
        
        # Create test users if they don't exist
        test_users = [
            {
                "email": "admin@blantyresynod.org",
                "full_name": "System Administrator",
                "password": "admin123",
                "roles": ["Super Administrator"]
            },
            {
                "email": "principal@school1.org",
                "full_name": "School Principal",
                "password": "principal123",
                "roles": ["School Administrator"]
            },
            {
                "email": "teacher1@school1.org",
                "full_name": "John Teacher",
                "password": "teacher123",
                "roles": ["Teacher"]
            },
            {
                "email": "finance@school1.org",
                "full_name": "Finance Manager",
                "password": "finance123",
                "roles": ["Finance Officer"]
            },
            {
                "email": "student1@school1.org",
                "full_name": "Alice Student",
                "password": "student123",
                "roles": ["Student"]
            },
            {
                "email": "parent1@school1.org",
                "full_name": "Bob Parent",
                "password": "parent123",
                "roles": ["Parent"]
            }
        ]
        
        from app.services.security import hash_password
        
        for user_data in test_users:
            existing = self.db.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": user_data["email"]}
            ).scalar()
            
            if not existing:
                # Create user
                hashed_password = hash_password(user_data["password"])
                result = self.db.execute(
                    text(
                        """
                        INSERT INTO users(email, full_name, hashed_password, is_active)
                        VALUES (:email, :full_name, :password, :is_active)
                        RETURNING id
                        """
                    ),
                    {
                        "email": user_data["email"],
                        "full_name": user_data["full_name"],
                        "password": hashed_password,
                        "is_active": True
                    }
                )
                user_id = result.scalar()
                
                # Assign roles
                for role_name in user_data["roles"]:
                    role_id = self.db.execute(
                        text("SELECT id FROM roles WHERE name = :name"),
                        {"name": role_name}
                    ).scalar()
                    
                    if role_id:
                        self.db.execute(
                            text("INSERT INTO user_roles(user_id, role_id) VALUES (:user_id, :role_id)"),
                            {"user_id": user_id, "role_id": role_id}
                        )
        
        # Ensure default grading policy exists BEFORE committing so current tenant search_path applies
        existing_policy = self.db.execute(text("SELECT id FROM grading_policies LIMIT 1")).scalar()
        if not existing_policy:
            self.db.execute(text("""
                INSERT INTO grading_policies(policy_type, ca_weight, exam_weight, pass_mark)
                VALUES ('percentage', 40.0, 60.0, 50.0)
            """))

        # Ensure default grade scales exist (A-F)
        existing_scales = self.db.execute(text("SELECT COUNT(*) FROM grade_scales")).scalar() or 0
        if existing_scales == 0:
            # Percentage-based default; points provided for GPA compatibility
            scales = [
                ('A', 80.0, 100.0, 4.00, 'Excellent', 1),
                ('B', 70.0, 79.99, 3.00, 'Very Good', 2),
                ('C', 60.0, 69.99, 2.00, 'Good', 3),
                ('D', 50.0, 59.99, 1.00, 'Pass', 4),
                ('E', 40.0, 49.99, 0.00, 'Weak', 5),
                ('F', 0.0, 39.99, 0.00, 'Fail', 6)
            ]
            for letter, min_s, max_s, pts, note, ord in scales:
                self.db.execute(text("""
                    INSERT INTO grade_scales(letter, min_score, max_score, points, remarks, sort_order)
                    VALUES (:l, :min, :max, :p, :r, :o)
                """), {"l": letter, "min": min_s, "max": max_s, "p": pts, "r": note, "o": ord})

        # Final commit for all seeded data
        self.db.commit()


