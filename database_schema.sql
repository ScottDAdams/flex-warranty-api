-- Flex Warranty Database Schema
-- Run this script in your Supabase SQL editor

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create shops table
CREATE TABLE IF NOT EXISTS shops (
    id SERIAL PRIMARY KEY,
    shop_url VARCHAR(255) UNIQUE NOT NULL,
    access_token VARCHAR(255),
    product_id VARCHAR(255),  -- Shopify product ID for warranty product
    variant_id VARCHAR(255),  -- Shopify variant ID for warranty product
    collection_id VARCHAR(255),  -- Shopify collection ID for "All" collection
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Create shop_settings table
CREATE TABLE IF NOT EXISTS shop_settings (
    id SERIAL PRIMARY KEY,
    shop_id INTEGER UNIQUE NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    show_offer_on_checkout BOOLEAN DEFAULT true,
    show_email_optin BOOLEAN DEFAULT true,
    api_token VARCHAR(255) DEFAULT md5(random()::text),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Create offer_themes table
CREATE TABLE IF NOT EXISTS offer_themes (
    id SERIAL PRIMARY KEY,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    primary_color VARCHAR(50),
    secondary_color VARCHAR(50),
    accent_color VARCHAR(50),
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT now()
);

-- Create offer_layouts table
CREATE TABLE IF NOT EXISTS offer_layouts (
    id SERIAL PRIMARY KEY,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    name VARCHAR(255),
    description TEXT,
    css_classes TEXT,
    preview_html TEXT,
    created_at TIMESTAMP DEFAULT now()
);

-- Create offers table
CREATE TABLE IF NOT EXISTS offers (
    id SERIAL PRIMARY KEY,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    headline TEXT,
    body TEXT,
    image_url TEXT,
    button_text VARCHAR(255),
    button_url TEXT,
    theme JSONB,
    layout_id INTEGER REFERENCES offer_layouts(id),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_shops_shop_url ON shops(shop_url);
CREATE INDEX IF NOT EXISTS idx_offers_shop_id ON offers(shop_id);
CREATE INDEX IF NOT EXISTS idx_offers_status ON offers(status);
CREATE INDEX IF NOT EXISTS idx_offer_themes_shop_id ON offer_themes(shop_id);
CREATE INDEX IF NOT EXISTS idx_offer_layouts_shop_id ON offer_layouts(shop_id);
CREATE INDEX IF NOT EXISTS idx_shop_settings_shop_id ON shop_settings(shop_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_shops_updated_at BEFORE UPDATE ON shops
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shop_settings_updated_at BEFORE UPDATE ON shop_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_offers_updated_at BEFORE UPDATE ON offers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create a function to insert default layouts and themes for a new shop
CREATE OR REPLACE FUNCTION insert_default_layouts_and_themes(shop_id INTEGER)
RETURNS VOID AS $$
BEGIN
    -- Insert default layouts
    INSERT INTO offer_layouts (shop_id, name, description, css_classes, preview_html) VALUES
    (shop_id, 'Standard', 'Standard warranty offer layout', 'warranty-offer-standard', '<div class="warranty-offer-standard">Standard layout preview</div>'),
    (shop_id, 'Compact', 'Compact warranty offer layout', 'warranty-offer-compact', '<div class="warranty-offer-compact">Compact layout preview</div>'),
    (shop_id, 'Premium', 'Premium warranty offer layout', 'warranty-offer-premium', '<div class="warranty-offer-premium">Premium layout preview</div>');

    -- Insert default themes
    INSERT INTO offer_themes (shop_id, name, primary_color, secondary_color, accent_color, is_default) VALUES
    (shop_id, 'Default Blue', '#2563eb', '#1e40af', '#3b82f6', true),
    (shop_id, 'Green Theme', '#059669', '#047857', '#10b981', false),
    (shop_id, 'Purple Theme', '#7c3aed', '#5b21b6', '#8b5cf6', false);
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to automatically insert default layouts and themes when a new shop is created
CREATE OR REPLACE FUNCTION create_default_shop_data()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert default shop settings
    INSERT INTO shop_settings (shop_id) VALUES (NEW.id);

    -- Insert default layouts and themes
    PERFORM insert_default_layouts_and_themes(NEW.id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically create default data for new shops
CREATE TRIGGER create_default_shop_data_trigger
    AFTER INSERT ON shops
    FOR EACH ROW
    EXECUTE FUNCTION create_default_shop_data();

-- Enable Row Level Security (RLS)
ALTER TABLE shops ENABLE ROW LEVEL SECURITY;
ALTER TABLE shop_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE offers ENABLE ROW LEVEL SECURITY;
ALTER TABLE offer_themes ENABLE ROW LEVEL SECURITY;
ALTER TABLE offer_layouts ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (you may want to customize these based on your auth requirements)
-- For now, we'll allow all operations - you can restrict this later
CREATE POLICY "Allow all operations on shops" ON shops FOR ALL USING (true);
CREATE POLICY "Allow all operations on shop_settings" ON shop_settings FOR ALL USING (true);
CREATE POLICY "Allow all operations on offers" ON offers FOR ALL USING (true);
CREATE POLICY "Allow all operations on offer_themes" ON offer_themes FOR ALL USING (true);
CREATE POLICY "Allow all operations on offer_layouts" ON offer_layouts FOR ALL USING (true); 

-- Analytics tables
CREATE TABLE IF NOT EXISTS offer_events (
    id BIGSERIAL PRIMARY KEY,
    shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,
    session_token VARCHAR(128),
    payload JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_offer_events_shop_id ON offer_events(shop_id);
CREATE INDEX IF NOT EXISTS idx_offer_events_type ON offer_events(event_type);
CREATE INDEX IF NOT EXISTS idx_offer_events_session ON offer_events(session_token);