from flask import Flask, request, send_from_directory, render_template
from flask_cors import CORS
import os
from .config import Config
from .routes.offers import offers_bp
from .routes.themes import themes_bp
from .routes.layouts import layouts_bp
from .routes.shops import shops_bp
from .routes.images import images_bp
from .routes.webhooks import webhooks_bp
from .routes.products import products_bp
from .routes.prompts import prompts_bp
from .routes.templates import templates_bp
from .routes.configs import configs_bp
from .routes.proxy import proxy_bp
from .models.database import get_db
from sqlalchemy import text

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(Config)

    # Initialize CORS for the entire application (broad dev policy for tunnels)
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": "*",
                "methods": ["GET", "POST", "OPTIONS", "PATCH", "DELETE"],
                "allow_headers": [
                    "Content-Type",
                    "Authorization",
                    "X-Shop-Domain",
                    "X-API-Key",
                ],
                "supports_credentials": False,
                "send_wildcard": True,
            }
        },
    )

    @app.after_request
    def add_cors_headers(resp):
        try:
            path = request.path or ''
        except Exception:
            path = ''
        if path.startswith('/api/') or path.startswith('/images/'):
            origin = request.headers.get('Origin', '*')
            resp.headers['Access-Control-Allow-Origin'] = origin if origin else '*'
            resp.headers['Vary'] = 'Origin'
            resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Shop-Domain, X-API-Key'
            resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PATCH, DELETE'
        return resp

    @app.route('/static/images/<path:filename>')
    def serve_static(filename):
        return send_from_directory(os.path.join(app.static_folder, 'images'), filename)

    @app.before_request
    def block_known_scanner_paths():
        bad_paths = [
            '.env', 'wp-config.php', '.git', 'config.yml', 'phpinfo.php',
            'secrets.json', 'config.json', 'settings.yaml'
        ]
        if any(bp in request.path.lower() for bp in bad_paths):
            app.logger.warning(f"Blocked suspicious path: {request.path} from IP {request.remote_addr}")
            return "Access Denied", 403

    # Register blueprints
    app.register_blueprint(offers_bp, url_prefix='/api')
    app.register_blueprint(themes_bp, url_prefix='/api')
    app.register_blueprint(layouts_bp, url_prefix='/api')
    app.register_blueprint(shops_bp, url_prefix='/api/shops')
    app.register_blueprint(images_bp, url_prefix='/api')
    app.register_blueprint(webhooks_bp, url_prefix='/api/webhooks')
    app.register_blueprint(products_bp, url_prefix='/api')
    app.register_blueprint(proxy_bp, url_prefix='/api')
    app.register_blueprint(prompts_bp, url_prefix='/api')
    app.register_blueprint(templates_bp, url_prefix='/api')
    app.register_blueprint(configs_bp, url_prefix='/api')

    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'flex-warranty-api'}, 200

    return app 