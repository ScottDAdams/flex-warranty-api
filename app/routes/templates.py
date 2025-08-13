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
              id, shop_id, type, name, description, template_json, css_overrides, is_active, created_at, updated_at
            FROM offer_templates
            WHERE shop_id IN (0, :sid) AND is_active = true
            ORDER BY type, name, (shop_id = :sid) DESC, id
        '''), {'sid': ctx['shop_id']}).mappings().all()
        return jsonify({'templates': [dict(r) for r in rows]}), 200


