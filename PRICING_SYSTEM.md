# Flex Warranty Pricing System

## Overview

The Flex Warranty pricing system is designed to handle multiple insurance providers and product categories with time-stamped pricing bands. The system supports AIG pricing models and is built to scale for additional insurers in the future.

## Database Schema

### Tables

#### `warranty_insurance_products`
Stores insurance product definitions:
- `insurer_name`: Insurance provider (e.g., 'AIG', 'SquareTrade')
- `product_category`: Product category (e.g., 'Consumer Electronics', 'Desktops, Laptops')
- `includes_adh`: Whether the plan includes Accidental Damage from Handling
- `is_active`: Whether the product is currently active

#### `warranty_pricing_bands`
Stores pricing bands with time-stamped versions:
- `insurance_product_id`: Reference to warranty_insurance_products
- `msrp_min/max`: Price range for the band
- `price_2_year/3_year`: Pricing for different warranty terms
- `effective_date`: When this pricing became active
- `expiry_date`: When this pricing expires (NULL = currently active)

## AIG Pricing Categories

The system supports four AIG product categories:

1. **Consumer Electronics (includes ADH)**
   - Phones, cameras, headphones, speakers, gaming devices
   - Includes accidental damage coverage

2. **Desktops, Laptops (includes ADH)**
   - Desktop computers, laptops, computer accessories
   - Includes accidental damage coverage

3. **Tablets (includes ADH)**
   - iPads, Android tablets, tablet accessories
   - Includes accidental damage coverage

4. **TVs (does not include ADH)**
   - Televisions, monitors
   - Does NOT include accidental damage coverage

## Setup Instructions

### 1. Create Database Tables

Run the pricing schema in your Supabase SQL editor:

```sql
-- Run database_schema_pricing.sql
```

### 2. Install Dependencies

```bash
pip install pandas openpyxl
```

### 3. Place Excel File

Place the `AIG_ElectronicsPricing.xlsx` file in:
```
flex-warranty-api/app/static/aig_pricing/AIG_ElectronicsPricing.xlsx
```

### 4. Ingest Pricing Data

Run the ingestion script:

```bash
cd flex-warranty-api
python ingest_aig_pricing.py
```

This will:
- Read all four sheets from the Excel file
- Parse MSRP bands and pricing
- Deactivate old pricing bands
- Insert new pricing bands with current timestamps

## API Usage

### Pricing Endpoint

`POST /api/pricing`

**Request:**
```json
{
  "session_token": "session_abc123",
  "product_id": "12345",
  "product_price": 299.99,
  "product_category": "Consumer Electronics",
  "warranty_term": 2
}
```

**Response:**
```json
{
  "warranty_price": 29.99,
  "session_token": "session_abc123",
  "variant_id": "67890",
  "product_category": "Consumer Electronics",
  "warranty_term": 2,
  "includes_adh": true
}
```

### Product Category Detection

The embed script automatically detects product categories based on keywords:

- **Desktops, Laptops**: laptop, desktop, computer
- **Tablets**: tablet, ipad
- **TVs**: tv, television
- **Consumer Electronics**: monitor, phone, smartphone, camera, headphones, speaker, gaming

## Pricing Logic

1. **Category Detection**: Product title/vendor is analyzed for keywords
2. **Price Band Lookup**: Product price is matched to appropriate MSRP band
3. **Term Selection**: 2-year or 3-year pricing is selected
4. **ADH Coverage**: System indicates whether accidental damage is included

## Future Enhancements

### Multiple Insurers
The system is designed to support multiple insurance providers:

```sql
-- Add new insurer
INSERT INTO warranty_insurance_products (insurer_name, product_category, includes_adh) 
VALUES ('SquareTrade', 'Consumer Electronics', true);
```

### Pricing Updates
To update pricing:

1. Update the Excel file with new pricing
2. Run the ingestion script
3. Old pricing is automatically deactivated
4. New pricing becomes effective immediately

### Environment Configuration
Set the active insurer via environment variable:

```bash
export ACTIVE_INSURER=AIG
```

## Troubleshooting

### Common Issues

1. **No pricing found**: Check that the product price falls within a defined MSRP band
2. **Category not found**: Verify the product category exists in `warranty_insurance_products`
3. **Excel parsing errors**: Ensure the Excel file format matches the expected structure

### Debug Logs

The ingestion script provides detailed logging:
- Shows which sheets are being processed
- Reports parsing errors for MSRP bands
- Indicates successful insertions and deactivations

## Security Considerations

- Pricing data is read-only for API consumers
- Only authorized users can update pricing bands
- Session tokens prevent pricing manipulation
- All pricing changes are timestamped for audit trails 