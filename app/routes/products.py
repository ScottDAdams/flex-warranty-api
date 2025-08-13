from flask import Blueprint, request, jsonify, Response, stream_with_context
from sqlalchemy import text
from ..utils.auth import require_auth, get_shop_context
from ..models.database import get_db
import requests
import os, json

products_bp = Blueprint('products', __name__)


def _shopify_graphql(shop_url: str, access_token: str, query: str, variables: dict | None = None):
    url = f"https://{shop_url}/admin/api/2024-01/graphql.json"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json",
    }
    resp = requests.post(url, json={"query": query, "variables": variables or {}}, headers=headers, timeout=30)
    return resp


def _get_shop_tokens(shop_id: int):
    with get_db() as db:
        row = db.execute(text('SELECT shop_url, access_token FROM shops WHERE id = :id'), {"id": shop_id}).mappings().first()
        return (row['shop_url'], row['access_token'])


@products_bp.route('/products/list', methods=['GET', 'OPTIONS'])
@require_auth
def list_products():
    ctx = get_shop_context()
    shop_url, access_token = _get_shop_tokens(ctx['shop_id'])
    # Pagination
    limit = max(1, min(int(request.args.get('limit', 50)), 250))
    cursor = request.args.get('cursor')
    # Exclude vendor Flex Protect using search syntax: -vendor:"Flex Protect"
    query = '-vendor:"Flex Protect"'
    gql = '''
    query($first:Int!, $after:String, $query:String!) {
      products(first:$first, after:$after, query:$query) {
        pageInfo { hasNextPage endCursor }
        edges { node { id title vendor productType handle tags bodyHtml } }
      }
    }
    '''
    if not access_token:
        return jsonify({"error": "Shop access token not found"}), 401
    r = _shopify_graphql(shop_url, access_token, gql, {"first": limit, "after": cursor, "query": query})
    if r.status_code != 200:
        return jsonify({"error": "Shopify error", "status": r.status_code, "body": r.text}), 502
    data = r.json()
    if data.get('errors') or data.get('data') is None:
        return jsonify({"error": "Shopify GraphQL returned errors", "body": data}), 502
    edges = data.get('data', {}).get('products', {}).get('edges', [])
    page_info = data.get('data', {}).get('products', {}).get('pageInfo', {})
    items = [e['node'] for e in edges]
    return jsonify({"items": items, "pageInfo": page_info}), 200


@products_bp.route('/products/categories', methods=['GET', 'OPTIONS'])
@require_auth
def list_categories():
    with get_db() as db:
        rows = db.execute(text('SELECT id, product_category FROM warranty_insurance_products WHERE is_active = true ORDER BY id')).mappings().all()
        return jsonify({"categories": [dict(r) for r in rows]}), 200


def _get_product_tags(shop_url: str, token: str, product_id: str) -> list[str]:
    q = '''query($id:ID!){ product(id:$id){ tags } }'''
    r = _shopify_graphql(shop_url, token, q, {"id": product_id})
    try:
        return r.json()['data']['product']['tags'] or []
    except Exception:
        return []


def _tags_add(shop_url: str, token: str, product_id: str, tags: list[str]):
    if not tags:
        return
    m = '''mutation($id:ID!, $tags:[String!]!){ tagsAdd(id:$id, tags:$tags){ userErrors{field message} } }'''
    _shopify_graphql(shop_url, token, m, {"id": product_id, "tags": tags})


def _tags_remove(shop_url: str, token: str, product_id: str, tags: list[str]):
    if not tags:
        return
    m = '''mutation($id:ID!, $tags:[String!]!){ tagsRemove(id:$id, tags:$tags){ userErrors{field message} } }'''
    _shopify_graphql(shop_url, token, m, {"id": product_id, "tags": tags})


@products_bp.route('/products/tag', methods=['POST', 'OPTIONS'])
@require_auth
def tag_product():
    ctx = get_shop_context()
    shop_url, token = _get_shop_tokens(ctx['shop_id'])
    data = request.get_json() or {}
    product_id = data.get('productId')
    enable = bool(data.get('enable', False))
    category_id = data.get('categoryId')
    if not product_id:
        return jsonify({"error": "Missing productId"}), 400

    if enable and (category_id is None):
        return jsonify({"error": "categoryId required when enable=true"}), 400
    current = _get_product_tags(shop_url, token, product_id)
    # Atomic remove + add
    remove = [t for t in (current or []) if t.startswith('flexprotect_cat') or t in {'flexprotect_on','flexprotect_off'}]
    add = []
    if category_id is not None:
        add.append(f'flexprotect_cat{int(category_id)}')
    add.append('flexprotect_on' if enable else 'flexprotect_off')
    if remove:
        _tags_remove(shop_url, token, product_id, list(set(remove)))
    if add:
        _tags_add(shop_url, token, product_id, list(set(add)))
    return jsonify({"ok": True}), 200


# Deterministic classifier per business rules
def _deterministic_classify(categories: list[dict], title: str, body: str, vendor: str, product_type: str, tags: list[str], general_category_id: int | None) -> tuple[int | None, bool, bool]:
    text = f"{title} {body} {vendor} {product_type} {' '.join(tags or [])}".lower()
    # Find general category id if not provided
    def get_general_id():
        if general_category_id:
            return general_category_id
        ce = next((c for c in categories if c['product_category'].lower() == 'consumer electronics'), None)
        return ce['id'] if ce else None

    # Map specific categories (excluding general) to keyword sets
    name_to_id = {c['product_category'].lower(): c['id'] for c in categories}
    general_id = get_general_id()
    specific_categories = [c for c in categories if c['id'] != general_id]

    # Helper to find category id by alias list (robust to punctuation/spacing)
    def norm(s: str) -> str:
        return ''.join(ch for ch in s.lower() if ch.isalnum())
    norm_map = {norm(c['product_category']): c['id'] for c in categories}
    def cat_id(aliases: list[str]) -> int | None:
        for a in aliases:
            nid = norm_map.get(norm(a))
            if nid:
                return nid
        return None

    tv_id = cat_id(['TVs','Television','TV'])
    laptop_id = cat_id(['Desktops, Laptops','Desktops Laptops','Laptops','Laptop'])

    base_mapping: dict[str, set[str]] = {
        'tvs': {' tv', 'television', 'oled', 'qled', 'uhd', '4k tv', 'roku tv', 'fire tv', 'smart tv'},
        'desktops, laptops': {'laptop', 'notebook', 'macbook', 'chromebook', 'desktop', 'pc', 'imac'},
        'tablets': {'tablet', 'ipad', 'galaxy tab', 'fire tablet'},
        'camera': {'camera', 'dslr', 'mirrorless', 'point and shoot'},
        'headphones': {'headphone', 'headphones'},
        'earbuds': {'earbuds', 'ear bud', 'in-ear', 'in ear'},
        'speaker': {'speaker', 'soundbar', 'smart speaker', 'bluetooth speaker'},
        'smartwatch': {'smartwatch', 'watch band', 'apple watch', 'galaxy watch'},
        'vr headset': {'vr headset', 'oculus', 'quest', 'vive'},
        'streaming device': {'streaming stick', 'roku', 'chromecast', 'apple tv'},
        'router': {'router', 'wifi 6', 'wi-fi 6', 'mesh'},
        'thermostat': {'thermostat', 'nest', 'ecobee'},
        'mouse': {'mouse', 'gaming mouse'},
        'keyboard': {'keyboard', 'mechanical keyboard'},
        'monitor': {'monitor', 'display'},
        'projector': {'projector'},
        'printer': {'printer'},
        'smart display': {'smart display', 'echo show'},
        'smart light': {'smart light', 'smart bulb', 'hue bulb', 'hue light', 'bulb'},
        'console': {'playstation', 'xbox', 'nintendo switch', 'switch console'},
        'drone': {'drone', 'quadcopter'},
    }

    # Prefer direct alias-based checks for critical categories
    if tv_id and any(kw in text for kw in {' tv', 'television', 'smart tv', '4k tv', 'qled', 'oled'}):
        return (tv_id, True, True)
    if laptop_id and any(kw in text for kw in {'laptop', 'notebook', 'macbook', 'chromebook'}):
        return (laptop_id, True, True)

    # Alias-driven matching per category (excluding general)
    for cat in specific_categories:
        aliases = cat.get('aliases') or []
        for alias in aliases:
            if alias and alias.lower() in text:
                return (cat['id'], True, True)

    # Try explicit mapping using base_mapping and category names present
    for cat in specific_categories:
        cname = cat['product_category'].lower()
        # Prefer normalized keys from base_mapping when they match a category name
        for key, kws in base_mapping.items():
            if key in cname:
                if any(kw in text for kw in kws):
                    return (cat['id'], True, True)
        # As a fallback, if any meaningful token from the category name appears in text
        simple_tokens = [t for t in cname.replace(',', ' ').split() if len(t) > 3 and t not in {'desktops', 'laptops', 'and'}]
        if any(tok in text for tok in simple_tokens):
            return (cat['id'], True, True)

    # Electronics indicator → general category
    electronics_terms = set().union(*base_mapping.values())
    electronics_terms.update({'smart', 'bluetooth', 'usb', 'wifi', 'wi-fi', 'charger', 'gaming', 'dock'})
    is_electronic = any(term in text for term in electronics_terms)
    if is_electronic:
        # Ambiguous electronic: would be general; signal for OpenAI fallback by returning (None, True)
        return (None, True, False)

    # Not an electronic device
    return (None, False, False)


def _classify_with_openai(categories: list[dict], title: str, body: str, vendor: str, product_type: str, tags: list[str], intro: str | None = None, general_category_id: int | None = None):
    api_key = os.environ.get('OPENAI_API_KEY')
    # fallback heuristic
    def heuristic():
        text = f"{title} {body} {vendor} {product_type} {' '.join(tags or [])}".lower()
        # 1) specific category shortcuts
        # build lookup by name
        name_to_id = {c['product_category'].lower(): c['id'] for c in categories}
        # desktops/laptops
        dl_keywords = ['laptop','notebook','macbook','chromebook','desktop','pc','imac','gaming pc','mini pc']
        if any(k in text for k in dl_keywords) and 'desktops, laptops' in name_to_id:
            return name_to_id['desktops, laptops']
        # tablets
        tb_keywords = ['tablet','ipad','galaxy tab','fire tablet']
        if any(k in text for k in tb_keywords) and 'tablets' in name_to_id:
            return name_to_id['tablets']
        # tvs
        tv_keywords = [' tv','television','smart tv','oled','qled','uhd','4k tv','roku tv','fire tv']
        if any(k in text for k in tv_keywords) and 'tvs' in name_to_id:
            return name_to_id['tvs']
        # 2) generic electronics keywords -> Consumer Electronics if present
        generic_terms = [
            'router','thermostat','bulb','light','smart light','smart bulb','drone','camera','doorbell','speaker','soundbar',
            'earbuds','headphones','smartwatch','fitness tracker','streaming stick','roku','chromecast','bluetooth speaker',
            'mouse','keyboard','headset','vr headset','smart display','nest','echo'
        ]
        if any(term in text for term in generic_terms):
            if general_category_id:
                return general_category_id
            ce = next((c for c in categories if c['product_category'].lower() == 'consumer electronics'), None)
            return ce['id'] if ce else None
        return None
    if not api_key:
        return heuristic()
    try:
        import json
        cat_names = [c['product_category'] for c in categories]
        specific = [n for n in cat_names if n.lower() != 'consumer electronics']
        specific_list = ", ".join(specific) if specific else ", ".join(cat_names)
        intro_text = (intro + "\n") if intro else ""
        prompt = {
            "role": "system",
            "content": (
                f"{intro_text}"
                "You are a product classifier for warranty categories. Given a Shopify product, pick exactly one category id from the provided list, or null if not eligible.\n"
                "Rules:\n"
                f"- Prefer the most specific matching category among: {specific_list} when it fits.\n"
                "- Use 'Consumer Electronics' only as a catch-all for products that are clearly electronic devices but do not strongly match a more specific category.\n"
                "- If the product is not an electronic device (e.g., clothing, food, decor), return category_id: null and enable: false.\n"
                "- Exactly one category; no multi-select.\n"
                "Return strict JSON: {\"category_id\": number|null, \"enable\": boolean} with no extra fields."
            )
        }
        user = {
            "role": "user",
            "content": (
                f"categories: {[{'id': c['id'], 'name': c['product_category']} for c in categories]}\n"
                f"title: {title}\nvendor: {vendor}\nproduct_type: {product_type}\n"
                f"tags: {tags}\nbody: {body[:2000]}"
            )
        }
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "messages": [prompt, user],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
            },
            timeout=30,
        )
        j = resp.json()
        content = j['choices'][0]['message']['content']
        obj = json.loads(content)
        cid = obj.get('category_id')
        if cid is None:
            # OpenAI abstained; apply heuristic fallback
            return heuristic()
        return int(cid)
    except Exception:
        return heuristic()


@products_bp.route('/products/evaluate', methods=['POST', 'OPTIONS'])
@require_auth
def evaluate_products():
    ctx = get_shop_context()
    shop_url, token = _get_shop_tokens(ctx['shop_id'])
    body = request.get_json() or {}
    clean_sweep = bool(body.get('cleanSweep', False))

    # Load active categories once
    with get_db() as db:
        cats = db.execute(text('SELECT id, product_category, COALESCE(aliases, ARRAY[]::text[]) AS aliases FROM warranty_insurance_products WHERE is_active = true')).mappings().all()
        categories = [dict(c) for c in cats]
        gp = db.execute(text('SELECT general_category_id FROM evaluation_prompts WHERE shop_id = :sid'), { 'sid': ctx['shop_id'] }).mappings().first()
        general_id = gp.get('general_category_id') if gp else None

    def generate():
        # 1) Collect product ids to process (up to 2000)
        total = 0
        to_process = []
        cursor = None
        while total < 2000:
            q = '''
            query($first:Int!, $after:String, $query:String!){
              products(first:$first, after:$after, query:$query){
                pageInfo{ hasNextPage endCursor }
                edges{ node{ id title vendor productType tags bodyHtml } }
              }
            }
            '''
            search = '-vendor:"Flex Protect"'
            if not clean_sweep:
                search += ' AND -tag:flexprotect_on AND -tag:flexprotect_off'
            r = _shopify_graphql(shop_url, token, q, {"first": 50, "after": cursor, "query": search})
            if r.status_code != 200:
                yield json.dumps({"error": "shopify", "status": r.status_code}) + "\n"
                break
            d = r.json()
            edges = d.get('data', {}).get('products', {}).get('edges', [])
            for e in edges:
                if total >= 2000:
                    break
                to_process.append(e['node'])
                total += 1
            page = d.get('data', {}).get('products', {}).get('pageInfo', {})
            if not page.get('hasNextPage') or total >= 2000:
                break
            cursor = page.get('endCursor')

        yield json.dumps({"total": total}) + "\n"

        # 2) Process one by one
        idx = 0
        for p in to_process:
            idx += 1
            try:
                cid, enable, confident = _deterministic_classify(categories, p.get('title') or '', p.get('bodyHtml') or '', p.get('vendor') or '', p.get('productType') or '', p.get('tags') or [], general_id)
                # If not confident and would otherwise fall to general, try OpenAI for specificity
                if enable and cid is None:
                    maybe = _classify_with_openai(categories, p.get('title') or '', p.get('bodyHtml') or '', p.get('vendor') or '', p.get('productType') or '', p.get('tags') or [], body.get('promptIntro') if isinstance(body, dict) else None, general_id)
                    if isinstance(maybe, int):
                        cid = maybe
                    else:
                        cid = general_id
                current = _get_product_tags(shop_url, token, p['id'])
                # Compute atomic remove/add sets
                remove = [t for t in (current or []) if t.startswith('flexprotect_cat') or t in {'flexprotect_on','flexprotect_off'}]
                add = []
                if cid:
                    add.append(f'flexprotect_cat{cid}')
                add.append('flexprotect_on' if enable else 'flexprotect_off')

                # Perform in fixed order: remove once, add once
                if remove:
                    _tags_remove(shop_url, token, p['id'], list(set(remove)))
                if add:
                    _tags_add(shop_url, token, p['id'], list(set(add)))
                yield json.dumps({"productId": p['id'], "index": idx, "total": total, "categoryId": cid, "enabled": enable, "title": p.get('title')}) + "\n"
            except Exception as e:
                yield json.dumps({"productId": p.get('id'), "index": idx, "total": total, "error": str(e)}) + "\n"

        yield json.dumps({"done": True, "count": idx}) + "\n"

    return Response(stream_with_context(generate()), mimetype='application/x-ndjson')


@products_bp.route('/products/clear-tags', methods=['POST', 'OPTIONS'])
@require_auth
def clear_flex_tags():
    """Remove all Flex Protect tags from all non-Flex Protect products.
    Tags removed: flexprotect_on, flexprotect_off, any flexprotect_cat*
    Streams NDJSON progress: {index,total,productId,removed:[...]}.
    """
    ctx = get_shop_context()
    shop_url, token = _get_shop_tokens(ctx['shop_id'])

    def generate():
        total = 0
        ids = []
        cursor = None
        # Collect product ids
        while True:
            q = '''
            query($first:Int!, $after:String, $query:String!){
              products(first:$first, after:$after, query:$query){
                pageInfo{ hasNextPage endCursor }
                edges{ node{ id title } }
              }
            }
            '''
            search = '-vendor:"Flex Protect"'
            r = _shopify_graphql(shop_url, token, q, {"first": 100, "after": cursor, "query": search})
            if r.status_code != 200:
                yield json.dumps({"error": "shopify", "status": r.status_code}) + "\n"
                break
            d = r.json()
            edges = d.get('data', {}).get('products', {}).get('edges', [])
            for e in edges:
                ids.append(e['node']['id'])
            page = d.get('data', {}).get('products', {}).get('pageInfo', {})
            if not page.get('hasNextPage'):
                break
            cursor = page.get('endCursor')

        total = len(ids)
        yield json.dumps({"total": total}) + "\n"

        idx = 0
        for pid in ids:
            idx += 1
            try:
                current = _get_product_tags(shop_url, token, pid)
                to_remove = [t for t in (current or []) if t == 'flexprotect_on' or t == 'flexprotect_off' or t.startswith('flexprotect_cat')]
                if to_remove:
                    _tags_remove(shop_url, token, pid, list(set(to_remove)))
                yield json.dumps({"index": idx, "total": total, "productId": pid, "removed": to_remove}) + "\n"
            except Exception as e:
                yield json.dumps({"index": idx, "total": total, "productId": pid, "error": str(e)}) + "\n"

        yield json.dumps({"done": True, "count": idx}) + "\n"

    return Response(stream_with_context(generate()), mimetype='application/x-ndjson')

