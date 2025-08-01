#!/usr/bin/env python3
"""
Simple database connection test
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def test_simple_connection():
    """Test database connection with correct password format"""
    
    # Try with the actual password (not URL-encoded)
    password = "S1n1star123456789!"
    username = "postgres.jfluxsyjfcfolvtlpbna"
    host = "aws-0-us-east-1.pooler.supabase.com:5432/postgres"
    
    # Construct the URL manually
    DATABASE_URL = f"postgresql://{username}:{password}@{host}"
    
    print(f"🔗 Testing connection with password: {password}")
    
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
    test_simple_connection() 