#!/usr/bin/env python3
"""
Migration script to add missing columns to shops table
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

def migrate_schema():
    """Add missing columns to shops table"""
    try:
        # Connect to database
        engine = create_engine(os.getenv('DATABASE_URL'))
        print("Connected to database successfully")
        
        with engine.connect() as conn:
            # Add missing columns
            print("Adding product_id column...")
            conn.execute(text("ALTER TABLE shops ADD COLUMN IF NOT EXISTS product_id VARCHAR(255)"))
            
            print("Adding variant_id column...")
            conn.execute(text("ALTER TABLE shops ADD COLUMN IF NOT EXISTS variant_id VARCHAR(255)"))
            
            print("Adding collection_id column...")
            conn.execute(text("ALTER TABLE shops ADD COLUMN IF NOT EXISTS collection_id VARCHAR(255)"))
            
            # Commit changes
            conn.commit()
            print("Database schema updated successfully!")
            
            # Verify the columns exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'shops' 
                AND column_name IN ('product_id', 'variant_id', 'collection_id')
                ORDER BY column_name
            """))
            
            columns = [row[0] for row in result.fetchall()]
            print(f"Verified columns: {columns}")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
 