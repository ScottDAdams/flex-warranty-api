from functools import wraps
from flask import request, jsonify
from sqlalchemy import text
from ..models.database import get_db
import logging

logger = logging.getLogger(__name__)

def require_auth(f):
    """Decorator to require authentication for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get shop domain from headers or query params
        shop_domain = request.headers.get('X-Shop-Domain') or request.args.get('shop')
        
        if not shop_domain:
            return jsonify({'error': 'Missing shop domain'}), 401
        
        # Get authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Missing authorization header'}), 401
        
        # Extract token (assuming Bearer token format)
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        else:
            token = auth_header
        
        # Validate shop and token
        try:
            with get_db() as db:
                result = db.execute(
                    text('''
                        SELECT s.id, s.shop_url, ss.api_token
                        FROM shops s
                        LEFT JOIN shop_settings ss ON s.id = ss.shop_id
                        WHERE s.shop_url = :shop_url
                    '''),
                    {'shop_url': shop_domain}
                ).mappings().first()
                
                if not result:
                    return jsonify({'error': 'Shop not found'}), 404
                
                # For now, we'll use the api_token from shop_settings
                # In production, you might want to validate against Shopify's session token
                if result['api_token'] and result['api_token'] != token:
                    return jsonify({'error': 'Invalid token'}), 401
                
                # Add shop info to request context
                request.shop_id = result['id']
                request.shop_url = result['shop_url']
                
        except Exception as e:
            logger.error(f"Auth error: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 500
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_shop_context():
    """Helper function to get current shop context"""
    return {
        'shop_id': getattr(request, 'shop_id', None),
        'shop_url': getattr(request, 'shop_url', None)
    } 