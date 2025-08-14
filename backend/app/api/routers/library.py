from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.tenancy.deps import get_tenant_db
from app.api.deps import get_current_user_id, require_permissions

router = APIRouter()

@router.get("/resources", dependencies=[Depends(require_permissions(["library.read"]))])
def list_resources(db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    """List library resources."""
    try:
        # Check if library_resources table exists
        result = db.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = current_schema() 
            AND table_name = 'library_resources'
        """)).scalar()
        
        if result == 0:
            return {"message": "Library table not found", "resources": []}
        
        # Get resources
        rows = db.execute(text("""
            SELECT id, title, description, author, category, file_size, 
                   upload_date, download_count
            FROM library_resources 
            WHERE is_active = true 
            ORDER BY upload_date DESC
        """)).mappings().all()
        
        return [dict(row) for row in rows]
    except Exception as e:
        return {"message": f"Error: {str(e)}", "resources": []}

@router.get("/categories", dependencies=[Depends(require_permissions(["library.read"]))])
def get_categories(db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    """Get all available resource categories."""
    try:
        rows = db.execute(text("""
            SELECT DISTINCT category FROM library_resources 
            WHERE category IS NOT NULL AND is_active = true 
            ORDER BY category
        """)).fetchall()
        
        return [row[0] for row in rows]
    except Exception as e:
        return []

@router.get("/stats", dependencies=[Depends(require_permissions(["library.read"]))])
def get_library_stats(db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    """Get library statistics."""
    try:
        total_resources = db.execute(text("""
            SELECT COUNT(*) FROM library_resources WHERE is_active = true
        """)).scalar() or 0
        
        total_downloads = db.execute(text("""
            SELECT COALESCE(SUM(download_count), 0) FROM library_resources WHERE is_active = true
        """)).scalar() or 0
        
        return {
            "total_resources": total_resources,
            "total_downloads": total_downloads,
            "resources_by_category": {},
            "resources_by_subject": {},
            "recent_uploads": []
        }
    except Exception as e:
        return {
            "total_resources": 0,
            "total_downloads": 0,
            "resources_by_category": {},
            "resources_by_subject": {},
            "recent_uploads": []
        }
