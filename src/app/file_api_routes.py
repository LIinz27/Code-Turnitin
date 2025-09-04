"""
File Management API Routes
Handles file operations, cleanup, and content retrieval endpoints
"""
from flask import Blueprint, request, jsonify
from .file_utils import FileManager


# Create blueprint for file management API
file_api_bp = Blueprint('file_api', __name__, url_prefix='/api/files')


@file_api_bp.route('/clear/mahasiswa', methods=['POST'])
def clear_mahasiswa_files():
    """Clear all student files"""
    try:
        count = FileManager.clear_student_files()
        return jsonify({
            "message": f"Berhasil menghapus {count} file mahasiswa.",
            "count": count
        }), 200
    except Exception as e:
        print(f"Error di endpoint clear mahasiswa files: {e}")
        return jsonify({
            "error": "Gagal menghapus file mahasiswa.", 
            "details": str(e)
        }), 500


@file_api_bp.route('/clear/github', methods=['POST'])
def clear_github_files():
    """Clear all GitHub files"""
    try:
        count = FileManager.clear_github_files()
        return jsonify({
            "message": f"Berhasil menghapus {count} file GitHub.",
            "count": count
        }), 200
    except Exception as e:
        print(f"Error di endpoint clear GitHub files: {e}")
        return jsonify({
            "error": "Gagal menghapus file GitHub.", 
            "details": str(e)
        }), 500


@file_api_bp.route('/content', methods=['POST'])
def get_code_content():
    """Get content of a specific file"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        file_type = data.get('file_type')  # 'mahasiswa' atau 'github'
        
        content, error = FileManager.get_file_content(filename, file_type)
        
        if error:
            return jsonify({"error": error}), 400
        
        return jsonify({"content": content}), 200
        
    except Exception as e:
        print(f"Error di endpoint get_code_content: {e}")
        return jsonify({
            "error": "Gagal mengambil konten file.", 
            "details": str(e)
        }), 500


@file_api_bp.route('/info/<file_type>', methods=['GET'])
def get_directory_info(file_type):
    """Get information about a directory"""
    try:
        from flask import current_app
        
        if file_type == 'mahasiswa':
            directory_path = current_app.config['UPLOAD_FOLDER_MAHASISWA']
        elif file_type == 'github':
            directory_path = current_app.config['UPLOAD_FOLDER_GITHUB']
        else:
            return jsonify({"error": "Invalid file_type"}), 400
        
        info = FileManager.get_directory_info(directory_path)
        return jsonify(info), 200
        
    except Exception as e:
        print(f"Error getting directory info: {e}")
        return jsonify({
            "error": "Gagal mengambil informasi direktori.", 
            "details": str(e)
        }), 500


# Legacy endpoints for backward compatibility
@file_api_bp.route('/clear_mahasiswa_files', methods=['POST'])
def clear_mahasiswa_files_legacy():
    """Legacy endpoint for clearing student files"""
    return clear_mahasiswa_files()


@file_api_bp.route('/clear_github_files', methods=['POST'])
def clear_github_files_legacy():
    """Legacy endpoint for clearing GitHub files"""
    return clear_github_files()


@file_api_bp.route('/get_code_content', methods=['POST'])
def get_code_content_legacy():
    """Legacy endpoint for getting code content"""
    return get_code_content()


def register_file_api_routes(app):
    """
    Register file management API routes with the Flask application
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(file_api_bp)
    
    # Also register legacy routes at root level for backward compatibility
    app.add_url_rule('/clear_mahasiswa_files', 'clear_mahasiswa_files_legacy', 
                     clear_mahasiswa_files, methods=['POST'])
    app.add_url_rule('/clear_github_files', 'clear_github_files_legacy', 
                     clear_github_files, methods=['POST'])
    app.add_url_rule('/get_code_content', 'get_code_content_legacy', 
                     get_code_content, methods=['POST'])
