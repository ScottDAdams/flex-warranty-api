from flask import Blueprint, request, jsonify
import json
from sqlalchemy import text
from ..utils.auth import require_auth, get_shop_context
from ..models.database import get_db

configs_bp = Blueprint('configs', __name__)


@configs_bp.route('/offer-configs', methods=['GET', 'OPTIONS'])
@require_auth
def list_configs():
    ctx = get_shop_context()
    with get_db() as db:
        rows = db.execute(text('''
            SELECT c.id, c.shop_id, c.template_id, c.theme_id, c.enabled, c.sort_order, c.display, c.created_at, c.updated_at,
                   t.type, t.name AS template_name,
                   th.name AS theme_name
            FROM offer_configs c
            JOIN offer_templates t ON t.id = c.template_id
            JOIN offer_themes th ON th.id = c.theme_id
            WHERE c.shop_id = :sid
            ORDER BY t.type, c.sort_order
        '''), {'sid': ctx['shop_id']}).mappings().all()
        return jsonify({'configs': [dict(r) for r in rows]}), 200


@configs_bp.route('/offer-configs', methods=['PUT', 'OPTIONS'])
@require_auth
def upsert_configs():
    ctx = get_shop_context()
    data = request.get_json() or {}
    items = data.get('configs') or []
    try:
        with get_db() as db:
            for it in items:
                db.execute(text('''
                    INSERT INTO offer_configs (shop_id, template_id, theme_id, enabled, sort_order, display)
                    VALUES (:sid, :tid, :thid, :enabled, :sort, CAST(:display AS JSONB))
                    ON CONFLICT (shop_id, template_id) DO UPDATE
                    SET theme_id = EXCLUDED.theme_id,
                        enabled = EXCLUDED.enabled,
                        sort_order = EXCLUDED.sort_order,
                        display = EXCLUDED.display,
                        updated_at = now()
                '''), {
                    'sid': ctx['shop_id'],
                    'tid': it.get('template_id') or it.get('id'),
                    'thid': it.get('theme_id'),
                    'enabled': bool(it.get('enabled', True)),
                    'sort': int(it.get('sort_order', 0)),
                    'display': json.dumps(it.get('display') or {})
                })
        return jsonify({'ok': True}), 200
    except Exception as e:
        return jsonify({ 'error': str(e) }), 500


