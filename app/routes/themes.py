from flask import Blueprint, request, jsonify
from sqlalchemy import text
import json
from datetime import datetime
from ..utils.auth import require_auth, get_shop_context
from ..models.database import get_db
import logging

logger = logging.getLogger(__name__)

# Create the Blueprint
themes_bp = Blueprint('themes', __name__)


@themes_bp.route('/themes', methods=['GET'])
@require_auth
def list_themes():
    """Get all themes for the current shop"""
    try:
        shop_context = get_shop_context()
        
        with get_db() as db:
            result = db.execute(
                text('''
                    SELECT * FROM offer_themes
                    WHERE shop_id = :shop_id
                    ORDER BY is_default DESC, name ASC
                '''),
                {'shop_id': shop_context['shop_id']}
            ).mappings().all()
            
            themes = []
            for row in result:
                theme = dict(row)
                theme['created_at'] = theme['created_at'].isoformat() if theme['created_at'] else None
                themes.append(theme)
            
            return jsonify({'themes': themes}), 200
            
    except Exception as e:
        logger.error(f"Error listing themes: {str(e)}")
        return jsonify({'error': 'Failed to list themes'}), 500


@themes_bp.route('/themes/<int:theme_id>', methods=['GET'])
@require_auth
def get_theme(theme_id):
    """Get a specific theme by ID"""
    try:
        shop_context = get_shop_context()
        
        with get_db() as db:
            result = db.execute(
                text('''
                    SELECT * FROM offer_themes
                    WHERE id = :theme_id AND shop_id = :shop_id
                '''),
                {
                    'theme_id': theme_id,
                    'shop_id': shop_context['shop_id']
                }
            ).mappings().first()
            
            if not result:
                return jsonify({'error': 'Theme not found'}), 404
            
            theme = dict(result)
            theme['created_at'] = theme['created_at'].isoformat() if theme['created_at'] else None
            
            return jsonify({'theme': theme}), 200
            
    except Exception as e:
        logger.error(f"Error getting theme: {str(e)}")
        return jsonify({'error': 'Failed to get theme'}), 500


@themes_bp.route('/themes', methods=['POST'])
@require_auth
def create_theme():
    """Create a new theme"""
    try:
        shop_context = get_shop_context()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Theme name is required'}), 400
        
        with get_db() as db:
            # If this is set as default, unset other defaults
            if data.get('is_default'):
                db.execute(
                    text('UPDATE offer_themes SET is_default = false WHERE shop_id = :shop_id'),
                    {'shop_id': shop_context['shop_id']}
                )
            
            result = db.execute(
                text('''
                    INSERT INTO offer_themes (shop_id, name, primary_color, secondary_color, accent_color, is_default)
                    VALUES (:shop_id, :name, :primary_color, :secondary_color, :accent_color, :is_default)
                    RETURNING id
                '''),
                {
                    'shop_id': shop_context['shop_id'],
                    'name': data.get('name'),
                    'primary_color': data.get('primary_color'),
                    'secondary_color': data.get('secondary_color'),
                    'accent_color': data.get('accent_color'),
                    'is_default': data.get('is_default', False)
                }
            )
            
            theme_id = result.fetchone()[0]
            
            # Get the created theme
            theme_result = db.execute(
                text('SELECT * FROM offer_themes WHERE id = :theme_id'),
                {'theme_id': theme_id}
            ).mappings().first()
            
            theme = dict(theme_result)
            theme['created_at'] = theme['created_at'].isoformat() if theme['created_at'] else None
            
            return jsonify({'theme': theme}), 201
            
    except Exception as e:
        logger.error(f"Error creating theme: {str(e)}")
        return jsonify({'error': 'Failed to create theme'}), 500


@themes_bp.route('/themes/<int:theme_id>', methods=['PUT'])
@require_auth
def update_theme(theme_id):
    """Update an existing theme"""
    try:
        shop_context = get_shop_context()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        with get_db() as db:
            # Check if theme exists and belongs to shop
            existing = db.execute(
                text('SELECT id FROM offer_themes WHERE id = :theme_id AND shop_id = :shop_id'),
                {
                    'theme_id': theme_id,
                    'shop_id': shop_context['shop_id']
                }
            ).fetchone()
            
            if not existing:
                return jsonify({'error': 'Theme not found'}), 404
            
            # If setting as default, unset other defaults
            if data.get('is_default'):
                db.execute(
                    text('UPDATE offer_themes SET is_default = false WHERE shop_id = :shop_id AND id != :theme_id'),
                    {
                        'shop_id': shop_context['shop_id'],
                        'theme_id': theme_id
                    }
                )
            
            # Build update query dynamically
            update_fields = []
            params = {'theme_id': theme_id, 'shop_id': shop_context['shop_id']}
            
            for field in ['name', 'primary_color', 'secondary_color', 'accent_color', 'is_default']:
                if field in data:
                    update_fields.append(f"{field} = :{field}")
                    params[field] = data[field]
            
            if not update_fields:
                return jsonify({'error': 'No fields to update'}), 400
            
            # Update the theme
            db.execute(
                text(f'''
                    UPDATE offer_themes 
                    SET {', '.join(update_fields)}
                    WHERE id = :theme_id AND shop_id = :shop_id
                '''),
                params
            )
            
            # Get the updated theme
            result = db.execute(
                text('SELECT * FROM offer_themes WHERE id = :theme_id'),
                {'theme_id': theme_id}
            ).mappings().first()
            
            theme = dict(result)
            theme['created_at'] = theme['created_at'].isoformat() if theme['created_at'] else None
            
            return jsonify({'theme': theme}), 200
            
    except Exception as e:
        logger.error(f"Error updating theme: {str(e)}")
        return jsonify({'error': 'Failed to update theme'}), 500


@themes_bp.route('/themes/<int:theme_id>', methods=['DELETE'])
@require_auth
def delete_theme(theme_id):
    """Delete a theme"""
    try:
        shop_context = get_shop_context()
        
        with get_db() as db:
            # Check if theme is default
            result = db.execute(
                text('SELECT is_default FROM offer_themes WHERE id = :theme_id AND shop_id = :shop_id'),
                {
                    'theme_id': theme_id,
                    'shop_id': shop_context['shop_id']
                }
            ).fetchone()
            
            if not result:
                return jsonify({'error': 'Theme not found'}), 404
            
            if result[0]:  # is_default is True
                return jsonify({'error': 'Cannot delete default theme'}), 400
            
            # Check if theme is being used by any offers
            offers_using_theme = db.execute(
                text('SELECT COUNT(*) FROM offers WHERE theme::text LIKE :theme_id AND shop_id = :shop_id'),
                {
                    'theme_id': f'%"id": {theme_id}%',
                    'shop_id': shop_context['shop_id']
                }
            ).fetchone()[0]
            
            if offers_using_theme > 0:
                return jsonify({'error': f'Theme is being used by {offers_using_theme} offer(s)'}), 400
            
            # Delete the theme
            delete_result = db.execute(
                text('DELETE FROM offer_themes WHERE id = :theme_id AND shop_id = :shop_id'),
                {
                    'theme_id': theme_id,
                    'shop_id': shop_context['shop_id']
                }
            )
            
            if delete_result.rowcount == 0:
                return jsonify({'error': 'Theme not found'}), 404
            
            return jsonify({'message': 'Theme deleted successfully'}), 200
            
    except Exception as e:
        logger.error(f"Error deleting theme: {str(e)}")
        return jsonify({'error': 'Failed to delete theme'}), 500


@themes_bp.route('/themes/<int:theme_id>/set-default', methods=['POST'])
@require_auth
def set_default_theme(theme_id):
    """Set a theme as the default for the shop"""
    try:
        shop_context = get_shop_context()
        
        with get_db() as db:
            # Check if theme exists and belongs to shop
            existing = db.execute(
                text('SELECT id FROM offer_themes WHERE id = :theme_id AND shop_id = :shop_id'),
                {
                    'theme_id': theme_id,
                    'shop_id': shop_context['shop_id']
                }
            ).fetchone()
            
            if not existing:
                return jsonify({'error': 'Theme not found'}), 404
            
            # Unset all other defaults
            db.execute(
                text('UPDATE offer_themes SET is_default = false WHERE shop_id = :shop_id'),
                {'shop_id': shop_context['shop_id']}
            )
            
            # Set this theme as default
            db.execute(
                text('UPDATE offer_themes SET is_default = true WHERE id = :theme_id'),
                {'theme_id': theme_id}
            )
            
            return jsonify({'message': 'Default theme updated successfully'}), 200
            
    except Exception as e:
        logger.error(f"Error setting default theme: {str(e)}")
        return jsonify({'error': 'Failed to set default theme'}), 500 