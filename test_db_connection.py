#!/usr/bin/env python3
"""
Test database connection
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

def test_connection():
    """Test database connection"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in .env file")
        return
    
    print(f"🔗 Testing connection with URL: {DATABASE_URL[:50]}...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            print("✅ Database connection successful!")
            
            # Test if warranty_insurance_products table exists
            result = conn.execute(text("SELECT COUNT(*) FROM warranty_insurance_products"))
            count = result.fetchone()[0]
            print(f"📊 Found {count} warranty insurance products")
            
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection() 