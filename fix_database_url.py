#!/usr/bin/env python3
"""
Script to fix DATABASE_URL encoding issue
"""
import urllib.parse
import os

def fix_database_url():
    """Fix the DATABASE_URL encoding issue"""
    
    # Get the current DATABASE_URL from Fly.io
    print("🔧 Fixing DATABASE_URL encoding issue...")
    
    # The issue is with special characters in the password
    # We need to URL-encode the password part
    
    # Example of what the URL might look like:
    # postgresql://postgres:r123!@aws-0-us-east-1.pooler.supabase.com:5432/postgres
    
    print("\n📋 Steps to fix:")
    print("1. Get your DATABASE_URL from Fly.io:")
    print("   fly secrets list -a flex-warranty-api")
    print()
    print("2. The password contains special characters that need URL encoding:")
    print("   - '!' becomes '%21'")
    print("   - '@' becomes '%40'")
    print()
    print("3. Update the secret with URL-encoded password:")
    print("   fly secrets set DATABASE_URL='postgresql://postgres:r123%21%40aws-0-us-east-1.pooler.supabase.com:5432/postgres' -a flex-warranty-api")
    print()
    print("4. Then run the ingestion:")
    print("   python3 ingest_aig_pricing.py")
    
    print("\n🎯 Alternative: Create a .env file locally with the correct URL")

if __name__ == "__main__":
    fix_database_url() 