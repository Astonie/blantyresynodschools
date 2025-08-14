from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class LibraryResourceCreate(BaseModel):
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    category: Optional[str] = None
    subject_id: Optional[int] = None
    class_id: Optional[int] = None
    tags: Optional[List[str]] = None

class LibraryResourceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    category: Optional[str] = None
    subject_id: Optional[int] = None
    class_id: Optional[int] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

class LibraryResourceRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    category: Optional[str] = None
    subject_id: Optional[int] = None
    class_id: Optional[int] = None
    subject_name: Optional[str] = None
    class_name: Optional[str] = None
    file_path: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    upload_date: datetime
    uploaded_by: Optional[int] = None
    uploader_name: Optional[str] = None
    is_active: bool
    download_count: int
    tags: Optional[List[str]] = None

class LibraryResourceSearch(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    subject_id: Optional[int] = None
    class_id: Optional[int] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None

class LibraryStats(BaseModel):
    total_resources: int
    total_downloads: int
    resources_by_category: dict
    resources_by_subject: dict
    recent_uploads: List[LibraryResourceRead]
