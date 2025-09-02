from flask import Blueprint, request, jsonify
from sqlalchemy import text
from ..utils.auth import require_auth, get_shop_context
from ..models.database import get_db

templates_bp = Blueprint('templates', __name__)


@templates_bp.route('/offer-templates', methods=['GET', 'OPTIONS'])
@require_auth
def list_templates():
    ctx = get_shop_context()
    ttype = request.args.get('type')
    sql = 'SELECT id, shop_id, type, name, description, template_json, css_overrides, is_active, created_at, updated_at FROM offer_templates WHERE shop_id IN (0, :sid)'
    params = {'sid': ctx['shop_id']}
    if ttype:
        sql += ' AND type = :type'
        params['type'] = ttype
    sql += ' ORDER BY type, (shop_id = :sid) DESC, name'
    with get_db() as db:
        rows = db.execute(text(sql), params).mappings().all()
        return jsonify({'templates': [dict(r) for r in rows]}), 200


@templates_bp.route('/offer-templates/effective', methods=['GET', 'OPTIONS'])
@require_auth
def list_effective_templates():
    ctx = get_shop_context()
    with get_db() as db:
        rows = db.execute(text('''
            SELECT DISTINCT ON (type, name)
              id, shop_id, type, name, description,
              template_json, css_overrides, is_active, created_at, updated_at,
              styles_css, content_html, container_html, script_js
            FROM offer_templates
            WHERE shop_id IN (0, :sid) AND is_active = true
            ORDER BY type, name, (shop_id = :sid) DESC, id
        '''), {'sid': ctx['shop_id']}).mappings().all()
        out = []
        for r in rows:
            row = dict(r)
            try:
                tj = row.get('template_json')
                if isinstance(tj, str):
                    import json as _json
                    tj = _json.loads(tj)
            except Exception:
                tj = {}
            if not isinstance(tj, dict):
                tj = {}
            # Assemble HTML from fragments when present
            styles = row.get('styles_css') or ''
            content = row.get('content_html') or ''
            container = row.get('container_html') or ''
            html_body = (container.replace('{content}', content) if container else content) or ''
            full_html = (f"<style>{styles}</style>" + html_body) if styles else html_body
            if full_html:
                tj['html'] = full_html
            row['template_json'] = tj
            out.append(row)
        return jsonify({'templates': out}), 200


@templates_bp.route('/offer-templates/stock', methods=['PUT', 'OPTIONS'])
@require_auth
def update_stock_template():
    """Update the stock (shop_id=0) template HTML for a given surface.
    Query: type=offer_modal|product_page|learn_more
    Body: { html: string }
    """
    ttype = (request.args.get('type') or '').strip().lower()
    if ttype not in ('offer_modal','product_page','learn_more'):
        return jsonify({'error': 'invalid type'}), 400
    try:
        data = request.get_json(silent=True) or {}
        html = data.get('html') if isinstance(data, dict) else None
        # Fallbacks for Postman/form-data or raw text
        if (not html) and request.form:
            html = request.form.get('html')
        if (not html) and request.data:
            try:
                html = request.data.decode('utf-8')
            except Exception:
                html = None
        if not isinstance(html, str) or not html.strip():
            return jsonify({'error': 'missing html'}), 400
        with get_db() as db:
            # Upsert stock row for type
            row = db.execute(text('''
                SELECT id FROM offer_templates
                WHERE shop_id = 0 AND lower(type::text) = :t
                ORDER BY updated_at DESC NULLS LAST, id DESC
                LIMIT 1
            '''), {'t': ttype}).mappings().first()
            if row:
                db.execute(text('''
                    UPDATE offer_templates
                    SET template_json = jsonb_set(
                        COALESCE(CASE WHEN jsonb_typeof(template_json::jsonb)='object' THEN template_json::jsonb ELSE '{}'::jsonb END,'{}'::jsonb),
                        '{html}', to_jsonb(:html::text), true
                    ),
                        updated_at = now(), is_active = true
                    WHERE id = :id
                '''), {'html': html, 'id': row['id']})
            else:
                db.execute(text('''
                    INSERT INTO offer_templates (shop_id, type, name, description, template_json, is_active)
                    VALUES (0, :type::offer_template_type, :name, :desc, jsonb_build_object('html', :html::text), true)
                '''), {
                    'type': ttype,
                    'name': f"Default {ttype.replace('_',' ').title()}",
                    'desc': 'Stock template',
                    'html': html,
                })
            db.commit()
        return jsonify({'ok': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

