#!/usr/bin/env python3
"""
Script to run AIG pricing ingestion on the deployed API
"""
import requests
import json
import os
from pathlib import Path

def run_ingestion_on_deployed():
    """Run the AIG pricing ingestion on the deployed API"""
    
    # API endpoint (we'll need to create this)
    api_url = "https://flex-warranty-api.fly.dev/api/ingest-aig-pricing"
    
    # Check if the Excel file exists
    excel_file_path = Path("app/static/aig_pricing/AIG_ElectronicsPricing.xlsx")
    
    if not excel_file_path.exists():
        print(f"❌ Excel file not found: {excel_file_path}")
        return
    
    print("📊 Starting AIG pricing ingestion on deployed API...")
    
    try:
        # For now, let's just check if the API is accessible
        response = requests.get("https://flex-warranty-api.fly.dev/health", timeout=10)
        print(f"✅ API is accessible: {response.status_code}")
        
        # We need to create an endpoint for this
        print("⚠️  Need to create an ingestion endpoint on the deployed API")
        print("   For now, the pricing data should already be in the database from previous runs")
        
    except Exception as e:
        print(f"❌ Error connecting to deployed API: {e}")

if __name__ == "__main__":
    run_ingestion_on_deployed() 