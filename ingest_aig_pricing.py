#!/usr/bin/env python3
"""
AIG Pricing Data Ingestion Script
Reads the AIG_ElectronicsPricing.xlsx file and ingests pricing data into the database.
"""

import pandas as pd
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable not set")
    sys.exit(1)

# Excel file path
EXCEL_FILE = "app/static/aig_pricing/AIG_ElectronicsPricing.xlsx"

def connect_to_database():
    """Create database connection"""
    try:
        engine = create_engine(DATABASE_URL)
        return engine
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def get_insurance_product_id(engine, insurer_name, product_category):
    """Get insurance product ID from database"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id FROM warranty_insurance_products 
                    WHERE insurer_name = :insurer_name 
                    AND product_category = :product_category
                    AND is_active = true
                """),
                {"insurer_name": insurer_name, "product_category": product_category}
            ).fetchone()
            
            if result:
                return result[0]
            else:
                print(f"Warning: No active insurance product found for {insurer_name} - {product_category}")
                return None
    except Exception as e:
        print(f"Error getting insurance product ID: {e}")
        return None

def deactivate_old_pricing(engine, insurance_product_id):
    """Deactivate old pricing bands for the given insurance product"""
    try:
        with engine.connect() as conn:
            conn.execute(
                text("""
                    UPDATE warranty_pricing_bands 
                    SET expiry_date = now() 
                    WHERE insurance_product_id = :product_id 
                    AND expiry_date IS NULL
                """),
                {"product_id": insurance_product_id}
            )
            conn.commit()
            print(f"Deactivated old pricing bands for insurance product {insurance_product_id}")
    except Exception as e:
        print(f"Error deactivating old pricing: {e}")

def insert_pricing_bands(engine, insurance_product_id, pricing_data):
    """Insert new pricing bands into database"""
    try:
        with engine.connect() as conn:
            for _, row in pricing_data.iterrows():
                # Get values from unnamed columns
                msrp_band = str(row.iloc[0])  # First column is MSRP Band
                price_2_year = row.iloc[3]    # Fourth column is 2-year price
                price_3_year = row.iloc[5]    # Sixth column is 3-year price
                
                # Skip if MSRP band is not valid
                if pd.isna(msrp_band) or msrp_band == 'nan' or 'MSRP Band' in msrp_band:
                    continue
                
                # Parse MSRP band
                msrp_min, msrp_max = parse_msrp_band(msrp_band)
                
                if msrp_min is None or msrp_max is None:
                    print(f"Warning: Could not parse MSRP band: {msrp_band}")
                    continue
                
                # Skip if prices are not valid
                if pd.isna(price_2_year) or pd.isna(price_3_year):
                    print(f"Warning: Invalid prices for band {msrp_band}")
                    continue
                
                # Insert pricing band
                conn.execute(
                    text("""
                        INSERT INTO warranty_pricing_bands 
                        (insurance_product_id, msrp_min, msrp_max, price_2_year, price_3_year, effective_date)
                        VALUES (:product_id, :msrp_min, :msrp_max, :price_2_year, :price_3_year, now())
                    """),
                    {
                        "product_id": insurance_product_id,
                        "msrp_min": msrp_min,
                        "msrp_max": msrp_max,
                        "price_2_year": float(price_2_year),
                        "price_3_year": float(price_3_year)
                    }
                )
            
            conn.commit()
            print(f"Inserted pricing bands for insurance product {insurance_product_id}")
    except Exception as e:
        print(f"Error inserting pricing bands: {e}")

def parse_msrp_band(msrp_band):
    """Parse MSRP band string to extract min and max values"""
    try:
        # Remove currency symbols and spaces
        msrp_band = msrp_band.replace('$', '').replace(',', '').strip()
        
        # Handle different separators
        if '–' in msrp_band:  # en dash
            parts = msrp_band.split('–')
        elif '-' in msrp_band:  # hyphen
            parts = msrp_band.split('-')
        elif 'to' in msrp_band.lower():
            parts = msrp_band.lower().split('to')
        else:
            print(f"Warning: Unknown MSRP band format: {msrp_band}")
            return None, None
        
        if len(parts) != 2:
            print(f"Warning: Invalid MSRP band format: {msrp_band}")
            return None, None
        
        min_val = float(parts[0].strip())
        max_val = float(parts[1].strip())
        
        return min_val, max_val
    except Exception as e:
        print(f"Error parsing MSRP band '{msrp_band}': {e}")
        return None, None

def process_excel_sheet(engine, sheet_name, insurer_name, product_category):
    """Process a single Excel sheet and ingest its pricing data"""
    print(f"\nProcessing sheet: {sheet_name}")
    
    try:
        # Read Excel sheet starting from row 3 (index 2) where the actual data begins
        df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, header=2)
        print(f"Found {len(df)} rows in {sheet_name}")
        
        # Get insurance product ID
        insurance_product_id = get_insurance_product_id(engine, insurer_name, product_category)
        if not insurance_product_id:
            print(f"Skipping {sheet_name} - no insurance product found")
            return
        
        # Deactivate old pricing
        deactivate_old_pricing(engine, insurance_product_id)
        
        # Insert new pricing bands
        insert_pricing_bands(engine, insurance_product_id, df)
        
    except Exception as e:
        print(f"Error processing sheet {sheet_name}: {e}")

def main():
    """Main ingestion function"""
    print("Starting AIG pricing data ingestion...")
    
    # Check if Excel file exists
    if not os.path.exists(EXCEL_FILE):
        print(f"Error: Excel file not found at {EXCEL_FILE}")
        sys.exit(1)
    
    # Connect to database
    engine = connect_to_database()
    print("Connected to database successfully")
    
    # Define sheet mappings - updated to match actual sheet names
    sheet_mappings = [
        ("Consumer Electronics", "AIG", "Consumer Electronics"),
        ("Desktops, Laptops", "AIG", "Desktops, Laptops"),
        ("Tablets", "AIG", "Tablets"),
        ("TVs", "AIG", "TVs")
    ]
    
    # Process each sheet
    for sheet_name, insurer_name, product_category in sheet_mappings:
        try:
            process_excel_sheet(engine, sheet_name, insurer_name, product_category)
        except Exception as e:
            print(f"Error processing {sheet_name}: {e}")
    
    print("\nAIG pricing data ingestion completed!")

if __name__ == "__main__":
    main() 