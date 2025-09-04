"""
Flask Application Factory
Creates and configures the Flask application with all components
"""
from flask import Flask
from .app_config import AppConfig, initialize_configuration
from .web_routes import register_web_routes
from .file_api_routes import register_file_api_routes
from .similarity_api_routes import register_similarity_api_routes
from .classroom_api_routes import register_classroom_api_routes


def create_app(config_class=AppConfig):
    """
    Create and configure Flask application
    
    Args:
        config_class: Configuration class to use
        
    Returns:
        Configured Flask application
    """
    # Initialize configuration first
    config = initialize_configuration()
    
    # Get absolute paths for template and static folders
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Go up to project root
    template_folder = os.path.join(base_dir, config.TEMPLATE_FOLDER)
    static_folder = os.path.join(base_dir, config.STATIC_FOLDER)
    
    # Create Flask app with absolute paths
    app = Flask(__name__, 
                template_folder=template_folder,
                static_folder=static_folder)
    
    print(f"Template folder: {template_folder}")
    print(f"Static folder: {static_folder}")
    
    # Configure app
    config.configure_app(app)
    
    # Register all route blueprints
    register_web_routes(app)
    register_file_api_routes(app)
    register_similarity_api_routes(app)
    register_classroom_api_routes(app)
    
    # Add health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "app": "Code Turnitin",
            "version": "2.0"
        }
    
    # Add error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return {"error": "Endpoint not found"}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        return {"error": "Internal server error"}, 500
    
    print("✅ Flask application created and configured successfully")
    return app


def create_development_app():
    """
    Create app for development with debug settings
    
    Returns:
        Flask app configured for development
    """
    app = create_app()
    app.config['DEBUG'] = True
    app.config['TESTING'] = False
    return app


def create_production_app():
    """
    Create app for production with optimized settings
    
    Returns:
        Flask app configured for production
    """
    app = create_app()
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    return app
