#!/usr/bin/env python3
"""
Check table structure
"""
import sys
sys.path.append('/app')

from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    db.execute(text('SET search_path TO "ndirande_high"'))
    columns = db.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'permissions' 
        ORDER BY ordinal_position
    """)).fetchall()
    
    print('Permissions table structure:')
    for col in columns:
        print(f'  {col.column_name}: {col.data_type}')
finally:
    db.close()
