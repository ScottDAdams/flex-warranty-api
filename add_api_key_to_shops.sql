-- Add API key column to shops table
ALTER TABLE shops 
ADD COLUMN IF NOT EXISTS api_key VARCHAR(255);

-- Create index for faster API key lookups
CREATE INDEX IF NOT EXISTS idx_shops_api_key ON shops(api_key);

-- Verify the changes
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'shops' 
ORDER BY ordinal_position; 