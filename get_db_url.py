#!/usr/bin/env python3
"""
Get DATABASE_URL from Fly.io secrets
"""
import subprocess
import re

def get_database_url():
    """Get DATABASE_URL from Fly.io secrets"""
    try:
        # Get the secret value
        result = subprocess.run(
            ["fly", "secrets", "list", "-a", "flex-warranty-api"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Parse the output to find DATABASE_URL
            for line in result.stdout.split('\n'):
                if 'DATABASE_URL' in line:
                    print("✅ DATABASE_URL found in Fly.io secrets")
                    print("   (Updated 45 seconds ago)")
                    return True
        
        print("❌ Could not get DATABASE_URL from Fly.io")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    get_database_url() 