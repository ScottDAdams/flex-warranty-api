import pandas as pd
import os
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class PricingService:
    def __init__(self):
        self.pricing_data = {}
        self.load_pricing_data()
    
    def load_pricing_data(self):
        """Load pricing data from the AIG Excel file"""
        try:
            # Path to the Excel file
            excel_path = Path(__file__).parent.parent / 'static' / 'aig_pricing' / 'AIG_ElectronicsPricing.xlsx'
            
            if not excel_path.exists():
                logger.error(f"Pricing file not found: {excel_path}")
                return
            
            # Load each worksheet as a separate pricing table
            self.pricing_data = {
                'consumer_electronics': pd.read_excel(excel_path, sheet_name='Consumer Electronics (includes ADH)'),
                'desktops_laptops': pd.read_excel(excel_path, sheet_name='Desktops, Laptops (includes ADH)'),
                'tablets': pd.read_excel(excel_path, sheet_name='Tablets (includes ADH)'),
                'tvs': pd.read_excel(excel_path, sheet_name='TVs (does not include ADH)')
            }
            
            # Clean and process each pricing table
            for category, df in self.pricing_data.items():
                self.pricing_data[category] = self._process_pricing_table(df, category)
                
            logger.info("Pricing data loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading pricing data: {str(e)}")
    
    def _process_pricing_table(self, df: pd.DataFrame, category: str) -> pd.DataFrame:
        """Process and clean a pricing table"""
        try:
            # Remove any empty rows and clean column names
            df = df.dropna(subset=['MSRP Band']).copy()
            
            # Extract MSRP range from the band column
            df['min_msrp'] = df['MSRP Band'].apply(self._extract_min_msrp)
            df['max_msrp'] = df['MSRP Band'].apply(self._extract_max_msrp)
            
            # Ensure price columns are numeric
            price_columns = ['2-year Price', '3-year Price']
            for col in price_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Add category info
            df['category'] = category
            
            return df
            
        except Exception as e:
            logger.error(f"Error processing pricing table for {category}: {str(e)}")
            return pd.DataFrame()
    
    def _extract_min_msrp(self, band_str: str) -> float:
        """Extract minimum MSRP from band string like '$50–$99.99'"""
        try:
            if pd.isna(band_str):
                return 0.0
            
            # Remove currency symbols and split by dash
            clean_str = str(band_str).replace('$', '').replace(',', '')
            parts = clean_str.split('–')
            
            if len(parts) >= 1:
                return float(parts[0].strip())
            return 0.0
            
        except Exception as e:
            logger.error(f"Error extracting min MSRP from '{band_str}': {str(e)}")
            return 0.0
    
    def _extract_max_msrp(self, band_str: str) -> float:
        """Extract maximum MSRP from band string like '$50–$99.99'"""
        try:
            if pd.isna(band_str):
                return float('inf')
            
            # Remove currency symbols and split by dash
            clean_str = str(band_str).replace('$', '').replace(',', '')
            parts = clean_str.split('–')
            
            if len(parts) >= 2:
                return float(parts[1].strip())
            return float('inf')
            
        except Exception as e:
            logger.error(f"Error extracting max MSRP from '{band_str}': {str(e)}")
            return float('inf')
    
    def get_product_category(self, product_info: Dict) -> str:
        """Determine product category based on product information"""
        try:
            title = product_info.get('title', '').lower()
            vendor = product_info.get('vendor', '').lower()
            product_type = product_info.get('product_type', '').lower()
            
            # Check for TV indicators
            tv_keywords = ['tv', 'television', 'smart tv', 'led tv', 'oled tv', '4k tv', '8k tv']
            if any(keyword in title for keyword in tv_keywords):
                return 'tvs'
            
            # Check for tablet indicators
            tablet_keywords = ['tablet', 'ipad', 'android tablet', 'surface']
            if any(keyword in title for keyword in tablet_keywords):
                return 'tablets'
            
            # Check for laptop/desktop indicators
            computer_keywords = ['laptop', 'notebook', 'desktop', 'computer', 'pc', 'macbook', 'imac', 'mac pro']
            if any(keyword in title for keyword in computer_keywords):
                return 'desktops_laptops'
            
            # Default to consumer electronics
            return 'consumer_electronics'
            
        except Exception as e:
            logger.error(f"Error determining product category: {str(e)}")
            return 'consumer_electronics'
    
    def get_warranty_pricing(self, product_info: Dict, term_years: int = 2) -> Optional[Dict]:
        """Get warranty pricing for a product based on its category and MSRP"""
        try:
            msrp = float(product_info.get('price', 0))
            category = self.get_product_category(product_info)
            
            if category not in self.pricing_data:
                logger.error(f"Unknown product category: {category}")
                return None
            
            pricing_table = self.pricing_data[category]
            
            # Find the appropriate pricing band
            matching_row = pricing_table[
                (pricing_table['min_msrp'] <= msrp) & 
                (pricing_table['max_msrp'] > msrp)
            ]
            
            if matching_row.empty:
                logger.warning(f"No pricing band found for MSRP ${msrp} in category {category}")
                return None
            
            row = matching_row.iloc[0]
            
            # Get the price for the specified term
            price_column = f'{term_years}-year Price'
            if price_column not in row:
                logger.error(f"Price column '{price_column}' not found")
                return None
            
            warranty_price = row[price_column]
            
            if pd.isna(warranty_price):
                logger.error(f"No price found for {term_years}-year warranty")
                return None
            
            return {
                'warranty_price': float(warranty_price),
                'category': category,
                'msrp_band': row['MSRP Band'],
                'term_years': term_years,
                'includes_adh': 'ADH' in row.get('category', ''),
                'product_msrp': msrp
            }
            
        except Exception as e:
            logger.error(f"Error getting warranty pricing: {str(e)}")
            return None
    
    def get_available_terms(self, product_info: Dict) -> Dict:
        """Get available warranty terms and pricing for a product"""
        try:
            result = {}
            
            # Check for 2-year and 3-year options
            for term in [2, 3]:
                pricing = self.get_warranty_pricing(product_info, term)
                if pricing:
                    result[f'{term}_year'] = pricing
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting available terms: {str(e)}")
            return {}
    
    def validate_pricing_data(self) -> bool:
        """Validate that pricing data is loaded correctly"""
        try:
            if not self.pricing_data:
                logger.error("No pricing data loaded")
                return False
            
            for category, df in self.pricing_data.items():
                if df.empty:
                    logger.error(f"Empty pricing data for category: {category}")
                    return False
                
                required_columns = ['MSRP Band', '2-year Price', '3-year Price']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    logger.error(f"Missing required columns in {category}: {missing_columns}")
                    return False
            
            logger.info("Pricing data validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating pricing data: {str(e)}")
            return False

# Global pricing service instance
pricing_service = PricingService() 