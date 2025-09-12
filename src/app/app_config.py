"""
Application Configuration and Environment Setup
Handles environment variables, app configuration, and directory setup
"""
import os
from flask import Flask


def load_env_file():
    """
    Manually load .env file if python-dotenv is not available
    """
    # Try multiple possible locations for .env file
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env'),  # Project root/config/.env
        os.path.join(os.path.dirname(__file__), '..', '..', '.env'),           # Project root/.env
        os.path.join(os.path.dirname(__file__), '..', 'config', '.env'),       # src/config/.env
    ]
    
    for env_path in possible_paths:
        if os.path.exists(env_path):
            print(f"✅ Loading .env from: {env_path}")
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip('"').strip("'")
                        os.environ[key] = value
                        if key == 'GITHUB_TOKEN':
                            print(f"✅ GITHUB_TOKEN loaded: {value[:8]}...")
            return True
    
    print("⚠️ No .env file found in expected locations")
    return False


def load_environment_variables():
    """
    Load environment variables from various sources
    """
    # First try manual loading for immediate availability
    load_env_file()
    
    # Then try dotenv library if available
    try:
        from dotenv import load_dotenv
        # Load root .env if present
        load_dotenv()
        # Explicitly load config/.env (current project keeps token there)
        config_env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
        if os.path.exists(config_env_path):
            load_dotenv(dotenv_path=config_env_path, override=True)
            print(f"✅ Loaded config/.env with dotenv")
    except ImportError:
        print("⚠️ python-dotenv not available, using manual .env loading only")
    
    # Check if GITHUB_TOKEN is now available
    github_token = os.getenv('GITHUB_TOKEN')
    if github_token:
        print(f"✅ GITHUB_TOKEN available: {github_token[:8]}...")
    else:
        print("⚠️ GITHUB_TOKEN not found in environment variables")


class AppConfig:
    """Application configuration class"""
    
    # Upload directories
    UPLOAD_FOLDER_MAHASISWA = 'data/mahasiswa'
    UPLOAD_FOLDER_GITHUB = 'data/github'
    
    # Cache directory
    CACHE_DIR = 'data/cache'
    
    # Template and static folders
    TEMPLATE_FOLDER = 'templates'
    STATIC_FOLDER = 'static'
    
    @classmethod
    def configure_app(cls, app: Flask) -> None:
        """
        Configure Flask application with necessary settings
        
        Args:
            app: Flask application instance
        """
        # Set upload folders
        app.config['UPLOAD_FOLDER_MAHASISWA'] = cls.UPLOAD_FOLDER_MAHASISWA
        app.config['UPLOAD_FOLDER_GITHUB'] = cls.UPLOAD_FOLDER_GITHUB
        app.config['CACHE_DIR'] = cls.CACHE_DIR
        
        # Create directories if they don't exist
        cls.create_directories()
    
    @classmethod
    def create_directories(cls) -> None:
        """Create necessary directories"""
        directories = [
            cls.UPLOAD_FOLDER_MAHASISWA,
            cls.UPLOAD_FOLDER_GITHUB,
            cls.CACHE_DIR
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"Created/verified directory: {directory}")
    
    @classmethod
    def get_upload_folder(cls, file_type: str) -> str:
        """
        Get upload folder path based on file type
        
        Args:
            file_type: Type of file ('mahasiswa' or 'github')
            
        Returns:
            Path to upload folder
            
        Raises:
            ValueError: If file_type is invalid
        """
        if file_type == 'mahasiswa':
            return cls.UPLOAD_FOLDER_MAHASISWA
        elif file_type == 'github':
            return cls.UPLOAD_FOLDER_GITHUB
        else:
            raise ValueError(f"Invalid file_type: {file_type}")


def initialize_configuration():
    """Initialize application configuration"""
    load_environment_variables()
    AppConfig.create_directories()
    
    # Verify critical environment variables
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("WARNING: GITHUB_TOKEN not found in environment variables")
    else:
        print("✅ GITHUB_TOKEN loaded successfully")
    
    return AppConfig
