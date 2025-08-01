#!/usr/bin/env python3
"""
Fix DATABASE_URL encoding
"""
import os
import urllib.parse
from dotenv import load_dotenv

def fix_url_encoding():
    """Fix DATABASE_URL encoding"""
    load_dotenv()
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in .env file")
        return
    
    print("🔧 Fixing DATABASE_URL encoding...")
    print(f"Original URL: {DATABASE_URL}")
    
    # Parse the URL
    if DATABASE_URL.startswith('postgresql://'):
        parts = DATABASE_URL.replace('postgresql://', '').split('@')
        if len(parts) == 2:
            auth_part = parts[0]
            host_part = parts[1]
            
            if ':' in auth_part:
                username, password = auth_part.split(':', 1)
                
                # URL encode the password
                encoded_password = urllib.parse.quote(password)
                
                # Reconstruct the URL
                fixed_url = f"postgresql://{username}:{encoded_password}@{host_part}"
                
                print(f"Fixed URL: {fixed_url}")
                print()
                print("📋 Copy this to your .env file:")
                print(f"DATABASE_URL={fixed_url}")
                
                return fixed_url
            else:
                print("❌ Invalid DATABASE_URL format - missing password")
        else:
            print("❌ Invalid DATABASE_URL format")
    else:
        print("❌ DATABASE_URL should start with 'postgresql://'")

if __name__ == "__main__":
    fix_url_encoding() 