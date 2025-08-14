from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.base import PublicBase
from app.db.session import engine
from app.models import public  # ensure models are imported so metadata is populated


def init_public() -> None:
    # Create public metadata tables using ORM for the public schema
    PublicBase.metadata.create_all(bind=engine)

    # Ensure tenants table exists if defined by ORM; otherwise a fallback DDL could be placed here


