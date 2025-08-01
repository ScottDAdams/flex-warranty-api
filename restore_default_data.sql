-- Restore default layouts and themes functions

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
DROP TRIGGER IF EXISTS create_default_shop_data_trigger ON shops;
CREATE TRIGGER create_default_shop_data_trigger
    AFTER INSERT ON shops
    FOR EACH ROW
    EXECUTE FUNCTION create_default_shop_data(); 