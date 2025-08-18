from flask import Blueprint, send_from_directory, current_app, request, jsonify
import os
import time
import hmac
import hashlib
from sqlalchemy import text
from ..models.database import get_db
from .offers import get_all_warranty_pricing_options
from ..config import Config
import json
import uuid

proxy_bp = Blueprint('proxy', __name__)

@proxy_bp.route('/js/warranty-embed.js')
def serve_warranty_embed():
    """Serve the warranty embed JavaScript file"""
    resp = send_from_directory(
        os.path.join(current_app.root_path, 'static', 'js'),
        'warranty-embed.js',
        mimetype='application/javascript'
    )
    # Prevent caching so storefront always gets latest
    try:
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
    except Exception:
        pass
    return resp

@proxy_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return {'status': 'healthy', 'service': 'flex-warranty-api'}, 200 


# ---------------- App Proxy security -----------------
def _verify_app_proxy_signature() -> bool:
    """Verify Shopify App Proxy signature.
    Accepts either 'signature' (App Proxy) or 'hmac' (standard) param.
    Also enforces a timestamp tolerance when provided.
    """
    try:
        # Keep original params for later, but derive signature values first
        params = request.args.to_dict(flat=True)
        provided_sig = params.get('signature')
        provided_hmac = params.get('hmac')

        # Optional timestamp freshness check
        ts = params.get('timestamp')
        if ts and str(ts).isdigit():
            if abs(int(time.time()) - int(ts)) > 300:
                return False

        secret = (Config.SHOPIFY_API_SECRET or '').encode('utf-8')
        # Reconstruct the App Proxy base string exactly as Shopify expects:
        # base_string = original_path + '?' + original_query_without_signature
        raw_qs = request.query_string.decode('utf-8') if request.query_string else ''
        # remove signature/hmac parameters preserving order
        import re
        qs_no_sig = re.sub(r'(^|&)(signature|hmac)=[^&]*', '', raw_qs).strip('&')

        # original path the customer requested (prefix + relative path)
        rel_path = request.path
        if rel_path.startswith('/api'):
            rel_path = rel_path[4:] or '/'
        orig_prefix = params.get('path_prefix') or Config.APP_PROXY_PREFIX or ''
        orig_path = f"{orig_prefix}{rel_path}"
        base_bytes = f"{orig_path}?{qs_no_sig}".encode('utf-8') if qs_no_sig else f"{orig_path}".encode('utf-8')

        if provided_sig:
            sig_calc = hmac.new(secret, base_bytes, hashlib.sha256).hexdigest()
            if hmac.compare_digest(sig_calc, provided_sig):
                return True

        # Fallback: standard hmac over sorted params (used in some docs/samples)
        items = sorted((k, v) for k, v in params.items() if k not in ('signature','hmac'))
        canonical_qs = '&'.join([f"{k}={v}" for k, v in items])
        if provided_hmac:
            hmac_calc = hmac.new(secret, canonical_qs.encode('utf-8'), hashlib.sha256).hexdigest()
            if hmac.compare_digest(hmac_calc, provided_hmac):
                return True

        return False
    except Exception:
        return False


def require_app_proxy_auth(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
            # Primary: strict signature verification
        if not _verify_app_proxy_signature():
            # Fallback for non-sensitive endpoints when coming via App Proxy
            if request.method == 'GET' or request.path.endswith('/events') or request.path.endswith('/pricing/select'):
                shop_param = request.args.get('shop')
                if shop_param:
                    with get_db() as db:
                        known = db.execute(text('SELECT 1 FROM shops WHERE shop_url = :s'), { 's': shop_param }).first()
                        if known:
                            return func(*args, **kwargs)
            return jsonify({'error': 'Unauthorized'}), 401
        return func(*args, **kwargs)
    return wrapper


@proxy_bp.route('/pricing/options', methods=['GET'])
@require_app_proxy_auth
def pricing_options():
    """Return available pricing options for a product price and category tag.
    Query params: shop, price, category_tag (flexprotect_cat<ID>)
    """
    try:
        price_raw = request.args.get('price')
        category_tag = request.args.get('category_tag')
        if price_raw is None or category_tag is None:
            return jsonify({'error': 'Missing price or category_tag'}), 400
        try:
            product_price = float(price_raw)
        except ValueError:
            return jsonify({'error': 'Invalid price'}), 400

        # Resolve category tag to name via DB
        with get_db() as db:
            cid = None
            import re
            m = re.match(r'^flexprotect_cat(\d+)$', category_tag.strip())
            if m:
                cid = int(m.group(1))
            category_name = None
            if cid is not None:
                row = db.execute(text('SELECT product_category, includes_adh FROM warranty_insurance_products WHERE id = :id AND is_active = true'), { 'id': cid }).mappings().first()
                if row:
                    category_name = row['product_category']

        if not category_name:
            return jsonify({'error': 'Unknown category tag'}), 400

        pricing = get_all_warranty_pricing_options(product_price, category_name)
        if not pricing:
            return jsonify({'error': 'No pricing available'}), 404
        # Generate a short server-issued session hint for stable variant naming/analytics
        session_hint = uuid.uuid4().hex[:8]
        return jsonify({ 'product_category': category_name, 'includes_adh': pricing['includes_adh'], 'options': pricing['options'], 'session_hint': session_hint })
    except Exception as e:
        current_app.logger.error(f"pricing_options error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@proxy_bp.route('/pricing/select', methods=['GET','POST'])
@require_app_proxy_auth
def pricing_select():
    """Select a protection option; create a session-scoped variant and return variant_id.
    Body: { session_token, product_id, price, term, category_tag }
    Query contains 'shop' from app proxy.
    """
    try:
        if request.method == 'GET':
            session_token = request.args.get('session_token','')
            product_id = request.args.get('product_id')
            price = float(request.args.get('price') or 0)
            term = int(request.args.get('term') or 2)
        else:
            data = request.get_json(silent=True) or {}
            if not data and request.form:
                # Accept form-encoded fallback: payload=<json>
                try:
                    raw = request.form.get('payload')
                    if raw:
                        import json as _json
                        data = _json.loads(raw)
                except Exception:
                    data = {}
            session_token = str(data.get('session_token') or '')
            product_id = data.get('product_id')  # original product id (for analytics only)
            price = float(data.get('price') or 0)
            term = int(data.get('term') or 2)
        shop_domain = request.args.get('shop')
        if not shop_domain or not session_token or price <= 0:
            return jsonify({'error': 'Missing required fields'}), 400

        # Load shop creds
        with get_db() as db:
            shop = db.execute(text('SELECT id, access_token, product_id FROM shops WHERE shop_url = :s'), { 's': shop_domain }).mappings().first()
            if not shop or not shop.get('access_token') or not shop.get('product_id'):
                return jsonify({'error': 'Shop not configured'}), 400

        # Create a new variant for this session (Admin GraphQL productVariantsBulkCreate)
        try:
            import requests
            token = shop['access_token']
            warranty_product_gid = shop['product_id']
            # Derive a stable short token segment from session_token; if missing, generate UUID
            # Prefer explicit session_hint from client/options; else hash session_token; else random
            base_token = request.args.get('session_hint') or session_token or uuid.uuid4().hex
            token_hash = hashlib.sha1(base_token.encode('utf-8')).hexdigest()[:8]
            option_value = f"Protection - {token_hash} - {term}yr"
            mutation = '''
            mutation($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
              productVariantsBulkCreate(productId: $productId, variants: $variants) {
                productVariants { id title price inventoryPolicy inventoryItem { id tracked } }
                userErrors { field message }
              }
            }
            '''
            # First try optionValues (works across Admin API versions)
            variables = {
                'productId': warranty_product_gid,
                'variants': [
                    {
                        'optionValues': [ { 'optionName': 'Title', 'name': option_value } ],
                        'price': str(price),
                        'inventoryPolicy': 'CONTINUE',
                        'inventoryItem': { 'tracked': False },
                    }
                ]
            }
            resp = requests.post(
                f"https://{shop_domain}/admin/api/2025-07/graphql.json",
                headers={ 'X-Shopify-Access-Token': token, 'Content-Type': 'application/json' },
                json={ 'query': mutation, 'variables': variables },
                timeout=10,
            )
            if resp.status_code != 200:
                try:
                    return jsonify({'error': 'Shopify API error', 'status': resp.status_code, 'body': resp.text}), 502
                except Exception:
                    return jsonify({'error': 'Shopify API error'}), 502
            j = resp.json()
            errs = j.get('data', {}).get('productVariantsBulkCreate', {}).get('userErrors')
            if errs:
                # If variant already exists for this token+term, look it up and return id instead of failing
                joined = '; '.join([e.get('message','') for e in errs])
                if 'already exists' in joined.lower():
                    lookup_q = '''
                    query($id: ID!, $query: String!) {
                      product(id: $id) {
                        variants(first: 50, query: $query) { edges { node { id title } } }
                      }
                    }
                    '''
                    qvars = { 'id': warranty_product_gid, 'query': f"title:'{option_value}'" }
                    lr = requests.post(
                        f"https://{shop_domain}/admin/api/2025-07/graphql.json",
                        headers={ 'X-Shopify-Access-Token': token, 'Content-Type': 'application/json' },
                        json={ 'query': lookup_q, 'variables': qvars },
                        timeout=10,
                    )
                    if lr.status_code == 200:
                        lj = lr.json()
                        edges = (((lj or {}).get('data') or {}).get('product') or {}).get('variants', {}).get('edges', [])
                        if edges:
                            vid = edges[0]['node']['id']
                            # Ensure price and inventory flags on existing variant
                            try:
                                upd_mut = '''
                                mutation($id: ID!, $input: ProductVariantInput!) {
                                  productVariantUpdate(id: $id, input: $input) {
                                    productVariant { id price inventoryPolicy inventoryItem { tracked } }
                                    userErrors { field message }
                                  }
                                }
                                '''
                                upd_vars = { 'id': vid, 'input': { 'price': f"{price:.2f}", 'inventoryPolicy': 'CONTINUE', 'inventoryItem': { 'tracked': False } } }
                                requests.post(
                                    f"https://{shop_domain}/admin/api/2025-07/graphql.json",
                                    headers={ 'X-Shopify-Access-Token': token, 'Content-Type': 'application/json' },
                                    json={ 'query': upd_mut, 'variables': upd_vars },
                                    timeout=10,
                                )
                            except Exception:
                                pass
                            return jsonify({ 'variant_id': vid, 'title': option_value, 'price': str(price), 'term': term })
                # Fallback: some shops accept 'options' (single value array)
                try:
                    fallback_vars = {
                        'productId': warranty_product_gid,
                        'variants': [ { 'options': [ option_value ], 'price': str(price), 'inventoryPolicy': 'CONTINUE', 'inventoryItem': { 'tracked': False } } ]
                    }
                    resp2 = requests.post(
                        f"https://{shop_domain}/admin/api/2025-07/graphql.json",
                        headers={ 'X-Shopify-Access-Token': token, 'Content-Type': 'application/json' },
                        json={ 'query': mutation, 'variables': fallback_vars },
                        timeout=10,
                    )
                    if resp2.status_code == 200:
                        j2 = resp2.json()
                        errs2 = j2.get('data', {}).get('productVariantsBulkCreate', {}).get('userErrors')
                        if not errs2:
                            created2 = j2.get('data', {}).get('productVariantsBulkCreate', {}).get('productVariants') or []
                            if created2:
                                v2 = created2[0]
                                return jsonify({ 'variant_id': v2['id'], 'title': v2['title'], 'price': v2.get('price'), 'term': term })
                except Exception:
                    pass
                return jsonify({'error': joined, 'details': errs}), 400
            created = j.get('data', {}).get('productVariantsBulkCreate', {}).get('productVariants') or []
            variant = created[0] if created else None
            if not variant:
                return jsonify({'error': 'Failed to create variant', 'body': j}), 500
            # Ensure price/inventory flags on newly created variant
            try:
                upd_mut = '''
                mutation($id: ID!, $input: ProductVariantInput!) {
                  productVariantUpdate(id: $id, input: $input) {
                    productVariant { id price inventoryPolicy inventoryItem { tracked } }
                    userErrors { field message }
                  }
                }
                '''
                upd_vars = { 'id': variant['id'], 'input': { 'price': f"{price:.2f}", 'inventoryPolicy': 'CONTINUE', 'inventoryItem': { 'tracked': False } } }
                requests.post(
                    f"https://{shop_domain}/admin/api/2025-07/graphql.json",
                    headers={ 'X-Shopify-Access-Token': token, 'Content-Type': 'application/json' },
                    json={ 'query': upd_mut, 'variables': upd_vars },
                    timeout=10,
                )
            except Exception:
                pass
            # Record protection variant for analytics/attribution if table exists
            try:
                with get_db() as db:
                    db.execute(text('''
                        insert into protection_variants (shop_id, variant_gid, product_gid, session_id, term, price, category_tag)
                        values (:sid, :vgid, :pgid, :sess, :term, :price, :ctag)
                        on conflict (shop_id, variant_gid) do nothing
                    '''), {
                        'sid': shop['id'],
                        'vgid': variant['id'],
                        'pgid': warranty_product_gid,
                        'sess': token_hash,
                        'term': term,
                        'price': price,
                        'ctag': request.args.get('category_tag'),
                    })
                    db.commit()
            except Exception:
                pass
            return jsonify({ 'variant_id': variant['id'], 'title': variant['title'], 'price': variant.get('price'), 'term': term })
        except Exception as e:
            current_app.logger.error(f"pricing_select error: {e}")
            return jsonify({'error': 'Failed to create variant'}), 500
    except Exception as e:
        current_app.logger.error(f"pricing_select outer error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@proxy_bp.route('/pricing/config', methods=['GET'])
@require_app_proxy_auth
def pricing_config():
    """Return enabled offer placements for the shop (effective by type)."""
    try:
        shop_domain = request.args.get('shop')
        if not shop_domain:
            return jsonify({'error': 'Missing shop'}), 400
        theme = None
        with get_db() as db:
            shop = db.execute(text('SELECT id FROM shops WHERE shop_url = :s'), { 's': shop_domain }).mappings().first()
            if not shop:
                return jsonify({'error': 'Shop not found'}), 404
            sid = shop['id']
            # Prefer shop-specific templates/configs but fall back to global (shop_id=0)
            rows = db.execute(text('''
                with effective_templates as (
                    select distinct on (type) id, type from offer_templates
                    where is_active = true and (shop_id = :sid or shop_id = 0)
                    order by type, case when shop_id = :sid then 0 else 1 end
                )
                select et.type, coalesce(oc.enabled, true) as enabled
                from effective_templates et
                left join offer_configs oc on oc.template_id = et.id and oc.shop_id = :sid
            '''), { 'sid': sid }).mappings().all()

            th = db.execute(text('''
                select id, text_color, background_color, button_color, chip_bg, chip_text, font_family
                from offer_themes
                where shop_id = :sid and (is_default = true)
                order by updated_at desc nulls last
                limit 1
            '''), { 'sid': sid }).mappings().first()
            if th:
                theme = {
                    'textColor': th.get('text_color'),
                    'backgroundColor': th.get('background_color'),
                    'buttonColor': th.get('button_color'),
                    'chipColor': th.get('chip_bg'),
                    'chipTextColor': th.get('chip_text'),
                    'fontFamily': th.get('font_family'),
                }
        enabled_by_type = { r['type']: bool(r['enabled']) for r in rows }
        # Default off if no rows
        for t in ['offer_modal','product_page','cart','learn_more']:
            enabled_by_type.setdefault(t, False)
        return jsonify({ 'enabled': enabled_by_type, 'theme': theme })
    except Exception as e:
        current_app.logger.error(f"pricing_config error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@proxy_bp.route('/events', methods=['POST'])
@require_app_proxy_auth
def proxy_events():
    """Capture lightweight analytics events from storefront."""
    try:
        data = request.get_json(silent=True) or {}
        shop_domain = request.args.get('shop')
        event_type = str(data.get('type') or 'unknown')
        session_token = str(data.get('session_token') or '')
        payload = data.get('payload') or {}
        with get_db() as db:
            # Map to existing schema: session_id, metadata(jsonb), timestamp defaults
            db.execute(text('''
                insert into offer_events (shop_id, event_type, session_id, metadata)
                select s.id, :etype, :stoken, CAST(:payload AS JSONB) from shops s where s.shop_url = :shop
            '''), { 'etype': event_type, 'stoken': session_token, 'payload': json.dumps(payload), 'shop': shop_domain })
            db.commit()
        return jsonify({ 'ok': True })
    except Exception as e:
        current_app.logger.error(f"proxy_events error: {e}")
        return jsonify({ 'ok': False }), 200

@proxy_bp.route('/storefront-token', methods=['GET'])
@require_app_proxy_auth
def storefront_token():
    """Return Storefront API token for this shop via App Proxy."""
    try:
        token = os.environ.get('STOREFRONT_API_TOKEN') or ''
        if not token:
            return jsonify({ 'error': 'missing token' }), 500
        return jsonify({ 'ok': True, 'token': token })
    except Exception as e:
        current_app.logger.error(f"storefront_token error: {e}")
        return jsonify({ 'error': 'Internal server error' }), 500