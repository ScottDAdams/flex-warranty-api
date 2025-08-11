from flask import Blueprint, request, jsonify
from sqlalchemy import text
import json
from datetime import datetime
from ..utils.auth import require_auth, get_shop_context
from ..models.database import get_db, Shop, ShopSettings
import logging

logger = logging.getLogger(__name__)

# Create the Blueprint
shops_bp = Blueprint('shops', __name__)


@shops_bp.route('/settings', methods=['GET'])
@require_auth
def get_shop_settings():
    """Get shop settings for the current shop"""
    try:
        shop_context = get_shop_context()
        
        with get_db() as db:
            result = db.execute(
                text('''
                    SELECT ss.*, s.shop_url
                    FROM shop_settings ss
                    JOIN shops s ON s.id = ss.shop_id
                    WHERE ss.shop_id = :shop_id
                '''),
                {'shop_id': shop_context['shop_id']}
            ).mappings().first()
            
            if not result:
                return jsonify({'error': 'Shop settings not found'}), 404
            
            settings = dict(result)
            settings['created_at'] = settings['created_at'].isoformat() if settings['created_at'] else None
            settings['updated_at'] = settings['updated_at'].isoformat() if settings['updated_at'] else None
            
            return jsonify({'settings': settings}), 200
            
    except Exception as e:
        logger.error(f"Error getting shop settings: {str(e)}")
        return jsonify({'error': 'Failed to get shop settings'}), 500


@shops_bp.route('/settings', methods=['PUT'])
@require_auth
def update_shop_settings():
    """Update shop settings"""
    try:
        shop_context = get_shop_context()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        with get_db() as db:
            # Check if settings exist
            existing = db.execute(
                text('SELECT id FROM shop_settings WHERE shop_id = :shop_id'),
                {'shop_id': shop_context['shop_id']}
            ).fetchone()
            
            if not existing:
                return jsonify({'error': 'Shop settings not found'}), 404
            
            # Build update query dynamically
            update_fields = []
            params = {'shop_id': shop_context['shop_id']}
            
            for field in ['show_offer_on_checkout', 'show_email_optin']:
                if field in data:
                    update_fields.append(f"{field} = :{field}")
                    params[field] = data[field]
            
            if not update_fields:
                return jsonify({'error': 'No fields to update'}), 400
            
            # Update the settings
            db.execute(
                text(f'''
                    UPDATE shop_settings 
                    SET {', '.join(update_fields)}, updated_at = now()
                    WHERE shop_id = :shop_id
                '''),
                params
            )
            
            # Get the updated settings
            result = db.execute(
                text('''
                    SELECT ss.*, s.shop_url
                    FROM shop_settings ss
                    JOIN shops s ON s.id = ss.shop_id
                    WHERE ss.shop_id = :shop_id
                '''),
                {'shop_id': shop_context['shop_id']}
            ).mappings().first()
            
            settings = dict(result)
            settings['created_at'] = settings['created_at'].isoformat() if settings['created_at'] else None
            settings['updated_at'] = settings['updated_at'].isoformat() if settings['updated_at'] else None
            
            return jsonify({'settings': settings}), 200
            
    except Exception as e:
        logger.error(f"Error updating shop settings: {str(e)}")
        return jsonify({'error': 'Failed to update shop settings'}), 500


@shops_bp.route('/api-key', methods=['POST'])
@require_auth
def regenerate_api_key():
    """Regenerate the API key for the shop (stored in shops.api_key)"""
    try:
        shop_context = get_shop_context()

        with get_db() as db:
            import secrets
            api_key = f"fw_{secrets.token_urlsafe(32)}"

            db.execute(
                text('UPDATE shops SET api_key = :api_key, updated_at = now() WHERE id = :shop_id'),
                {'api_key': api_key, 'shop_id': shop_context['shop_id']}
            )

            return jsonify({
                'message': 'API key regenerated successfully',
                'api_key': api_key
            }), 200

    except Exception as e:
        logger.error(f"Error regenerating API key: {str(e)}")
        return jsonify({'error': 'Failed to regenerate API key'}), 500


@shops_bp.route('/stats', methods=['GET'])
@require_auth
def get_shop_stats():
    """Get statistics for the current shop"""
    try:
        shop_context = get_shop_context()
        
        with get_db() as db:
            # Get counts
            stats = {}
            
            # Count offers
            result = db.execute(
                text('SELECT COUNT(*) FROM offers WHERE shop_id = :shop_id'),
                {'shop_id': shop_context['shop_id']}
            ).fetchone()
            stats['total_offers'] = result[0]
            
            # Count active offers
            result = db.execute(
                text('SELECT COUNT(*) FROM offers WHERE shop_id = :shop_id AND status = :status'),
                {'shop_id': shop_context['shop_id'], 'status': 'active'}
            ).fetchone()
            stats['active_offers'] = result[0]
            
            # Count themes
            result = db.execute(
                text('SELECT COUNT(*) FROM offer_themes WHERE shop_id = :shop_id'),
                {'shop_id': shop_context['shop_id']}
            ).fetchone()
            stats['total_themes'] = result[0]
            
            # Count layouts
            result = db.execute(
                text('SELECT COUNT(*) FROM offer_layouts WHERE shop_id = :shop_id'),
                {'shop_id': shop_context['shop_id']}
            ).fetchone()
            stats['total_layouts'] = result[0]
            
            return jsonify({'stats': stats}), 200
            
    except Exception as e:
        logger.error(f"Error getting shop stats: {str(e)}")
        return jsonify({'error': 'Failed to get shop stats'}), 500


@shops_bp.route('/register', methods=['POST'])
def register_shop():
    """Register a new shop with warranty product and collection info"""
    try:
        data = request.get_json()
        shop_url = data.get('shop_url')
        access_token = data.get('access_token')
        product_id = data.get('product_id')
        variant_id = data.get('variant_id')
        collection_id = data.get('collection_id')

        if not shop_url or not access_token:
            return jsonify({'error': 'Missing required fields'}), 400

        with get_db() as db:
            # Check if shop already exists
            existing_shop = db.query(Shop).filter_by(shop_url=shop_url).first()
            
            if existing_shop:
                # Update existing shop with new product/variant/collection info
                existing_shop.access_token = access_token
                existing_shop.product_id = product_id
                existing_shop.variant_id = variant_id
                existing_shop.collection_id = collection_id
                
                # Generate new API key for existing shop
                import secrets
                api_key = f"fw_{secrets.token_urlsafe(32)}"
                existing_shop.api_key = api_key
                
                db.commit()

                return jsonify({
                    'message': 'Shop updated successfully',
                    'shop_id': existing_shop.id,
                    'api_key': api_key
                }), 200
            else:
                # Generate API key for new shop
                import secrets
                api_key = f"fw_{secrets.token_urlsafe(32)}"
                
                # Create new shop with API key
                new_shop = Shop(
                    shop_url=shop_url,
                    access_token=access_token,
                    api_key=api_key,
                    product_id=product_id,
                    variant_id=variant_id,
                    collection_id=collection_id
                )
                db.add(new_shop)
                db.commit()
                db.refresh(new_shop)

                return jsonify({
                    'message': 'Shop registered successfully',
                    'shop_id': new_shop.id,
                    'api_key': api_key
                }), 201

    except Exception as e:
        logger.error(f"Shop registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500


@shops_bp.route('/uninstall', methods=['POST'])
def uninstall_shop():
    """Handle shop uninstallation"""
    try:
        data = request.get_json()
        shop_url = data.get('shop_url')

        if not shop_url:
            return jsonify({'error': 'Missing shop_url'}), 400

        with get_db() as db:
            shop = db.query(Shop).filter_by(shop_url=shop_url).first()
            
            if shop:
                # Delete shop and all related data (cascade will handle related records)
                db.delete(shop)
                db.commit()
                
                return jsonify({'message': 'Shop uninstalled successfully'}), 200
            else:
                return jsonify({'message': 'Shop not found'}), 404

    except Exception as e:
        logger.error(f"Shop uninstall error: {str(e)}")
        return jsonify({'error': 'Uninstall failed'}), 500 