-- Flex Warranty Pricing Database Schema
-- Run this script in your Supabase SQL editor

-- Create warranty insurance products table
CREATE TABLE IF NOT EXISTS warranty_insurance_products (
    id SERIAL PRIMARY KEY,
    insurer_name VARCHAR(100) NOT NULL, -- e.g., 'AIG', 'SquareTrade', etc.
    product_category VARCHAR(100) NOT NULL, -- e.g., 'Consumer Electronics', 'Desktops, Laptops', 'Tablets', 'TVs'
    includes_adh BOOLEAN DEFAULT false, -- Accidental Damage from Handling
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Create warranty pricing bands table
CREATE TABLE IF NOT EXISTS warranty_pricing_bands (
    id SERIAL PRIMARY KEY,
    insurance_product_id INTEGER NOT NULL REFERENCES warranty_insurance_products(id) ON DELETE CASCADE,
    msrp_min DECIMAL(10,2) NOT NULL,
    msrp_max DECIMAL(10,2) NOT NULL,
    price_2_year DECIMAL(10,2) NOT NULL,
    price_3_year DECIMAL(10,2) NOT NULL,
    effective_date TIMESTAMP NOT NULL DEFAULT now(),
    expiry_date TIMESTAMP, -- NULL means currently active
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_warranty_insurance_products_insurer ON warranty_insurance_products(insurer_name);
CREATE INDEX IF NOT EXISTS idx_warranty_insurance_products_category ON warranty_insurance_products(product_category);
CREATE INDEX IF NOT EXISTS idx_warranty_insurance_products_active ON warranty_insurance_products(is_active);
CREATE INDEX IF NOT EXISTS idx_warranty_pricing_bands_product_id ON warranty_pricing_bands(insurance_product_id);
CREATE INDEX IF NOT EXISTS idx_warranty_pricing_bands_msrp ON warranty_pricing_bands(msrp_min, msrp_max);
CREATE INDEX IF NOT EXISTS idx_warranty_pricing_bands_effective ON warranty_pricing_bands(effective_date, expiry_date);

-- Create updated_at trigger function (if not already exists)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_warranty_insurance_products_updated_at BEFORE UPDATE ON warranty_insurance_products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_warranty_pricing_bands_updated_at BEFORE UPDATE ON warranty_pricing_bands
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE warranty_insurance_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE warranty_pricing_bands ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Allow all operations on warranty_insurance_products" ON warranty_insurance_products FOR ALL USING (true);
CREATE POLICY "Allow all operations on warranty_pricing_bands" ON warranty_pricing_bands FOR ALL USING (true);

-- Insert default AIG insurance products
INSERT INTO warranty_insurance_products (insurer_name, product_category, includes_adh) VALUES
('AIG', 'Consumer Electronics', true),
('AIG', 'Desktops, Laptops', true),
('AIG', 'Tablets', true),
('AIG', 'TVs', false)
ON CONFLICT DO NOTHING; 