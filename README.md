# Flex Warranty API

A multitenant Flask API for managing electronics warranty offers in Shopify stores.

## Features

- **Multitenant Architecture**: All data scoped by `shop_id`
- **Warranty Offer Management**: Create, update, delete warranty offers
- **Theme Customization**: Color schemes and styling options
- **Layout Templates**: Customizable offer layouts
- **Shop Settings**: Per-shop configuration
- **Shopify Integration**: OAuth and webhook support

## Database Schema

The API uses Supabase/PostgreSQL with the following key tables:

- `shops` - Store merchant information
- `shop_settings` - Per-shop configuration
- `offers` - Warranty offers with content and styling
- `offer_themes` - Color schemes and styling
- `offer_layouts` - Layout templates

## Setup

### 1. Environment Variables

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://username:password@host:port/database
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret
SHOPIFY_API_SECRET=your_api_secret
SHOPIFY_APP_URL=https://your-app-url.com
API_TOKEN=your_api_token
DEBUG=True
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

Run the SQL schema in your Supabase project:

```sql
-- Copy and run the contents of database_schema.sql
```

### 4. Run the API

```bash
python main.py
```

## API Endpoints

### Authentication

All API endpoints require authentication via:
- `X-Shop-Domain` header or `shop` query parameter
- `Authorization` header with Bearer token

### Offers

- `GET /api/offers` - List all offers for shop
- `GET /api/offers/{id}` - Get specific offer
- `POST /api/offers` - Create new offer
- `PUT /api/offers/{id}` - Update offer
- `DELETE /api/offers/{id}` - Delete offer
- `POST /api/offers/{id}/toggle-status` - Toggle offer status

### Themes

- `GET /api/themes` - List all themes
- `GET /api/themes/{id}` - Get specific theme
- `POST /api/themes` - Create new theme
- `PUT /api/themes/{id}` - Update theme
- `DELETE /api/themes/{id}` - Delete theme
- `POST /api/themes/{id}/set-default` - Set default theme

### Layouts

- `GET /api/layouts` - List all layouts
- `GET /api/layouts/{id}` - Get specific layout
- `POST /api/layouts` - Create new layout
- `PUT /api/layouts/{id}` - Update layout
- `DELETE /api/layouts/{id}` - Delete layout
- `POST /api/layouts/preview` - Preview layout

### Shop Settings

- `GET /api/shops/settings` - Get shop settings
- `PUT /api/shops/settings` - Update shop settings
- `POST /api/shops/api-token` - Regenerate API token
- `GET /api/shops/stats` - Get shop statistics

### Webhooks

- `POST /api/webhooks/app/installed` - App installation
- `POST /api/webhooks/app/uninstalled` - App uninstallation
- `POST /api/webhooks/shop/update` - Shop updates
- `POST /api/webhooks/orders/create` - Order creation

## Example Usage

### Create a Warranty Offer

```bash
curl -X POST https://your-api.com/api/offers \
  -H "Content-Type: application/json" \
  -H "X-Shop-Domain: your-shop.myshopify.com" \
  -H "Authorization: Bearer your-api-token" \
  -d '{
    "headline": "Extended Warranty Protection",
    "body": "Protect your purchase with comprehensive coverage",
    "button_text": "Add Warranty",
    "button_url": "/products/warranty",
    "status": "active"
  }'
```

### Create a Theme

```bash
curl -X POST https://your-api.com/api/themes \
  -H "Content-Type: application/json" \
  -H "X-Shop-Domain: your-shop.myshopify.com" \
  -H "Authorization: Bearer your-api-token" \
  -d '{
    "name": "Blue Theme",
    "primary_color": "#2563eb",
    "secondary_color": "#1e40af",
    "accent_color": "#3b82f6",
    "is_default": true
  }'
```

## Deployment

### Fly.io

1. Install Fly CLI
2. Run `fly launch`
3. Set environment variables: `fly secrets set DATABASE_URL=...`
4. Deploy: `fly deploy`

### Docker

```bash
docker build -t flex-warranty-api .
docker run -p 8080:8080 flex-warranty-api
```

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

```bash
black .
flake8 .
```

## License

MIT License 