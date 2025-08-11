from flask import Blueprint, request, jsonify, send_file
from sqlalchemy import text
from ..utils.auth import require_auth, get_shop_context
from ..models.database import get_db
import io
import imghdr

images_bp = Blueprint('images', __name__)


def _validate_image(image_bytes: bytes):
    image_type = imghdr.what(None, h=image_bytes)
    return image_type if image_type in ['jpeg', 'png', 'gif'] else None


@images_bp.route('/images/<int:image_id>/display', methods=['GET'])
def display_image(image_id: int):
    try:
        with get_db() as db:
            row = db.execute(
                text('SELECT data, content_type FROM offer_images WHERE id = :id'),
                {'id': image_id}
            ).mappings().first()
            if not row:
                return 'Image not found', 404

            resp = send_file(io.BytesIO(row['data']), mimetype=row['content_type'])
            resp.headers['Cache-Control'] = 'public, max-age=31536000'
            resp.headers['ETag'] = f'"{image_id}"'
            return resp
    except Exception as e:
        return ('Error serving image', 500)


@images_bp.route('/images', methods=['GET', 'OPTIONS'])
@require_auth
def list_images():
    try:
        ctx = get_shop_context()
        with get_db() as db:
            rows = db.execute(
                text('''
                    SELECT id, filename, content_type, created_at
                    FROM offer_images
                    WHERE shop_id = :shop_id OR shop_id = 0
                    ORDER BY created_at DESC
                '''),
                {'shop_id': ctx['shop_id']}
            ).mappings().all()
            return jsonify({'success': True, 'images': [dict(r) for r in rows]}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to list images'}), 500


@images_bp.route('/images/upload', methods=['POST', 'OPTIONS'])
@require_auth
def upload_image():
    try:
        ctx = get_shop_context()
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'}), 400
        f = request.files['image']
        if not f.filename:
            return jsonify({'success': False, 'error': 'No selected file'}), 400
        data = f.read()
        image_type = _validate_image(data)
        if not image_type:
            return jsonify({'success': False, 'error': 'Invalid image format. Must be JPEG, PNG, or GIF'}), 400
        content_type = f'image/{image_type}'

        with get_db() as db:
            res = db.execute(
                text('''
                    INSERT INTO offer_images (filename, content_type, data, shop_id)
                    VALUES (:filename, :content_type, :data, :shop_id)
                    RETURNING id, filename, content_type, created_at
                '''),
                {'filename': f.filename, 'content_type': content_type, 'data': data, 'shop_id': ctx['shop_id']}
            )
            row = res.mappings().first()
            return jsonify({'success': True, 'image': dict(row)}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': 'Upload failed'}), 500


@images_bp.route('/images/<int:image_id>', methods=['DELETE'])
@require_auth
def delete_image(image_id: int):
    try:
        with get_db() as db:
            res = db.execute(text('DELETE FROM offer_images WHERE id = :id'), {'id': image_id})
            if res.rowcount == 0:
                return jsonify({'success': False, 'error': 'Image not found'}), 404
            return jsonify({'success': True}), 200
    except Exception:
        return jsonify({'success': False, 'error': 'Delete failed'}), 500


