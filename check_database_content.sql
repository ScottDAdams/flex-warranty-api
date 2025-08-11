-- Flex Warranty Database Content Check
-- Run this in Supabase SQL Editor to see the complete database state

-- ========================================
-- 1. DATABASE STRUCTURE
-- ========================================

-- Show all tables
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Show table schemas
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
ORDER BY table_name, ordinal_position;

-- ========================================
-- 2. TABLE CONTENTS
-- ========================================

-- Shops table
SELECT '=== SHOPS TABLE ===' as info;
SELECT 
    id,
    shop_url,
    CASE 
        WHEN api_key IS NOT NULL THEN CONCAT(LEFT(api_key, 10), '...')
        ELSE 'NULL'
    END as api_key_preview,
    product_id,
    variant_id,
    collection_id,
    created_at,
    updated_at
FROM shops
ORDER BY id;

-- Shop Settings table
SELECT '=== SHOP SETTINGS TABLE ===' as info;
SELECT 
    id,
    shop_id,
    show_offer_on_checkout,
    show_email_optin,
    created_at,
    updated_at
FROM shop_settings
ORDER BY id;

-- Offers table
SELECT '=== OFFERS TABLE ===' as info;
SELECT 
    id,
    shop_id,
    headline,
    LEFT(body, 50) as body_preview,
    LEFT(image_url, 50) as image_url_preview,
    button_text,
    LEFT(button_url, 50) as button_url_preview,
    status,
    created_at,
    updated_at
FROM offers
ORDER BY id;

-- Offer Themes table
SELECT '=== OFFER THEMES TABLE ===' as info;
SELECT 
    id,
    shop_id,
    name,
    primary_color,
    secondary_color,
    accent_color,
    is_default,
    created_at
FROM offer_themes
ORDER BY id;

-- Offer Layouts table
SELECT '=== OFFER LAYOUTS TABLE ===' as info;
SELECT 
    id,
    shop_id,
    name,
    description,
    LEFT(css_classes, 50) as css_classes_preview,
    LEFT(preview_html, 50) as preview_html_preview,
    created_at
FROM offer_layouts
ORDER BY id;

-- Warranty Insurance Products table
SELECT '=== WARRANTY INSURANCE PRODUCTS TABLE ===' as info;
SELECT 
    id,
    insurer_name,
    product_category,
    includes_adh,
    is_active,
    created_at,
    updated_at
FROM warranty_insurance_products
ORDER BY id;

-- Warranty Pricing Bands table
SELECT '=== WARRANTY PRICING BANDS TABLE ===' as info;
SELECT 
    id,
    insurance_product_id,
    msrp_min,
    msrp_max,
    price_2_year,
    price_3_year,
    effective_date,
    expiry_date,
    created_at,
    updated_at
FROM warranty_pricing_bands
ORDER BY id;

-- ========================================
-- 3. DATA COUNTS
-- ========================================

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

-- ========================================
-- 4. SAMPLE PRICING DATA (if any exists)
-- ========================================

SELECT '=== SAMPLE PRICING DATA ===' as info;
SELECT 
    wip.insurer_name,
    wip.product_category,
    wip.includes_adh,
    COUNT(wpb.id) as pricing_bands_count,
    MIN(wpb.msrp_min) as min_price,
    MAX(wpb.msrp_max) as max_price,
    MIN(wpb.price_2_year) as min_2yr_price,
    MAX(wpb.price_2_year) as max_2yr_price,
    MIN(wpb.price_3_year) as min_3yr_price,
    MAX(wpb.price_3_year) as max_3yr_price
FROM warranty_insurance_products wip
LEFT JOIN warranty_pricing_bands wpb ON wip.id = wpb.insurance_product_id
GROUP BY wip.id, wip.insurer_name, wip.product_category, wip.includes_adh
ORDER BY wip.insurer_name, wip.product_category;

-- ========================================
-- 5. TRIGGERS AND FUNCTIONS
-- ========================================

SELECT '=== TRIGGERS ===' as info;
SELECT 
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement
FROM information_schema.triggers 
WHERE trigger_schema = 'public'
ORDER BY trigger_name;

SELECT '=== FUNCTIONS ===' as info;
SELECT 
    routine_name,
    routine_type,
    data_type
FROM information_schema.routines 
WHERE routine_schema = 'public'
ORDER BY routine_name; 