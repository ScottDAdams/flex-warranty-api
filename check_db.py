#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.models.database import Session, Shop, Offer, OfferTheme, OfferLayout, ShopSettings, WarrantyInsuranceProduct, WarrantyPricingBand

def check_database():
    """Check the current state of the database"""
    session = Session()
    
    try:
        print("=== FLEX WARRANTY DATABASE STATUS ===")
        print(f"Shops: {session.query(Shop).count()}")
        print(f"Offers: {session.query(Offer).count()}")
        print(f"Themes: {session.query(OfferTheme).count()}")
        print(f"Layouts: {session.query(OfferLayout).count()}")
        print(f"Shop Settings: {session.query(ShopSettings).count()}")
        print(f"Warranty Insurance Products: {session.query(WarrantyInsuranceProduct).count()}")
        print(f"Warranty Pricing Bands: {session.query(WarrantyPricingBand).count()}")
        
        print("\n=== SAMPLE DATA ===")
        
        # Check shops
        shops = session.query(Shop).all()
        if shops:
            print(f"Shops found: {len(shops)}")
            for shop in shops:
                print(f"  - {shop.shop_url} (API Key: {shop.api_key[:20] if shop.api_key else 'None'}...)")
        else:
            print("No shops found")
            
        # Check themes
        themes = session.query(OfferTheme).all()
        if themes:
            print(f"Themes found: {len(themes)}")
            for theme in themes[:3]:  # Show first 3
                print(f"  - {theme.name} (Shop ID: {theme.shop_id})")
        else:
            print("No themes found")
            
        # Check layouts
        layouts = session.query(OfferLayout).all()
        if layouts:
            print(f"Layouts found: {len(layouts)}")
            for layout in layouts[:3]:  # Show first 3
                print(f"  - {layout.name} (Shop ID: {layout.shop_id})")
        else:
            print("No layouts found")
            
        # Check warranty products
        warranty_products = session.query(WarrantyInsuranceProduct).all()
        if warranty_products:
            print(f"Warranty Insurance Products found: {len(warranty_products)}")
            for product in warranty_products:
                print(f"  - {product.insurer_name} - {product.product_category} (ADH: {product.includes_adh})")
        else:
            print("No warranty insurance products found")
            
        # Check pricing bands
        pricing_bands = session.query(WarrantyPricingBand).all()
        if pricing_bands:
            print(f"Warranty Pricing Bands found: {len(pricing_bands)}")
            for band in pricing_bands[:5]:  # Show first 5
                print(f"  - ${band.msrp_min}-${band.msrp_max}: 2yr=${band.price_2_year}, 3yr=${band.price_3_year}")
        else:
            print("No warranty pricing bands found")
            
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_database() 