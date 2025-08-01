from flask import Blueprint, send_from_directory, current_app
import os

proxy_bp = Blueprint('proxy', __name__)

@proxy_bp.route('/js/warranty-embed.js')
def serve_warranty_embed():
    """Serve the warranty embed JavaScript file"""
    return send_from_directory(
        os.path.join(current_app.root_path, 'static', 'js'),
        'warranty-embed.js',
        mimetype='application/javascript'
    )

@proxy_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return {'status': 'healthy', 'service': 'flex-warranty-api'}, 200 