#!/usr/bin/env python3
"""
Database migration script to add missing columns to production database
Run this script to update the database schema
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

def migrate_database():
    """Add missing columns to the Click table"""
    
    # Get database URL from environment
    database_url = os.environ.get("DATABASE_URL", "sqlite:///smartlink.db")
    
    # Fix Railway/Heroku postgres URL format
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    print(f"Connecting to database...")
    engine = create_engine(database_url)
    
    # List of migrations to run
    migrations = [
        # Add confidence_score column
        {
            "name": "Add confidence_score to Click table",
            "check": "SELECT column_name FROM information_schema.columns WHERE table_name='click' AND column_name='confidence_score'",
            "migrate": "ALTER TABLE click ADD COLUMN confidence_score FLOAT",
            "sqlite_check": "PRAGMA table_info(click)",
            "sqlite_migrate": "ALTER TABLE click ADD COLUMN confidence_score REAL"
        },
        # Add risk_level column
        {
            "name": "Add risk_level to Click table",
            "check": "SELECT column_name FROM information_schema.columns WHERE table_name='click' AND column_name='risk_level'",
            "migrate": "ALTER TABLE click ADD COLUMN risk_level VARCHAR(10)",
            "sqlite_check": "PRAGMA table_info(click)",
            "sqlite_migrate": "ALTER TABLE click ADD COLUMN risk_level TEXT"
        },
        # Add detection_methods column
        {
            "name": "Add detection_methods to Click table",
            "check": "SELECT column_name FROM information_schema.columns WHERE table_name='click' AND column_name='detection_methods'",
            "migrate": "ALTER TABLE click ADD COLUMN detection_methods TEXT",
            "sqlite_check": "PRAGMA table_info(click)",
            "sqlite_migrate": "ALTER TABLE click ADD COLUMN detection_methods TEXT"
        }
    ]
    
    with engine.connect() as conn:
        # Determine if we're using SQLite or PostgreSQL
        is_sqlite = database_url.startswith("sqlite")
        
        for migration in migrations:
            try:
                print(f"\nChecking: {migration['name']}...")
                
                if is_sqlite:
                    # SQLite approach
                    result = conn.execute(text(migration['sqlite_check']))
                    columns = [row[1] for row in result]
                    column_name = migration['migrate'].split()[-2]
                    
                    if column_name in columns:
                        print(f"  ✓ Column already exists, skipping")
                        continue
                else:
                    # PostgreSQL approach
                    result = conn.execute(text(migration['check']))
                    if result.rowcount > 0:
                        print(f"  ✓ Column already exists, skipping")
                        continue
                
                # Run migration
                print(f"  → Running migration...")
                if is_sqlite:
                    conn.execute(text(migration['sqlite_migrate']))
                else:
                    conn.execute(text(migration['migrate']))
                conn.commit()
                print(f"  ✓ Migration completed successfully")
                
            except (OperationalError, ProgrammingError) as e:
                if "already exists" in str(e).lower():
                    print(f"  ✓ Column already exists, skipping")
                else:
                    print(f"  ✗ Migration failed: {e}")
                    conn.rollback()
                    continue
    
    print("\n✨ Database migration completed!")

if __name__ == "__main__":
    try:
        migrate_database()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)