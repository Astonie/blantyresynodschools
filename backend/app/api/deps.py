from typing import Callable, Iterable

from fastapi import Depends, Header, HTTPException, status, Response
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.tenancy.deps import get_tenant_db
from app.services.security import create_access_token


def get_bearer_token(authorization: str | None = Header(default=None, alias="Authorization")) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")
    return authorization.split(" ", 1)[1]


def get_current_user_id(response: Response, token: str = Depends(get_bearer_token)) -> int:
    try:
        # Decode and validate token (exp enforced by library)
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        sub = payload.get("sub")
        # Enforce idle timeout based on 'iat' claim to handle inactivity
        issued_at = payload.get("iat")
        if issued_at is not None:
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            iat_dt = datetime.fromtimestamp(int(issued_at), tz=timezone.utc)
            idle_limit = timedelta(minutes=settings.session_idle_timeout_minutes)
            if now - iat_dt > idle_limit:
                raise HTTPException(status_code=401, detail="Session expired due to inactivity")
            # Sliding session: refresh token so active users stay logged in
            extra = {}
            tenant = payload.get("tenant")
            if tenant:
                extra["tenant"] = tenant
            new_token = create_access_token(subject=str(sub), expires_delta=idle_limit, extra=extra)
            response.headers["X-Refreshed-Token"] = new_token
        if sub is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return int(sub)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_roles(required: Iterable[str]) -> Callable:
    required_set = set(r.strip() for r in required)

    def dependency(
        db: Session = Depends(get_tenant_db),
        user_id: int = Depends(get_current_user_id),
    ) -> None:
        rows = db.execute(
            text(
                """
                SELECT r.name FROM roles r
                JOIN user_roles ur ON ur.role_id = r.id
                WHERE ur.user_id = :uid
                """
            ),
            {"uid": user_id},
        ).scalars().all()
        if not set(rows).intersection(required_set):
            raise HTTPException(status_code=403, detail="Insufficient role")

    return dependency


def require_permissions(required: Iterable[str]) -> Callable:
    required_set = set(p.strip() for p in required)

    def dependency(
        db: Session = Depends(get_tenant_db),
        user_id: int = Depends(get_current_user_id),
    ) -> None:
        rows = db.execute(
            text(
                """
                SELECT DISTINCT p.name
                FROM permissions p
                JOIN role_permissions rp ON rp.permission_id = p.id
                JOIN user_roles ur ON ur.role_id = rp.role_id
                WHERE ur.user_id = :uid
                """
            ),
            {"uid": user_id},
        ).scalars().all()
        if not set(rows).intersection(required_set):
            raise HTTPException(status_code=403, detail="Insufficient permission")

    return dependency


def require_hq_access(x_hq_key: str | None = Header(default=None, alias="X-HQ-Key")) -> None:
    if not settings.hq_api_key:
        raise HTTPException(status_code=403, detail="HQ access not configured")
    if not x_hq_key or x_hq_key != settings.hq_api_key:
        raise HTTPException(status_code=401, detail="Invalid HQ API key")



