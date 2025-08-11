from flask import Blueprint, request, jsonify
from sqlalchemy import text
import json
from datetime import datetime
from ..utils.auth import require_auth, get_shop_context
from ..models.database import get_db, Offer, OfferTheme, OfferLayout, Shop, WarrantyInsuranceProduct, WarrantyPricingBand
import logging
import requests

logger = logging.getLogger(__name__)

# Create the Blueprint
offers_bp = Blueprint('offers', __name__)


@offers_bp.route('/offers', methods=['GET'])
@require_auth
def get_offers():
    """Get all offers for a shop"""
    try:
        shop_context = get_shop_context()
        
        with get_db() as db:
            result = db.execute(
                text('''
                    SELECT o.*, ol.name as layout_name
                    FROM offers o
                    LEFT JOIN offer_layouts ol ON o.layout_id = ol.id
                    WHERE o.shop_id = :shop_id
                    ORDER BY o.created_at DESC
                '''),
                {'shop_id': shop_context['shop_id']}
            ).mappings().all()

            offers = []
            for row in result:
                offers.append({
                    'id': row['id'],
                    'headline': row['headline'],
                    'body': row['body'],
                    'image_url': row['image_url'],
                    'button_text': row['button_text'],
                    'button_url': row['button_url'],
                    'theme': row['theme'],
                    'layout_id': row['layout_id'],
                    'layout_name': row['layout_name'],
                    'status': row['status'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
                })

            return jsonify({'offers': offers}), 200

    except Exception as e:
        logger.error(f"Get offers error: {str(e)}")
        return jsonify({'error': 'Failed to get offers'}), 500


@offers_bp.route('/offers/<int:offer_id>', methods=['GET'])
@require_auth
def get_offer(offer_id):
    """Get a specific offer"""
    try:
        shop_context = get_shop_context()
        
        with get_db() as db:
            result = db.execute(
                text('''
                    SELECT o.*, ol.name as layout_name
                    FROM offers o
                    LEFT JOIN offer_layouts ol ON o.layout_id = ol.id
                    WHERE o.id = :offer_id AND o.shop_id = :shop_id
                '''),
                {'offer_id': offer_id, 'shop_id': shop_context['shop_id']}
            ).mappings().first()

            if not result:
                return jsonify({'error': 'Offer not found'}), 404

            offer = {
                'id': result['id'],
                'headline': result['headline'],
                'body': result['body'],
                'image_url': result['image_url'],
                'button_text': result['button_text'],
                'button_url': result['button_url'],
                'theme': result['theme'],
                'layout_id': result['layout_id'],
                'layout_name': result['layout_name'],
                'status': result['status'],
                'created_at': result['created_at'].isoformat() if result['created_at'] else None,
                'updated_at': result['updated_at'].isoformat() if result['updated_at'] else None
            }

            return jsonify({'offer': offer}), 200

    except Exception as e:
        logger.error(f"Get offer error: {str(e)}")
        return jsonify({'error': 'Failed to get offer'}), 500


@offers_bp.route('/offers', methods=['POST'])
@require_auth
def create_offer():
    """Create a new offer"""
    try:
        shop_context = get_shop_context()
        data = request.get_json()

        required_fields = ['headline', 'body', 'button_text']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400

        with get_db() as db:
            new_offer = Offer(
                shop_id=shop_context['shop_id'],
                headline=data['headline'],
                body=data['body'],
                image_url=data.get('image_url'),
                button_text=data['button_text'],
                button_url=data.get('button_url'),
                theme=data.get('theme'),
                layout_id=data.get('layout_id'),
                status=data.get('status', 'active')
            )
            db.add(new_offer)
            db.commit()
            db.refresh(new_offer)

            return jsonify({
                'message': 'Offer created successfully',
                'offer_id': new_offer.id
            }), 201

    except Exception as e:
        logger.error(f"Create offer error: {str(e)}")
        return jsonify({'error': 'Failed to create offer'}), 500


@offers_bp.route('/offers/<int:offer_id>', methods=['PUT'])
@require_auth
def update_offer(offer_id):
    """Update an existing offer"""
    try:
        shop_context = get_shop_context()
        data = request.get_json()

        with get_db() as db:
            offer = db.query(Offer).filter_by(
                id=offer_id, 
                shop_id=shop_context['shop_id']
            ).first()

            if not offer:
                return jsonify({'error': 'Offer not found'}), 404

            # Update fields
            if 'headline' in data:
                offer.headline = data['headline']
            if 'body' in data:
                offer.body = data['body']
            if 'image_url' in data:
                offer.image_url = data['image_url']
            if 'button_text' in data:
                offer.button_text = data['button_text']
            if 'button_url' in data:
                offer.button_url = data['button_url']
            if 'theme' in data:
                offer.theme = data['theme']
            if 'layout_id' in data:
                offer.layout_id = data['layout_id']
            if 'status' in data:
                offer.status = data['status']

            db.commit()

            return jsonify({'message': 'Offer updated successfully'}), 200

    except Exception as e:
        logger.error(f"Update offer error: {str(e)}")
        return jsonify({'error': 'Failed to update offer'}), 500


@offers_bp.route('/offers/<int:offer_id>', methods=['DELETE'])
@require_auth
def delete_offer(offer_id):
    """Delete an offer"""
    try:
        shop_context = get_shop_context()
        
        with get_db() as db:
            offer = db.query(Offer).filter_by(
                id=offer_id, 
                shop_id=shop_context['shop_id']
            ).first()

            if not offer:
                return jsonify({'error': 'Offer not found'}), 404

            db.delete(offer)
            db.commit()

            return jsonify({'message': 'Offer deleted successfully'}), 200

    except Exception as e:
        logger.error(f"Delete offer error: {str(e)}")
        return jsonify({'error': 'Failed to delete offer'}), 500


@offers_bp.route('/offers/<int:offer_id>/toggle-status', methods=['POST'])
@require_auth
def toggle_offer_status(offer_id):
    """Toggle offer status between active and inactive"""
    try:
        shop_context = get_shop_context()
        
        with get_db() as db:
            offer = db.query(Offer).filter_by(
                id=offer_id, 
                shop_id=shop_context['shop_id']
            ).first()

            if not offer:
                return jsonify({'error': 'Offer not found'}), 404

            # Toggle status
            offer.status = 'inactive' if offer.status == 'active' else 'active'
            db.commit()

            return jsonify({
                'message': 'Offer status updated successfully',
                'status': offer.status
            }), 200

    except Exception as e:
        logger.error(f"Toggle status error: {str(e)}")
        return jsonify({'error': 'Failed to toggle status'}), 500


@offers_bp.route('/pricing', methods=['POST'])
def get_dynamic_pricing():
    """Get dynamic pricing for warranty product based on AIG pricing bands"""
    try:
        # Check for API key authentication
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'Missing API key'}), 401
        
        # Be tolerant of clients missing the JSON content-type
        try:
            data = request.get_json(silent=True)
            if data is None and request.data:
                import json as _json
                data = _json.loads(request.data)
        except Exception:
            data = {}
        
        session_token = data.get('session_token')
        product_id = data.get('product_id')
        product_price = data.get('product_price', 0)
        product_category = data.get('product_category', 'Consumer Electronics')  # Default category
        shop_domain = request.headers.get('X-Shop-Domain')
        
        if not session_token or not product_id:
            return jsonify({'error': 'Missing session_token or product_id'}), 400

        # Get shop info and validate API key
        with get_db() as db:
            shop = db.query(Shop).filter_by(shop_url=shop_domain).first()
            if not shop:
                return jsonify({'error': 'Shop not found'}), 404
            
            # Validate API key against shop record
            if not shop.api_key or shop.api_key != api_key:
                return jsonify({'error': 'Invalid API key'}), 401

        # Get all warranty pricing options from AIG pricing bands
        pricing_options = get_all_warranty_pricing_options(product_price, product_category)
        
        if not pricing_options:
            return jsonify({'error': 'No pricing found for this product'}), 404

        return jsonify({
            'session_token': session_token,
            'variant_id': shop.variant_id,
            'product_category': product_category,
            'includes_adh': pricing_options['includes_adh'],
            'pricing_options': pricing_options['options']
        }), 200

    except Exception as e:
        logger.error(f"Dynamic pricing error: {str(e)}")
        return jsonify({'error': 'Failed to get pricing'}), 500


def get_all_warranty_pricing_options(product_price, product_category):
    """Get all warranty pricing options from AIG pricing bands"""
    try:
        with get_db() as db:
            # Get active insurance product for the category
            insurance_product = db.query(WarrantyInsuranceProduct).filter_by(
                insurer_name='AIG',
                product_category=product_category,
                is_active=True
            ).first()
            
            if not insurance_product:
                logger.error(f"No active AIG insurance product found for category: {product_category}")
                return None
            
            # Get pricing band for the product price
            pricing_band = db.query(WarrantyPricingBand).filter(
                WarrantyPricingBand.insurance_product_id == insurance_product.id,
                WarrantyPricingBand.msrp_min <= product_price,
                WarrantyPricingBand.msrp_max >= product_price,
                WarrantyPricingBand.expiry_date.is_(None)  # Currently active
            ).first()
            
            if not pricing_band:
                logger.error(f"No pricing band found for product price: {product_price}")
                return None
            
            # Return all available pricing options
            options = []
            
            # Add 2-year option
            if pricing_band.price_2_year:
                options.append({
                    'term': 2,
                    'price': float(pricing_band.price_2_year),
                    'display_name': '2 Year'
                })
            
            # Add 3-year option
            if pricing_band.price_3_year:
                options.append({
                    'term': 3,
                    'price': float(pricing_band.price_3_year),
                    'display_name': '3 Year'
                })
            
            # Note: AIG pricing typically only has 2-year and 3-year options
            # If you need 1-year options, you'd need to add that to the pricing bands
            
            return {
                'options': options,
                'includes_adh': insurance_product.includes_adh,
                'product_category': product_category
            }
            
    except Exception as e:
        logger.error(f"Error getting warranty pricing options: {str(e)}")
        return None


def update_warranty_variant_price(access_token, shop_url, variant_id, price, session_token):
    """Update warranty variant price in Shopify"""
    try:
        # Create variant title with session token
        variant_title = f"Protection - {session_token[:8]}"
        
        mutation = '''
        mutation productVariantUpdate($input: ProductVariantInput!) {
          productVariantUpdate(input: $input) {
            productVariant {
              id
              title
              price
            }
            userErrors {
              field
              message
            }
          }
        }
        '''
        
        variables = {
            "input": {
                "id": f"gid://shopify/ProductVariant/{variant_id}",
                "title": variant_title,
                "price": str(price)
            }
        }
        
        response = requests.post(
            f"https://{shop_url}/admin/api/2024-01/graphql.json",
            headers={
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json"
            },
            json={
                "query": mutation,
                "variables": variables
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('data', {}).get('productVariantUpdate', {}).get('userErrors'):
                return {'success': False, 'errors': result['data']['productVariantUpdate']['userErrors']}
            return {'success': True, 'variant': result['data']['productVariantUpdate']['productVariant']}
        else:
            return {'success': False, 'error': f'Shopify API error: {response.status_code}'}
            
    except Exception as e:
        logger.error(f"Update variant price error: {str(e)}")
        return {'success': False, 'error': str(e)}


@offers_bp.route('/cleanup-variants', methods=['POST'])
@require_auth
def cleanup_old_variants():
    """Clean up old warranty variants to stay under Shopify limits"""
    try:
        shop_context = get_shop_context()
        
        with get_db() as db:
            shop = db.query(Shop).filter_by(id=shop_context['shop_id']).first()
            if not shop:
                return jsonify({'error': 'Shop not found'}), 404

        # Get all variants for the warranty product
        query = '''
        query getProductVariants($productId: ID!) {
          product(id: $productId) {
            variants(first: 250) {
              edges {
                node {
                  id
                  title
                  price
                  createdAt
                }
              }
            }
          }
        }
        '''
        
        response = requests.post(
            f"https://{shop.shop_url}/admin/api/2024-01/graphql.json",
            headers={
                "X-Shopify-Access-Token": shop.access_token,
                "Content-Type": "application/json"
            },
            json={
                "query": query,
                "variables": {
                    "productId": f"gid://shopify/Product/{shop.product_id}"
                }
            }
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to get variants'}), 500
            
        result = response.json()
        variants = result.get('data', {}).get('product', {}).get('variants', {}).get('edges', [])
        
        # If we have more than 100 variants, delete the oldest ones
        if len(variants) > 100:
            # Sort by creation date and delete oldest
            sorted_variants = sorted(variants, key=lambda x: x['node']['createdAt'])
            variants_to_delete = sorted_variants[:-100]  # Keep the 100 newest
            
            deleted_count = 0
            for variant in variants_to_delete:
                delete_mutation = '''
                mutation productVariantDelete($input: ProductVariantDeleteInput!) {
                  productVariantDelete(input: $input) {
                    deletedProductVariantId
                    userErrors {
                      field
                      message
                    }
                  }
                }
                '''
                
                delete_response = requests.post(
                    f"https://{shop.shop_url}/admin/api/2024-01/graphql.json",
                    headers={
                        "X-Shopify-Access-Token": shop.access_token,
                        "Content-Type": "application/json"
                    },
                    json={
                        "query": delete_mutation,
                        "variables": {
                            "input": {
                                "id": variant['node']['id']
                            }
                        }
                    }
                )
                
                if delete_response.status_code == 200:
                    deleted_count += 1
            
            return jsonify({
                'message': f'Cleaned up {deleted_count} old variants',
                'deleted_count': deleted_count
            }), 200
        else:
            return jsonify({
                'message': 'No cleanup needed',
                'variant_count': len(variants)
            }), 200

    except Exception as e:
        logger.error(f"Cleanup variants error: {str(e)}")
        return jsonify({'error': 'Failed to cleanup variants'}), 500 