from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


engine: Engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_public_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def tenant_session(schema_name: str) -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        with session.begin():
            session.execute(
                text("select set_config('search_path', :sp, true)").execution_options(autocommit=False),
                {"sp": f"{schema_name}, public"},
            )
            yield session
    finally:
        session.close()


def get_tenant_session(schema_name: str) -> Generator[Session, None, None]:
    with tenant_session(schema_name) as s:
        yield s



