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


@shops_bp.route('/me', methods=['GET'])
@require_auth
def get_shop_me():
    """Return normalized state for the current shop.

    Response shape:
    {
      shop_url,
      product_id, variant_id, collection_id,
      has_product, has_variant, has_collection,
      registered
    }
    """
    try:
        shop_context = get_shop_context()

        with get_db() as db:
            # Ensure onboarding columns exist (safe, idempotent)
            try:
                db.execute(text("ALTER TABLE shops ADD COLUMN IF NOT EXISTS onboarding_step SMALLINT NOT NULL DEFAULT 0"))
                db.execute(text("ALTER TABLE shops ADD COLUMN IF NOT EXISTS onboarding JSONB NOT NULL DEFAULT '{}'::jsonb"))
            except Exception:
                pass

            row = db.execute(text('''
                SELECT shop_url, product_id, variant_id, collection_id, api_key,
                       COALESCE(onboarding_step, 0) AS onboarding_step,
                       COALESCE(onboarding, '{}'::jsonb) AS onboarding
                FROM shops WHERE id = :sid
            '''), { 'sid': shop_context['shop_id'] }).mappings().first()
            if not row:
                return jsonify({'error': 'Shop not found'}), 404

            resp = {
                'shop_url': row['shop_url'],
                'product_id': row['product_id'],
                'variant_id': row['variant_id'],
                'collection_id': row['collection_id'],
                'has_product': bool(row['product_id']),
                'has_variant': bool(row['variant_id']),
                'has_collection': bool(row['collection_id']),
                'registered': bool(row['api_key']),
                'onboarding_step': int(row['onboarding_step'] or 0),
                'onboarding': row['onboarding'] or {},
            }

            return jsonify(resp), 200

    except Exception as e:
        logger.error(f"Error getting shop me: {str(e)}")
        return jsonify({'error': 'Failed to get shop state'}), 500


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


@shops_bp.route('/setup/run', methods=['POST'])
@require_auth
def run_setup_step():
    """Run a single, idempotent setup step and persist onboarding progress."""
    try:
        shop_context = get_shop_context()
        data = request.get_json(silent=True) or {}
        step = str(data.get('step') or '').strip()
        if not step:
            return jsonify({ 'error': 'Missing step' }), 400

        with get_db() as db:
            # Ensure onboarding columns exist
            try:
                db.execute(text("ALTER TABLE shops ADD COLUMN IF NOT EXISTS onboarding_step SMALLINT NOT NULL DEFAULT 0"))
                db.execute(text("ALTER TABLE shops ADD COLUMN IF NOT EXISTS onboarding JSONB NOT NULL DEFAULT '{}'::jsonb"))
            except Exception:
                pass

            shop = db.execute(text("""
                SELECT shop_url, access_token, product_id, collection_id, api_key,
                       COALESCE(onboarding, '{}'::jsonb) AS onboarding,
                       COALESCE(onboarding_step, 0) AS onboarding_step
                FROM shops
                WHERE id = :sid
            """), { 'sid': shop_context['shop_id'] }).mappings().first()
            if not shop or not shop.get('access_token'):
                return jsonify({ 'error': 'Shop not configured (missing access token)' }), 400

            import requests
            base_admin = f"https://{shop['shop_url']}/admin/api/2025-07/graphql.json"
            headers = { 'X-Shopify-Access-Token': shop['access_token'], 'Content-Type': 'application/json' }

            def update_flags(delta: dict, step_bump: int = None):
                onboarding = dict(shop.get('onboarding') or {})
                onboarding.update(delta)
                params = { 'sid': shop_context['shop_id'], 'onb': json.dumps(onboarding) }
                set_step = ''
                if step_bump is not None:
                    set_step = ', onboarding_step = :stp'
                    params['stp'] = step_bump
                db.execute(text(f"UPDATE shops SET onboarding = CAST(:onb AS JSONB){set_step}, updated_at = now() WHERE id = :sid"), params)

            if step == 'ensure_product':
                # Find or create product
                q = { 'query': 'query{ products(first:1, query: "title:\'Flex Protect - Extended Warranty\'") { edges { node { id } } } }' }
                r = requests.post(base_admin, headers=headers, json=q, timeout=15); j = r.json()
                pid = (((j.get('data') or {}).get('products') or {}).get('edges') or [{}])[0].get('node', {}).get('id')
                if not pid:
                    c = {
                        'query': 'mutation($input: ProductInput!){ productCreate(input:$input){ product{ id } userErrors{ field message } } }',
                        'variables': { 'input': { 'title': 'Flex Protect - Extended Warranty', 'vendor': 'Flex Protect', 'productType': 'Warranty', 'status': 'ACTIVE' } }
                    }
                    r2 = requests.post(base_admin, headers=headers, json=c, timeout=20); j2 = r2.json();
                    if (j2.get('data') or {}).get('productCreate', {}).get('userErrors'):
                        return jsonify({ 'error': 'productCreate failed', 'body': j2 }), 500
                    pid = (j2.get('data') or {}).get('productCreate', {}).get('product', {}).get('id')

                # Description
                desc = "Flex Protect - Extended Warranty offers comprehensive coverage that extends the life of your valuable products beyond the manufacturer’s warranty. This plan not only safeguards your purchase against unexpected mechanical and electrical failures but also includes Accidental Damage from Handling (ADH) protection, covering drops, spills, and other common mishaps. Designed to provide peace of mind, Flex Protect minimizes repair costs and downtime, ensuring your device stays in optimal condition with expert service support when you need it most."
                requests.post(base_admin, headers=headers, json={ 'query': 'mutation($input: ProductInput!){ productUpdate(input:$input){ product{ id } userErrors{ field message } } }', 'variables': { 'input': { 'id': pid, 'status': 'ACTIVE', 'vendor': 'Flex Protect', 'productType': 'Warranty', 'descriptionHtml': desc } } }, timeout=20)

                # Media
                media = [
                    { 'originalSource': 'https://flex-warranty-api.fly.dev/static/images/Protection-Tile.jpeg', 'alt': 'Flex Protect Protection Overview', 'mediaContentType': 'IMAGE' },
                    { 'originalSource': 'https://flex-warranty-api.fly.dev/static/images/Claims-Tile.jpeg', 'alt': 'Fast, simple claims', 'mediaContentType': 'IMAGE' },
                    { 'originalSource': 'https://flex-warranty-api.fly.dev/static/images/Savings-Tile.jpeg', 'alt': 'Save on repairs and replacements', 'mediaContentType': 'IMAGE' },
                ]
                requests.post(base_admin, headers=headers, json={ 'query': 'mutation($input: ProductInput!, $media: [CreateMediaInput!]!){ productUpdate(input:$input, media:$media){ product{ id } userErrors{ field message } } }', 'variables': { 'input': { 'id': pid }, 'media': media } }, timeout=30)

                # Publish to Online Store
                pubs = requests.post(base_admin, headers=headers, json={ 'query': 'query { publications(first:10){ edges { node { id name } } } }' }, timeout=15).json()
                pub = None
                try:
                    pub = [e['node']['id'] for e in pubs['data']['publications']['edges'] if e['node']['name'] == 'Online Store'][0]
                except Exception:
                    pub = None
                if pub:
                    requests.post(base_admin, headers=headers, json={ 'query': 'mutation($id: ID!, $pub: ID!){ publishablePublish(id:$id, input:{ publicationId:$pub }){ userErrors{ field message } } }', 'variables': { 'id': pid, 'pub': pub } }, timeout=20)

                # Persist product id
                db.execute(text('UPDATE shops SET product_id = :pid, updated_at = now() WHERE id = :sid'), { 'pid': pid, 'sid': shop_context['shop_id'] })
                update_flags({ 'product_done': True }, 4)
                return jsonify({ 'ok': True, 'product_id': pid })

            if step == 'ensure_collection':
                q = { 'query': 'query { collections(first:1, query: "title:\'ALL\' OR title:\'ALL (Smart)\'") { edges { node { id title ruleSet { rules { column relation condition } } } } } }' }
                r = requests.post(base_admin, headers=headers, json=q, timeout=15).json()
                edges = (((r.get('data') or {}).get('collections') or {}).get('edges') or [])
                cid = edges[0]['node']['id'] if edges else None
                if not edges:
                    m = {
                        'query': 'mutation($input: CollectionInput!){ collectionCreate(input:$input){ collection{ id } userErrors{ field message } } }',
                        'variables': { 'input': { 'title': 'ALL', 'ruleSet': { 'appliedDisjunctively': False, 'rules': [ { 'column': 'VENDOR', 'relation': 'NOT_EQUALS', 'condition': 'Flex Protect' } ] } } }
                    }
                    cj = requests.post(base_admin, headers=headers, json=m, timeout=20).json()
                    cid = (cj.get('data') or {}).get('collectionCreate', {}).get('collection', {}).get('id')
                else:
                    if not edges[0]['node'].get('ruleSet'):
                        m2 = {
                            'query': 'mutation($input: CollectionInput!){ collectionCreate(input:$input){ collection{ id } userErrors{ field message } } }',
                            'variables': { 'input': { 'title': 'ALL (Smart)', 'ruleSet': { 'appliedDisjunctively': False, 'rules': [ { 'column': 'VENDOR', 'relation': 'NOT_EQUALS', 'condition': 'Flex Protect' } ] } } }
                        }
                        cj2 = requests.post(base_admin, headers=headers, json=m2, timeout=20).json()
                        cid = (cj2.get('data') or {}).get('collectionCreate', {}).get('collection', {}).get('id')

                pubs = requests.post(base_admin, headers=headers, json={ 'query': 'query { publications(first:10){ edges { node { id name } } } }' }, timeout=15).json()
                pub = None
                try:
                    pub = [e['node']['id'] for e in pubs['data']['publications']['edges'] if e['node']['name'] == 'Online Store'][0]
                except Exception:
                    pub = None
                if pub and cid:
                    requests.post(base_admin, headers=headers, json={ 'query': 'mutation($id: ID!, $pub: ID!){ publishablePublish(id:$id, input:{ publicationId:$pub }){ userErrors{ field message } } }', 'variables': { 'id': cid, 'pub': pub } }, timeout=20)

                db.execute(text('UPDATE shops SET collection_id = :cid, updated_at = now() WHERE id = :sid'), { 'cid': cid, 'sid': shop_context['shop_id'] })
                update_flags({ 'collection_done': True }, 5)
                return jsonify({ 'ok': True, 'collection_id': cid })

            if step == 'install_script':
                # Delete existing
                lst = requests.post(base_admin, headers=headers, json={ 'query': 'query { scriptTags(first:50){ edges { node { id src } } } }' }, timeout=15).json()
                for e in (lst.get('data') or {}).get('scriptTags', {}).get('edges', []):
                    src = (e.get('node') or {}).get('src') or ''
                    if ('/app/storefront-token' in src) or ('/js/warranty-embed.js' in src):
                        requests.post(base_admin, headers=headers, json={ 'query': 'mutation($id: ID!){ scriptTagDelete(id:$id){ deletedScriptTagId userErrors{ field message } } }', 'variables': { 'id': e['node']['id'] } }, timeout=15)
                embedSrc = f"https://flex-warranty-api.fly.dev/api/js/warranty-embed.js?v={int(datetime.utcnow().timestamp())}"
                cr = requests.post(base_admin, headers=headers, json={ 'query': 'mutation($input: ScriptTagInput!){ scriptTagCreate(input:$input){ scriptTag{ id src displayScope } userErrors{ field message } } }', 'variables': { 'input': { 'src': embedSrc, 'displayScope': 'ALL' } } }, timeout=15).json()
                if (cr.get('data') or {}).get('scriptTagCreate', {}).get('userErrors'):
                    return jsonify({ 'error': 'scriptTagCreate failed', 'body': cr }), 500
                update_flags({ 'script_installed': True }, 6)
                return jsonify({ 'ok': True })

            return jsonify({ 'error': 'Unknown step' }), 400

    except Exception as e:
        logger.error(f"setup_run error: {e}")
        return jsonify({ 'error': 'Setup failed' }), 500