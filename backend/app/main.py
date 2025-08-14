from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routers.auth import router as auth_router
from app.api.routers.students import router as students_router
from app.api.routers.finance import router as finance_router
from app.api.routers.tenants import router as tenants_router
from app.api.routers.hq import router as hq_router
from app.api.routers.academic import router as academic_router
from app.api.routers.teachers import router as teachers_router
from app.api.routers.settings import router as settings_router
from app.api.routers.library import router as library_router
from app.api.routers.communications import router as communications_router
from app.db.init_db import init_public
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import SessionLocal
from app.tenancy.service import TenantService


app = FastAPI(title=settings.app_name)

origins: list[str] = []
if isinstance(settings.cors_origins, str) and settings.cors_origins:
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
elif isinstance(settings.cors_origins, list) and settings.cors_origins:
    origins = [str(o) for o in settings.cors_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],  # limit in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Refreshed-Token"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(tenants_router, prefix="/api/tenants", tags=["tenants"])
app.include_router(hq_router, prefix="/api/hq", tags=["hq"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(students_router, prefix="/api/students", tags=["students"])
app.include_router(finance_router, prefix="/api/finance", tags=["finance"])
app.include_router(academic_router, prefix="/api/academic", tags=["academic"])
app.include_router(teachers_router, prefix="/api/teachers", tags=["teachers"])
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])
app.include_router(library_router, prefix="/api/library", tags=["library"])
app.include_router(communications_router, prefix="/api/communications", tags=["communications"])


@app.on_event("startup")
def on_startup() -> None:
    init_public()
    # Ensure all tenant schemas exist and have baseline RBAC seeded
    db: Session = SessionLocal()
    try:
        schema_names = db.execute(text("SELECT schema_name FROM tenants ORDER BY id ASC")).scalars().all()
        svc = TenantService(db)
        for schema_name in schema_names:
            svc.ensure_schema(schema_name)
            db.execute(text(f"SET LOCAL search_path TO \"{schema_name}\", public"))
            svc.seed_defaults()
        db.commit()
    finally:
        db.close()


