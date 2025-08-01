#!/usr/bin/env python3
"""
Verify the correct password for Supabase
"""
import os
from dotenv import load_dotenv

def verify_password():
    """Help verify the correct password"""
    
    print("🔍 Password Verification Help")
    print("=" * 40)
    print()
    print("The database connection is failing because the password doesn't match.")
    print()
    print("📋 Steps to fix:")
    print("1. Go to Supabase Dashboard")
    print("2. Navigate to Settings > Database")
    print("3. Check the 'Database Password' field")
    print("4. Make sure it matches exactly: S1n1star123456789!")
    print()
    print("🔧 Alternative solutions:")
    print("1. Reset the password in Supabase to something simple (no special chars)")
    print("2. Use the connection string from Supabase Dashboard")
    print("3. Check if there are any extra spaces or characters")
    print()
    print("💡 Quick test - try this password in Supabase:")
    print("   SimplePassword123")
    print()
    print("Then update your .env file with:")
    print("DATABASE_URL=postgresql://postgres.jfluxsyjfcfolvtlpbna:SimplePassword123@aws-0-us-east-1.pooler.supabase.com:5432/postgres")

if __name__ == "__main__":
    verify_password() 