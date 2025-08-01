-- Quick Data Counts for Flex Warranty Database
-- Run this in Supabase SQL Editor

SELECT '=== DATA COUNTS ===' as info;

SELECT 
    'shops' as table_name,
    COUNT(*) as record_count
FROM shops
UNION ALL
SELECT 
    'shop_settings' as table_name,
    COUNT(*) as record_count
FROM shop_settings
UNION ALL
SELECT 
    'offers' as table_name,
    COUNT(*) as record_count
FROM offers
UNION ALL
SELECT 
    'offer_themes' as table_name,
    COUNT(*) as record_count
FROM offer_themes
UNION ALL
SELECT 
    'offer_layouts' as table_name,
    COUNT(*) as record_count
FROM offer_layouts
UNION ALL
SELECT 
    'warranty_insurance_products' as table_name,
    COUNT(*) as record_count
FROM warranty_insurance_products
UNION ALL
SELECT 
    'warranty_pricing_bands' as table_name,
    COUNT(*) as record_count
FROM warranty_pricing_bands
ORDER BY table_name;

-- Also show sample data from warranty tables
SELECT '=== WARRANTY INSURANCE PRODUCTS ===' as info;
SELECT 
    id,
    insurer_name,
    product_category,
    includes_adh,
    is_active
FROM warranty_insurance_products
ORDER BY id;

SELECT '=== WARRANTY PRICING BANDS (first 5) ===' as info;
SELECT 
    id,
    insurance_product_id,
    msrp_min,
    msrp_max,
    price_2_year,
    price_3_year
FROM warranty_pricing_bands
ORDER BY id
LIMIT 5; 