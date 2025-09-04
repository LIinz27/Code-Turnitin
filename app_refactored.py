"""
Main Application Entry Point
Refactored Flask application using factory pattern
"""

# Import the application factory
from src.app import create_development_app

# Create the application
app = create_development_app()

if __name__ == '__main__':
    print("🚀 Starting Code Turnitin Application (Refactored)")
    print("📁 Organized structure with modular components")
    print("🔧 Using Flask application factory pattern")
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
