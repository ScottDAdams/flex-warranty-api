#!/usr/bin/env python3
"""
Test database connection with new simple password
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def test_new_password():
    """Test database connection with new simple password"""
    
    # Load environment variables
    load_dotenv()
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in .env file")
        return False
    
    print(f"🔗 Testing connection with new password...")
    print(f"URL: {DATABASE_URL[:50]}...")
    
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
            
            # Test if warranty_pricing_bands table exists
            result = conn.execute(text("SELECT COUNT(*) FROM warranty_pricing_bands"))
            count = result.fetchone()[0]
            print(f"📊 Found {count} warranty pricing bands")
            
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_new_password() 