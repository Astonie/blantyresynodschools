import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.config import settings
from app.db.session import get_public_session
from app.tenancy.deps import get_tenant_db
from app.services.security import create_access_token


# Test database URL - use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    # Create tables
    from app.db.base import PublicBase, TenantBase
    # For tests, we'll use PublicBase as the main base
    PublicBase.metadata.create_all(bind=test_engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        PublicBase.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def public_db_session(db_session: Session) -> Generator[Session, None, None]:
    """Create a public database session for tenant management tests."""
    # Initialize public schema
    db_session.execute(text("""
        CREATE TABLE IF NOT EXISTS tenants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name varchar(255) NOT NULL,
            slug varchar(64) NOT NULL UNIQUE,
            schema_name varchar(64) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """))
    db_session.commit()
    yield db_session


@pytest.fixture(scope="function")
def tenant_db_session(db_session: Session) -> Generator[Session, None, None]:
    """Create a tenant database session for tenant-specific tests."""
    # For SQLite tests, we'll use table prefixes instead of schemas
    # Create a test tenant schema
    schema_name = "test_tenant"
    # SQLite doesn't support schemas, so we'll use table prefixes
    # db_session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
    # db_session.execute(text(f'SET search_path TO "{schema_name}", public'))
    
    # Enable foreign key constraints in SQLite
    db_session.execute(text("PRAGMA foreign_keys=ON"))

    # Create tenant tables
    db_session.execute(text("""
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name varchar(64) NOT NULL UNIQUE,
            description varchar(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """))

    db_session.execute(text("""
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name varchar(128) NOT NULL UNIQUE,
            description varchar(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """))
    
    db_session.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email varchar(255) NOT NULL UNIQUE,
            full_name varchar(255),
            hashed_password varchar(255) NOT NULL,
            is_active INTEGER DEFAULT 1 NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """))
    
    db_session.execute(text("""
        CREATE TABLE IF NOT EXISTS user_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id int NOT NULL,
            role_id int NOT NULL,
            UNIQUE(user_id, role_id)
        )
    """))

    db_session.execute(text("""
        CREATE TABLE IF NOT EXISTS role_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id int NOT NULL,
            permission_id int NOT NULL,
            UNIQUE(role_id, permission_id)
        )
    """))
    
    db_session.execute(text("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name varchar(128) NOT NULL,
            last_name varchar(128) NOT NULL,
            gender varchar(16),
            date_of_birth date,
            admission_no varchar(64) NOT NULL UNIQUE,
            current_class varchar(64),
            parent_phone varchar(20),
            parent_email varchar(255),
            address text,
            emergency_contact varchar(255),
            emergency_phone varchar(20),
            enrollment_date date DEFAULT CURRENT_DATE,
            status varchar(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """))
    
    db_session.execute(text("""
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name varchar(64) NOT NULL UNIQUE,
            grade_level varchar(32),
            capacity int DEFAULT 40,
            teacher_id int,
            academic_year varchar(16) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """))
    
    db_session.execute(text("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name varchar(128) NOT NULL,
            code varchar(16) NOT NULL UNIQUE,
            description text,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """))
    db_session.execute(text("""
        CREATE TABLE IF NOT EXISTS class_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id int NOT NULL,
            subject_id int NOT NULL,
            teacher_id int,
            UNIQUE(class_id, subject_id)
        )
    """))
    db_session.execute(text("""
        CREATE TABLE IF NOT EXISTS academic_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id int NOT NULL,
            subject_id int NOT NULL,
            class_id int NOT NULL,
            term varchar(32) NOT NULL,
            academic_year varchar(16) NOT NULL,
            score REAL,
            ca_score REAL,
            exam_score REAL,
            overall_score REAL,
            grade varchar(4),
            remarks text,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """))
    db_session.execute(text("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id int NOT NULL,
            class_id int NOT NULL,
            date date NOT NULL,
            status varchar(16) NOT NULL DEFAULT 'present',
            notes text,
            recorded_by int,
            UNIQUE(student_id, class_id, date)
        )
    """))

    # Ensure a clean state for each test run (tables above are tenant-scoped)
    for table in [
        "attendance",
        "academic_records",
        "class_subjects",
        "payments",
        "invoices",
        "subjects",
        "classes",
        "students",
        "user_roles",
        "role_permissions",
        "users",
        "roles",
        "permissions",
    ]:
        try:
            db_session.execute(text(f"DELETE FROM {table}"))
        except Exception:
            pass
    
    db_session.execute(text("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id int NOT NULL,
            term varchar(32) NOT NULL,
            currency varchar(8) NOT NULL DEFAULT 'MWK',
            amount REAL NOT NULL,
            status varchar(16) NOT NULL DEFAULT 'pending',
            due_date date,
            issued_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE RESTRICT
        )
    """))
    
    db_session.execute(text("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id int NOT NULL,
            amount REAL NOT NULL,
            method varchar(32) NOT NULL,
            reference varchar(128),
            paid_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
        )
    """))
    
    db_session.commit()
    yield db_session


@pytest.fixture
def client(public_db_session: Session, tenant_db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with dependency overrides."""
    
    def override_get_public_session():
        try:
            yield public_db_session
        finally:
            pass
    
    def override_get_tenant_db():
        try:
            yield tenant_db_session
        finally:
            pass
    
    app.dependency_overrides[get_public_session] = override_get_public_session
    app.dependency_overrides[get_tenant_db] = override_get_tenant_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_tenant(public_db_session: Session) -> dict:
    """Create a test tenant."""
    from app.tenancy.service import TenantService
    
    svc = TenantService(public_db_session)
    tenant = svc.create(
        name="Test School",
        slug="test-school",
        schema_name="test_tenant"
    )
    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "schema_name": tenant.schema_name
    }


@pytest.fixture
def test_user(tenant_db_session: Session) -> dict:
    """Create a test user with Administrator role."""
    from app.services.security import hash_password
    
            # Create roles (use INSERT OR IGNORE to avoid duplicates)
    tenant_db_session.execute(text("""
        INSERT OR IGNORE INTO roles(name) VALUES
        ('Administrator'),
        ('Teacher'),
        ('Student'),
        ('Parent'),
        ('Accountant'),
        ('Head Teacher')
    """))

    # Seed required permissions across domains used by tests
    tenant_db_session.execute(text("""
        INSERT OR IGNORE INTO permissions(name, description) VALUES
        ('students.read', 'View students'),
        ('students.create', 'Create students'),
        ('students.update', 'Update students'),
        ('students.delete', 'Delete students'),
        ('teachers.read', 'View teachers'),
        ('teachers.create', 'Create teachers'),
        ('teachers.update', 'Update teachers'),
        ('teachers.delete', 'Delete teachers'),
        ('academic.read', 'View academic records'),
        ('academic.record', 'Record academic results'),
        ('academic.attendance', 'Record attendance'),
        ('finance.read', 'View invoices and payments'),
        ('finance.write', 'Create invoices and payments'),
        ('settings.manage', 'Manage tenant settings')
    """))
    
    # Create user (use INSERT OR IGNORE to avoid duplicates)
    hashed_password = hash_password("testpassword123")
    tenant_db_session.execute(text("""
        INSERT OR IGNORE INTO users(email, full_name, hashed_password)
        VALUES (:email, :name, :password)
    """), {
        "email": "admin@testschool.com",
        "name": "Test Administrator",
        "password": hashed_password
    })
    
    # Get user and role IDs
    user_id = tenant_db_session.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": "admin@testschool.com"}
    ).scalar()
    
    admin_role_id = tenant_db_session.execute(
        text("SELECT id FROM roles WHERE name = 'Administrator'")
    ).scalar()
    perm_read_id = tenant_db_session.execute(text("SELECT id FROM permissions WHERE name = 'finance.read'")) .scalar()
    perm_write_id = tenant_db_session.execute(text("SELECT id FROM permissions WHERE name = 'finance.write'")) .scalar()
    # Also grant broad permissions to Administrator for other test suites
    p_students = [
        tenant_db_session.execute(text("SELECT id FROM permissions WHERE name = :n"), {"n": n}).scalar()
        for n in [
            'students.read','students.create','students.update','students.delete',
            'teachers.read','teachers.create','teachers.update','teachers.delete',
            'academic.read','academic.record','academic.attendance','settings.manage'
        ]
    ]
    
    # Assign role (use INSERT OR IGNORE to avoid duplicates)
    tenant_db_session.execute(text("""
        INSERT OR IGNORE INTO user_roles(user_id, role_id) VALUES (:user_id, :role_id)
    """), {"user_id": user_id, "role_id": admin_role_id})

    # Map Administrator role to finance permissions
    if admin_role_id and perm_read_id:
        tenant_db_session.execute(text("""
            INSERT OR IGNORE INTO role_permissions(role_id, permission_id) VALUES (:r, :p)
        """), {"r": admin_role_id, "p": perm_read_id})
    if admin_role_id and perm_write_id:
        tenant_db_session.execute(text("""
            INSERT OR IGNORE INTO role_permissions(role_id, permission_id) VALUES (:r, :p)
        """), {"r": admin_role_id, "p": perm_write_id})
    for pid in p_students:
        if admin_role_id and pid:
            tenant_db_session.execute(text("""
                INSERT OR IGNORE INTO role_permissions(role_id, permission_id) VALUES (:r, :p)
            """), {"r": admin_role_id, "p": pid})
    
    tenant_db_session.commit()
    
    return {
        "id": user_id,
        "email": "admin@testschool.com",
        "full_name": "Test Administrator",
        "role": "Administrator"
    }


@pytest.fixture
def readonly_user(tenant_db_session: Session) -> dict:
    """Create a test user with Teacher role (no finance permissions)."""
    from app.services.security import hash_password

    # Ensure Teacher role exists
    teacher_role_id = tenant_db_session.execute(text("SELECT id FROM roles WHERE name = 'Teacher'")) .scalar()
    if not teacher_role_id:
        tenant_db_session.execute(text("INSERT OR IGNORE INTO roles(name) VALUES ('Teacher')"))
        teacher_role_id = tenant_db_session.execute(text("SELECT id FROM roles WHERE name = 'Teacher'")) .scalar()

    # Create user
    tenant_db_session.execute(text("""
        INSERT OR IGNORE INTO users(email, full_name, hashed_password)
        VALUES (:email, :name, :password)
    """), {
        "email": "teacher@testschool.com",
        "name": "Test Teacher",
        "password": hash_password("testpassword123")
    })

    user_id = tenant_db_session.execute(text("SELECT id FROM users WHERE email = :email"), {"email": "teacher@testschool.com"}).scalar()
    # Assign Teacher role
    tenant_db_session.execute(text("INSERT OR IGNORE INTO user_roles(user_id, role_id) VALUES (:u, :r)"), {"u": user_id, "r": teacher_role_id})
    tenant_db_session.commit()
    return {"id": user_id, "email": "teacher@testschool.com", "role": "Teacher"}


@pytest.fixture
def readonly_auth_headers(readonly_user: dict) -> dict:
    token = create_access_token(subject=str(readonly_user["id"]))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers(test_user: dict) -> dict:
    """Create authentication headers for API requests."""
    token = create_access_token(
        subject=str(test_user["id"]), extra={"tenant": "test_tenant"}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_student(tenant_db_session: Session) -> dict:
    """Create a test student."""
    tenant_db_session.execute(text("""
        INSERT OR IGNORE INTO students(
            first_name, last_name, gender, admission_no, current_class,
            parent_phone, parent_email
        ) VALUES (:first, :last, :gender, :adm, :cls, :phone, :email)
    """), {
        "first": "John",
        "last": "Doe",
        "gender": "Male",
        "adm": "STU001",
        "cls": "Form 1",
        "phone": "+265123456789",
        "email": "parent@example.com"
    })
    
    student_id = tenant_db_session.execute(
        text("SELECT id FROM students WHERE admission_no = :adm"),
        {"adm": "STU001"}
    ).scalar()
    
    tenant_db_session.commit()
    
    return {
        "id": student_id,
        "first_name": "John",
        "last_name": "Doe",
        "admission_no": "STU001"
    }


@pytest.fixture
def test_class(tenant_db_session: Session) -> dict:
    """Create a test class."""
    exists = tenant_db_session.execute(text("SELECT id FROM classes WHERE name = :name"), {"name": "Form 1A"}).scalar()
    if not exists:
        tenant_db_session.execute(text("""
            INSERT INTO classes(name, grade_level, capacity, academic_year)
            VALUES (:name, :grade, :cap, :year)
        """), {
            "name": "Form 1A",
            "grade": "Form 1",
            "cap": 40,
            "year": "2024"
        })
    
    class_id = tenant_db_session.execute(
        text("SELECT id FROM classes WHERE name = :name"),
        {"name": "Form 1A"}
    ).scalar()
    
    tenant_db_session.commit()
    
    return {
        "id": class_id,
        "name": "Form 1A",
        "grade_level": "Form 1"
    }


@pytest.fixture
def test_subject(tenant_db_session: Session) -> dict:
    """Create a test subject."""
    exists = tenant_db_session.execute(text("SELECT id FROM subjects WHERE code = :code"), {"code": "MATH"}).scalar()
    if not exists:
        tenant_db_session.execute(text("""
            INSERT INTO subjects(name, code, description)
            VALUES (:name, :code, :desc)
        """), {
            "name": "Mathematics",
            "code": "MATH",
            "desc": "Basic mathematics course"
        })
    
    subject_id = tenant_db_session.execute(
        text("SELECT id FROM subjects WHERE code = :code"),
        {"code": "MATH"}
    ).scalar()
    
    tenant_db_session.commit()
    
    return {
        "id": subject_id,
        "name": "Mathematics",
        "code": "MATH"
    }
