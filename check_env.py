#!/usr/bin/env python3
"""
Check .env file format
"""
import os
from dotenv import load_dotenv

def check_env():
    """Check .env file format"""
    load_dotenv()
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in .env file")
        return
    
    print("🔍 Checking DATABASE_URL format:")
    print(f"URL: {DATABASE_URL}")
    
    # Parse the URL to check format
    if DATABASE_URL.startswith('postgresql://'):
        parts = DATABASE_URL.replace('postgresql://', '').split('@')
        if len(parts) == 2:
            auth_part = parts[0]
            host_part = parts[1]
            
            if ':' in auth_part:
                username, password = auth_part.split(':', 1)
                print(f"Username: {username}")
                print(f"Password: {password}")
                print(f"Host: {host_part}")
                
                # Check for special characters in password
                special_chars = ['@', ':', '/', '\\', '!', '#', '$', '%', '^', '&', '*', '(', ')', '+', '=', '{', '}', '[', ']', '|', ';', '"', "'", ',', '.', '<', '>', '?']
                found_chars = [char for char in password if char in special_chars]
                
                if found_chars:
                    print(f"⚠️  Special characters found in password: {found_chars}")
                    print("   These might need URL encoding")
                else:
                    print("✅ No special characters in password")
            else:
                print("❌ Invalid DATABASE_URL format - missing password")
        else:
            print("❌ Invalid DATABASE_URL format")
    else:
        print("❌ DATABASE_URL should start with 'postgresql://'")

if __name__ == "__main__":
    check_env() 