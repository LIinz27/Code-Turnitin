"""
Web Routes - Template Rendering
Handles all template rendering routes and static file serving
"""
from flask import Blueprint, render_template, send_from_directory, current_app


# Create blueprint for web routes
web_bp = Blueprint('web', __name__)


@web_bp.route('/')
def index():
    """Main index page"""
    return render_template('index.html')


@web_bp.route('/classroom')
def classroom_page():
    """Classroom management page"""
    return render_template('classroom.html')


@web_bp.route('/test-repos')
def test_repos_page():
    """Test repositories page"""
    return render_template('test_repos.html')


@web_bp.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(current_app.static_folder, filename)


def register_web_routes(app):
    """
    Register web routes with the Flask application
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(web_bp)
