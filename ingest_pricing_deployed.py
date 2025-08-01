#!/usr/bin/env python3
"""
Script to ingest AIG pricing data on the deployed API
"""
import requests
import json
import os
from pathlib import Path

def ingest_pricing_on_deployed():
    """Ingest AIG pricing data on the deployed API"""
    
    print("📊 Starting AIG pricing ingestion on deployed API...")
    
    # First, let's check if the API is accessible
    try:
        response = requests.get("https://flex-warranty-api.fly.dev/health", timeout=10)
        print(f"✅ API is accessible: {response.status_code}")
    except Exception as e:
        print(f"❌ Error connecting to deployed API: {e}")
        return
    
    # Check if the Excel file exists locally
    excel_file_path = Path("app/static/aig_pricing/AIG_ElectronicsPricing.xlsx")
    
    if not excel_file_path.exists():
        print(f"❌ Excel file not found: {excel_file_path}")
        print("   Please ensure the AIG_ElectronicsPricing.xlsx file is in app/static/aig_pricing/")
        return
    
    print(f"✅ Excel file found: {excel_file_path}")
    print("📁 File size:", excel_file_path.stat().st_size, "bytes")
    
    # We need to create an endpoint for this
    print("\n⚠️  Need to create an ingestion endpoint on the deployed API")
    print("   For now, you can:")
    print("   1. Run the ingestion locally with proper DATABASE_URL")
    print("   2. Create an API endpoint for ingestion")
    print("   3. Manually insert the pricing data via SQL")
    
    print("\n🎯 Next Steps:")
    print("   1. Fix the DATABASE_URL encoding issue")
    print("   2. Run: python3 ingest_aig_pricing.py")
    print("   3. Or create an API endpoint for ingestion")

if __name__ == "__main__":
    ingest_pricing_on_deployed() 