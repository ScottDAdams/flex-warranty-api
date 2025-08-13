from flask import Blueprint, request, jsonify
from sqlalchemy import text
from ..utils.auth import require_auth, get_shop_context
from ..models.database import get_db

prompts_bp = Blueprint('prompts', __name__)


@prompts_bp.route('/shops/prompt', methods=['GET', 'OPTIONS'])
@require_auth
def get_prompt():
    ctx = get_shop_context()
    with get_db() as db:
        row = db.execute(
            text('SELECT prompt_intro, prompt_rules, prompt_template, general_category_id, examples FROM evaluation_prompts WHERE shop_id = :sid'),
            {'sid': ctx['shop_id']}
        ).mappings().first()
        if not row:
            return jsonify({'prompt_intro': '', 'prompt_rules': '', 'prompt_template': '', 'general_category_id': None, 'examples': []}), 200
        return jsonify({
            'prompt_intro': row.get('prompt_intro') or '',
            'prompt_rules': row.get('prompt_rules') or '',
            'prompt_template': row.get('prompt_template') or '',
            'general_category_id': row.get('general_category_id'),
            'examples': row.get('examples') or []
        }), 200


@prompts_bp.route('/shops/prompt', methods=['PUT', 'OPTIONS'])
@require_auth
def upsert_prompt():
    ctx = get_shop_context()
    data = request.get_json() or {}
    prompt_intro = data.get('prompt_intro') or ''
    prompt_rules = data.get('prompt_rules') or ''
    prompt_template = data.get('prompt_template') or ''
    general_category_id = data.get('general_category_id')
    examples = data.get('examples') or []
    with get_db() as db:
        db.execute(
            text('''
                INSERT INTO evaluation_prompts (shop_id, prompt_intro, prompt_rules, prompt_template, general_category_id, examples)
                VALUES (:sid, :intro, :rules, :tpl, :gid, :examples::jsonb)
                ON CONFLICT (shop_id) DO UPDATE
                SET prompt_intro = EXCLUDED.prompt_intro,
                    prompt_rules = EXCLUDED.prompt_rules,
                    prompt_template = EXCLUDED.prompt_template,
                    general_category_id = EXCLUDED.general_category_id,
                    examples = EXCLUDED.examples,
                    updated_at = now()
            '''),
            {'sid': ctx['shop_id'], 'intro': prompt_intro, 'rules': prompt_rules, 'tpl': prompt_template, 'gid': general_category_id, 'examples': examples}
        )
    return jsonify({'ok': True}), 200


