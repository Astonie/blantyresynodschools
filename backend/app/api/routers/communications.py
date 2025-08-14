from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from app.tenancy.deps import get_tenant_db
from app.api.deps import get_current_user_id, require_permissions

router = APIRouter()

# List announcements
@router.get("/announcements", dependencies=[Depends(require_permissions(["communications.read"]))])
def list_announcements(
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id),
    published: Optional[bool] = Query(None),
    search: Optional[str] = Query(None)
):
    query = """
        SELECT a.id, a.title, a.content, a.audience_type, a.audience_value,
               a.is_published, a.scheduled_at, a.published_at,
               a.created_by, u.full_name as created_by_name,
               a.created_at, a.updated_at
        FROM announcements a
        LEFT JOIN users u ON u.id = a.created_by
        WHERE 1=1
    """
    params = {}
    if published is not None:
        query += " AND a.is_published = :published"
        params["published"] = published
    if search:
        query += " AND (LOWER(a.title) LIKE :s OR LOWER(a.content) LIKE :s)"
        params["s"] = f"%{search.lower()}%"
    query += " ORDER BY COALESCE(a.published_at, a.created_at) DESC, a.id DESC"

    rows = db.execute(text(query), params).mappings().all()
    return [dict(r) for r in rows]


# Create announcement
@router.post("/announcements", dependencies=[Depends(require_permissions(["communications.manage", "communications.send"]))])
def create_announcement(
    title: str,
    content: str,
    audience_type: str = "all",  # all | role | class
    audience_value: Optional[str] = None,
    scheduled_at: Optional[str] = None,
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id),
):
    if audience_type not in ("all", "role", "class"):
        raise HTTPException(status_code=400, detail="Invalid audience_type")

    result = db.execute(
        text(
            """
            INSERT INTO announcements(title, content, audience_type, audience_value, scheduled_at, created_by)
            VALUES (:title, :content, :atype, :avalue, :sched, :uid)
            RETURNING id
            """
        ),
        {
            "title": title,
            "content": content,
            "atype": audience_type,
            "avalue": audience_value,
            "sched": scheduled_at,
            "uid": user_id,
        },
    )
    ann_id = result.scalar()
    row = db.execute(
        text(
            """
            SELECT a.id, a.title, a.content, a.audience_type, a.audience_value,
                   a.is_published, a.scheduled_at, a.published_at,
                   a.created_by, u.full_name as created_by_name,
                   a.created_at, a.updated_at
            FROM announcements a
            LEFT JOIN users u ON u.id = a.created_by
            WHERE a.id = :id
            """
        ),
        {"id": ann_id},
    ).mappings().first()
    db.commit()
    return dict(row)


# Get announcement
@router.get("/announcements/{ann_id}", dependencies=[Depends(require_permissions(["communications.read"]))])
def get_announcement(ann_id: int, db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    row = db.execute(
        text(
            """
            SELECT a.id, a.title, a.content, a.audience_type, a.audience_value,
                   a.is_published, a.scheduled_at, a.published_at,
                   a.created_by, u.full_name as created_by_name,
                   a.created_at, a.updated_at
            FROM announcements a
            LEFT JOIN users u ON u.id = a.created_by
            WHERE a.id = :id
            """
        ),
        {"id": ann_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return dict(row)


# Update announcement
@router.put("/announcements/{ann_id}", dependencies=[Depends(require_permissions(["communications.manage", "communications.send"]))])
def update_announcement(
    ann_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    audience_type: Optional[str] = None,
    audience_value: Optional[str] = None,
    scheduled_at: Optional[str] = None,
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id),
):
    update_fields = []
    params = {"id": ann_id}
    if title is not None:
        update_fields.append("title = :title")
        params["title"] = title
    if content is not None:
        update_fields.append("content = :content")
        params["content"] = content
    if audience_type is not None:
        if audience_type not in ("all", "role", "class"):
            raise HTTPException(status_code=400, detail="Invalid audience_type")
        update_fields.append("audience_type = :atype")
        params["atype"] = audience_type
    if audience_value is not None:
        update_fields.append("audience_value = :avalue")
        params["avalue"] = audience_value
    if scheduled_at is not None:
        update_fields.append("scheduled_at = :sched")
        params["sched"] = scheduled_at

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    query = f"UPDATE announcements SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = :id"
    res = db.execute(text(query), params)
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    row = db.execute(
        text(
            """
            SELECT a.id, a.title, a.content, a.audience_type, a.audience_value,
                   a.is_published, a.scheduled_at, a.published_at,
                   a.created_by, u.full_name as created_by_name,
                   a.created_at, a.updated_at
            FROM announcements a
            LEFT JOIN users u ON u.id = a.created_by
            WHERE a.id = :id
            """
        ),
        {"id": ann_id},
    ).mappings().first()
    db.commit()
    return dict(row)


# Publish announcement
@router.post("/announcements/{ann_id}/publish", dependencies=[Depends(require_permissions(["communications.manage", "communications.send"]))])
def publish_announcement(ann_id: int, db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    res = db.execute(
        text("UPDATE announcements SET is_published = TRUE, published_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
        {"id": ann_id},
    )
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    db.commit()
    return {"message": "Announcement published"}


# Delete announcement
@router.delete("/announcements/{ann_id}", dependencies=[Depends(require_permissions(["communications.manage"]))])
def delete_announcement(ann_id: int, db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    res = db.execute(text("DELETE FROM announcements WHERE id = :id"), {"id": ann_id})
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    db.commit()
    return {"message": "Announcement deleted"}
