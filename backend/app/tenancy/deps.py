from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_public_session, get_tenant_session
from app.tenancy.service import TenantService


def get_tenant_slug(x_tenant: str | None = Header(default=None, alias="X-Tenant")) -> str:
    if not x_tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing X-Tenant header")
    return x_tenant.strip()


def get_tenant_schema(
    slug: str = Depends(get_tenant_slug),
    db: Session = Depends(get_public_session),
) -> str:
    tenant = TenantService(db).get_by_slug(slug)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return tenant.schema_name


def get_tenant_db(schema_name: str = Depends(get_tenant_schema)):
    yield from get_tenant_session(schema_name)



