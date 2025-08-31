#!/usr/bin/env python3
"""
Check the actual structure of the users table
"""
import sys
sys.path.append('/app')

from app.db.session import SessionLocal
from sqlalchemy import text

def check_users_table():
    print('🔍 CHECKING USERS TABLE STRUCTURE')
    print('=' * 40)
    
    db = SessionLocal()
    try:
        # Use ndirande_high as test schema
        db.execute(text('SET search_path TO "ndirande_high"'))
        
        print('\n📋 Users table columns:')
        columns = db.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)).fetchall()
        
        for col_name, data_type, nullable in columns:
            print(f'   {col_name}: {data_type} {"NULL" if nullable == "YES" else "NOT NULL"}')
        
        print('\n📊 Sample data:')
        users = db.execute(text('SELECT * FROM users LIMIT 3')).mappings().all()
        for i, user in enumerate(users, 1):
            print(f'   User {i}: {dict(user)}')
            
    finally:
        db.close()

if __name__ == "__main__":
    check_users_table()
