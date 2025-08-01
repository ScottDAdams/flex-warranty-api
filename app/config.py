import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')

    # Shopify settings
    SHOPIFY_WEBHOOK_SECRET = os.environ.get('SHOPIFY_WEBHOOK_SECRET')
    SHOPIFY_APP_URL = os.getenv('SHOPIFY_APP_URL', 'https://your-default-url.com')
    SHOPIFY_API_SECRET = os.environ.get('SHOPIFY_API_SECRET')

    # Email settings
    SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '2525'))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    EMAIL_FROM_ADDRESS = os.environ.get('EMAIL_FROM_ADDRESS')

    # API
    API_TOKEN = os.getenv('API_TOKEN')

    # CORS
    CORS_ORIGINS = [
        'https://*.myshopify.com',  # All Shopify store domains
        'https://*.myshopify.io',  # All Shopify dev
        'https://*.trycloudflare.com',  # All Cloudflare tunnel domains
        'https://*.tail85cd8a.ts.net'  # All tailscale domains
    ]

    # Additional configs can be added here
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true' 