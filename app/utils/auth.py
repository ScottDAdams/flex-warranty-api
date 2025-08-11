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
        # Allow CORS preflight to pass without auth
        if request.method == 'OPTIONS':
            return ('', 200)
        # Get shop domain from headers or query params
        shop_domain = request.headers.get('X-Shop-Domain') or request.args.get('shop')
        if not shop_domain:
            return jsonify({'error': 'Missing shop domain'}), 401

        # API key can come from X-API-Key or Authorization: Bearer <key>
        auth_header = request.headers.get('Authorization') or ''
        bearer = auth_header[7:] if auth_header.startswith('Bearer ') else auth_header
        provided_key = (request.headers.get('X-API-Key') or bearer or '').strip()
        if not provided_key:
            return jsonify({'error': 'Missing API key'}), 401

        try:
            with get_db() as db:
                result = db.execute(
                    text('''
                        SELECT s.id, s.shop_url, s.api_key
                        FROM shops s
                        WHERE s.shop_url = :shop_url
                    '''),
                    {'shop_url': shop_domain}
                ).mappings().first()

                if not result:
                    return jsonify({'error': 'Shop not found'}), 404

                expected_key = (result['api_key'] or '').strip()
                if not expected_key or provided_key != expected_key:
                    return jsonify({'error': 'Invalid API key'}), 401

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