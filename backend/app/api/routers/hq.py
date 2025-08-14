from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_public_session, tenant_session
from app.api.deps import require_hq_access


router = APIRouter()


@router.get("/tenants", dependencies=[Depends(require_hq_access)])
def list_tenants(db: Session = Depends(get_public_session)):
    rows = db.execute(text("SELECT id, name, slug, schema_name, created_at FROM tenants ORDER BY id DESC")).mappings().all()
    return [dict(r) for r in rows]


@router.get("/summary", dependencies=[Depends(require_hq_access)])
def summary(db: Session = Depends(get_public_session)):
    tenants = db.execute(text("SELECT id, name, slug, schema_name FROM tenants ORDER BY id ASC")).mappings().all()
    results: list[dict] = []
    for t in tenants:
        schema = t["schema_name"]
        students = invoices = payments = 0
        try:
            with tenant_session(schema) as tdb:
                students = int(tdb.execute(text("SELECT count(*) FROM students")).scalar() or 0)
                invoices = int(tdb.execute(text("SELECT count(*) FROM invoices")).scalar() or 0)
                payments = int(tdb.execute(text("SELECT count(*) FROM payments")).scalar() or 0)
        except Exception:
            pass
        results.append({
            "id": t["id"],
            "name": t["name"],
            "slug": t["slug"],
            "students": students,
            "invoices": invoices,
            "payments": payments,
        })
    return {"tenants": results}


