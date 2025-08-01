from flask import Blueprint, request, jsonify
from sqlalchemy import text
import json
from datetime import datetime
from ..utils.auth import require_auth, get_shop_context
from ..models.database import get_db
import logging

logger = logging.getLogger(__name__)

# Create the Blueprint
layouts_bp = Blueprint('layouts', __name__)


@layouts_bp.route('/layouts', methods=['GET'])
@require_auth
def list_layouts():
    """Get all layouts for the current shop"""
    try:
        shop_context = get_shop_context()
        
        with get_db() as db:
            result = db.execute(
                text('''
                    SELECT * FROM offer_layouts
                    WHERE shop_id = :shop_id
                    ORDER BY name ASC
                '''),
                {'shop_id': shop_context['shop_id']}
            ).mappings().all()
            
            layouts = []
            for row in result:
                layout = dict(row)
                layout['created_at'] = layout['created_at'].isoformat() if layout['created_at'] else None
                layouts.append(layout)
            
            return jsonify({'layouts': layouts}), 200
            
    except Exception as e:
        logger.error(f"Error listing layouts: {str(e)}")
        return jsonify({'error': 'Failed to list layouts'}), 500


@layouts_bp.route('/layouts/<int:layout_id>', methods=['GET'])
@require_auth
def get_layout(layout_id):
    """Get a specific layout by ID"""
    try:
        shop_context = get_shop_context()
        
        with get_db() as db:
            result = db.execute(
                text('''
                    SELECT * FROM offer_layouts
                    WHERE id = :layout_id AND shop_id = :shop_id
                '''),
                {
                    'layout_id': layout_id,
                    'shop_id': shop_context['shop_id']
                }
            ).mappings().first()
            
            if not result:
                return jsonify({'error': 'Layout not found'}), 404
            
            layout = dict(result)
            layout['created_at'] = layout['created_at'].isoformat() if layout['created_at'] else None
            
            return jsonify({'layout': layout}), 200
            
    except Exception as e:
        logger.error(f"Error getting layout: {str(e)}")
        return jsonify({'error': 'Failed to get layout'}), 500


@layouts_bp.route('/layouts', methods=['POST'])
@require_auth
def create_layout():
    """Create a new layout"""
    try:
        shop_context = get_shop_context()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Layout name is required'}), 400
        
        with get_db() as db:
            result = db.execute(
                text('''
                    INSERT INTO offer_layouts (shop_id, name, description, css_classes, preview_html)
                    VALUES (:shop_id, :name, :description, :css_classes, :preview_html)
                    RETURNING id
                '''),
                {
                    'shop_id': shop_context['shop_id'],
                    'name': data.get('name'),
                    'description': data.get('description'),
                    'css_classes': data.get('css_classes'),
                    'preview_html': data.get('preview_html')
                }
            )
            
            layout_id = result.fetchone()[0]
            
            # Get the created layout
            layout_result = db.execute(
                text('SELECT * FROM offer_layouts WHERE id = :layout_id'),
                {'layout_id': layout_id}
            ).mappings().first()
            
            layout = dict(layout_result)
            layout['created_at'] = layout['created_at'].isoformat() if layout['created_at'] else None
            
            return jsonify({'layout': layout}), 201
            
    except Exception as e:
        logger.error(f"Error creating layout: {str(e)}")
        return jsonify({'error': 'Failed to create layout'}), 500


@layouts_bp.route('/layouts/<int:layout_id>', methods=['PUT'])
@require_auth
def update_layout(layout_id):
    """Update an existing layout"""
    try:
        shop_context = get_shop_context()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        with get_db() as db:
            # Check if layout exists and belongs to shop
            existing = db.execute(
                text('SELECT id FROM offer_layouts WHERE id = :layout_id AND shop_id = :shop_id'),
                {
                    'layout_id': layout_id,
                    'shop_id': shop_context['shop_id']
                }
            ).fetchone()
            
            if not existing:
                return jsonify({'error': 'Layout not found'}), 404
            
            # Build update query dynamically
            update_fields = []
            params = {'layout_id': layout_id, 'shop_id': shop_context['shop_id']}
            
            for field in ['name', 'description', 'css_classes', 'preview_html']:
                if field in data:
                    update_fields.append(f"{field} = :{field}")
                    params[field] = data[field]
            
            if not update_fields:
                return jsonify({'error': 'No fields to update'}), 400
            
            # Update the layout
            db.execute(
                text(f'''
                    UPDATE offer_layouts 
                    SET {', '.join(update_fields)}
                    WHERE id = :layout_id AND shop_id = :shop_id
                '''),
                params
            )
            
            # Get the updated layout
            result = db.execute(
                text('SELECT * FROM offer_layouts WHERE id = :layout_id'),
                {'layout_id': layout_id}
            ).mappings().first()
            
            layout = dict(result)
            layout['created_at'] = layout['created_at'].isoformat() if layout['created_at'] else None
            
            return jsonify({'layout': layout}), 200
            
    except Exception as e:
        logger.error(f"Error updating layout: {str(e)}")
        return jsonify({'error': 'Failed to update layout'}), 500


@layouts_bp.route('/layouts/<int:layout_id>', methods=['DELETE'])
@require_auth
def delete_layout(layout_id):
    """Delete a layout"""
    try:
        shop_context = get_shop_context()
        
        with get_db() as db:
            # Check if layout is being used by any offers
            offers_using_layout = db.execute(
                text('SELECT COUNT(*) FROM offers WHERE layout_id = :layout_id AND shop_id = :shop_id'),
                {
                    'layout_id': layout_id,
                    'shop_id': shop_context['shop_id']
                }
            ).fetchone()[0]
            
            if offers_using_layout > 0:
                return jsonify({'error': f'Layout is being used by {offers_using_layout} offer(s)'}), 400
            
            # Delete the layout
            delete_result = db.execute(
                text('DELETE FROM offer_layouts WHERE id = :layout_id AND shop_id = :shop_id'),
                {
                    'layout_id': layout_id,
                    'shop_id': shop_context['shop_id']
                }
            )
            
            if delete_result.rowcount == 0:
                return jsonify({'error': 'Layout not found'}), 404
            
            return jsonify({'message': 'Layout deleted successfully'}), 200
            
    except Exception as e:
        logger.error(f"Error deleting layout: {str(e)}")
        return jsonify({'error': 'Failed to delete layout'}), 500


@layouts_bp.route('/layouts/preview', methods=['POST'])
@require_auth
def preview_layout():
    """Preview a layout with sample data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Sample warranty offer data for preview
        sample_data = {
            'headline': data.get('headline', 'Extended Warranty Protection'),
            'body': data.get('body', 'Protect your purchase with our comprehensive extended warranty coverage.'),
            'button_text': data.get('button_text', 'Add Warranty'),
            'button_url': '#',
            'image_url': data.get('image_url', 'https://via.placeholder.com/300x200?text=Warranty')
        }
        
        # Generate preview HTML based on layout
        layout_html = data.get('preview_html', '')
        
        # Replace placeholders with sample data
        preview_html = layout_html.replace('{{headline}}', sample_data['headline'])
        preview_html = preview_html.replace('{{body}}', sample_data['body'])
        preview_html = preview_html.replace('{{button_text}}', sample_data['button_text'])
        preview_html = preview_html.replace('{{image_url}}', sample_data['image_url'])
        
        return jsonify({
            'preview_html': preview_html,
            'sample_data': sample_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating preview: {str(e)}")
        return jsonify({'error': 'Failed to generate preview'}), 500 