from flask import Blueprint, request, jsonify
from sqlalchemy import text
import json
import hmac
import hashlib
import logging
from ..models.database import get_db
from ..config import Config
import base64

logger = logging.getLogger(__name__)

# Create the Blueprint
webhooks_bp = Blueprint('webhooks', __name__)


def verify_webhook_signature(data, signature, secret):
    """Verify Shopify webhook signature"""
    try:
        calculated_signature = base64.b64encode(
            hmac.new(
                secret.encode('utf-8'),
                data,
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        return hmac.compare_digest(calculated_signature, signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {str(e)}")
        return False


@webhooks_bp.route('/app/installed', methods=['POST'])
def app_installed():
    """Handle app installation webhook"""
    try:
        # Verify webhook signature
        signature = request.headers.get('X-Shopify-Hmac-Sha256')
        if not signature:
            return jsonify({'error': 'Missing signature'}), 401
        
        if not verify_webhook_signature(request.data, signature, Config.SHOPIFY_WEBHOOK_SECRET):
            return jsonify({'error': 'Invalid signature'}), 401
        
        data = request.get_json()
        shop_domain = data.get('shop_domain')
        access_token = data.get('access_token')
        
        if not shop_domain or not access_token:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Register the shop
        with get_db() as db:
            # Check if shop already exists
            existing = db.execute(
                text('SELECT id FROM shops WHERE shop_url = :shop_url'),
                {'shop_url': shop_domain}
            ).fetchone()
            
            if existing:
                # Update existing shop
                db.execute(
                    text('UPDATE shops SET access_token = :access_token, updated_at = now() WHERE shop_url = :shop_url'),
                    {
                        'access_token': access_token,
                        'shop_url': shop_domain
                    }
                )
                shop_id = existing[0]
            else:
                # Create new shop
                result = db.execute(
                    text('''
                        INSERT INTO shops (shop_url, access_token)
                        VALUES (:shop_url, :access_token)
                        RETURNING id
                    '''),
                    {
                        'shop_url': shop_domain,
                        'access_token': access_token
                    }
                )
                shop_id = result.fetchone()[0]
        
        logger.info(f"App installed for shop: {shop_domain}")
        return jsonify({'message': 'App installed successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error handling app installed webhook: {str(e)}")
        return jsonify({'error': 'Failed to handle webhook'}), 500


@webhooks_bp.route('/app/uninstalled', methods=['POST'])
def app_uninstalled():
    """Handle app uninstallation webhook"""
    try:
        # Verify webhook signature
        signature = request.headers.get('X-Shopify-Hmac-Sha256')
        if not signature:
            return jsonify({'error': 'Missing signature'}), 401
        
        if not verify_webhook_signature(request.data, signature, Config.SHOPIFY_WEBHOOK_SECRET):
            return jsonify({'error': 'Invalid signature'}), 401
        
        data = request.get_json()
        shop_domain = data.get('shop_domain')
        
        if not shop_domain:
            return jsonify({'error': 'Missing shop domain'}), 400
        
        # Remove shop access token (but keep data for potential reinstall)
        with get_db() as db:
            db.execute(
                text('UPDATE shops SET access_token = NULL, updated_at = now() WHERE shop_url = :shop_url'),
                {'shop_url': shop_domain}
            )
        
        logger.info(f"App uninstalled for shop: {shop_domain}")
        return jsonify({'message': 'App uninstalled successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error handling app uninstalled webhook: {str(e)}")
        return jsonify({'error': 'Failed to handle webhook'}), 500


@webhooks_bp.route('/shop/update', methods=['POST'])
def shop_update():
    """Handle shop update webhook"""
    try:
        # Verify webhook signature
        signature = request.headers.get('X-Shopify-Hmac-Sha256')
        if not signature:
            return jsonify({'error': 'Missing signature'}), 401
        
        if not verify_webhook_signature(request.data, signature, Config.SHOPIFY_WEBHOOK_SECRET):
            return jsonify({'error': 'Invalid signature'}), 401
        
        data = request.get_json()
        shop_domain = data.get('domain')
        
        if not shop_domain:
            return jsonify({'error': 'Missing shop domain'}), 400
        
        # Update shop information
        with get_db() as db:
            db.execute(
                text('UPDATE shops SET updated_at = now() WHERE shop_url = :shop_url'),
                {'shop_url': shop_domain}
            )
        
        logger.info(f"Shop updated: {shop_domain}")
        return jsonify({'message': 'Shop updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error handling shop update webhook: {str(e)}")
        return jsonify({'error': 'Failed to handle webhook'}), 500


@webhooks_bp.route('/orders/create', methods=['POST'])
def order_created():
    """Handle order creation webhook"""
    try:
        # Verify webhook signature
        signature = request.headers.get('X-Shopify-Hmac-Sha256')
        if not signature:
            return jsonify({'error': 'Missing signature'}), 401
        
        if not verify_webhook_signature(request.data, signature, Config.SHOPIFY_WEBHOOK_SECRET):
            return jsonify({'error': 'Invalid signature'}), 401
        
        data = request.get_json()
        shop_domain = data.get('shop_domain')
        order_id = data.get('id')
        
        if not shop_domain or not order_id:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Here you could implement logic to:
        # 1. Check if warranty offers should be shown for this order
        # 2. Send warranty offers via email
        # 3. Track order data for analytics
        
        logger.info(f"Order created: {order_id} for shop: {shop_domain}")
        return jsonify({'message': 'Order processed successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error handling order created webhook: {str(e)}")
        return jsonify({'error': 'Failed to handle webhook'}), 500 