"""
Classroom API Routes
Handles GitHub Classroom specific API endpoints
"""
import os
from flask import Blueprint, request, jsonify, current_app
from ..scrapers.github_classroom_refactored import GitHubClassroom


# Create blueprint for classroom API
classroom_api_bp = Blueprint('classroom_api', __name__, url_prefix='/api/classroom')


@classroom_api_bp.route('/list', methods=['GET'])
def api_classroom_list():
    """Get list of accessible classrooms"""
    try:
        classroom = GitHubClassroom()
        classrooms = classroom.get_classrooms()
        
        return jsonify({
            "success": True,
            "classrooms": classrooms,
            "count": len(classrooms)
        }), 200
        
    except Exception as e:
        print(f"Error in /api/classroom/list: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@classroom_api_bp.route('/load', methods=['POST'])
def api_classroom_load():
    """Load classroom details by URL or ID"""
    print("DEBUG: /api/classroom/load endpoint called")
    
    try:
        data = request.get_json()
        print(f"DEBUG: Request data: {data}")
        
        classroom_url = data.get('classroom_url', '').strip()
        print(f"DEBUG: Classroom URL: {classroom_url}")
        
        if not classroom_url:
            return jsonify({
                "success": False,
                "error": "Classroom URL atau ID tidak boleh kosong"
            }), 400
        
        classroom = GitHubClassroom()
        print("DEBUG: GitHubClassroom instance created")
        
        # Extract classroom ID from URL or use ID directly
        classroom_id = classroom.extract_classroom_id(classroom_url)
        print(f"DEBUG: Extracted classroom ID: {classroom_id}")
        
        if not classroom_id:
            return jsonify({
                "success": False,
                "error": "Format classroom URL atau ID tidak valid, atau classroom tidak ditemukan"
            }), 400
        
        # Get classroom details using correct ID
        print(f"DEBUG: Getting classroom details for ID: {classroom_id}")
        classroom_details = classroom.get_classroom_details(classroom_id)
        print(f"DEBUG: Classroom details: {bool(classroom_details)}")
        
        if not classroom_details:
            return jsonify({
                "success": False,
                "error": f"Classroom dengan ID {classroom_id} tidak ditemukan atau tidak dapat diakses"
            }), 404
        
        print("DEBUG: Returning success response")
        return jsonify({
            "success": True,
            "classroom": classroom_details
        }), 200
        
    except Exception as e:
        print(f"ERROR in /api/classroom/load: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@classroom_api_bp.route('/<int:classroom_id>/assignments', methods=['GET'])
def api_classroom_assignments(classroom_id):
    """Get list of assignments in a classroom"""
    try:
        classroom = GitHubClassroom()
        assignments = classroom.get_classroom_assignments(classroom_id)
        
        return jsonify({
            "success": True,
            "assignments": assignments,
            "count": len(assignments)
        }), 200
        
    except Exception as e:
        print(f"Error in /api/classroom/assignments: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@classroom_api_bp.route('/<int:classroom_id>/assignments/<int:assignment_id>/preview', methods=['GET'])
def api_assignment_preview(classroom_id, assignment_id):
    """Preview assignment repositories without downloading"""
    try:
        classroom = GitHubClassroom()
        preview_data = classroom.preview_assignment_repositories(assignment_id)
        
        return jsonify({
            "success": True,
            "preview": preview_data
        }), 200
        
    except Exception as e:
        print(f"Error in assignment preview: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@classroom_api_bp.route('/download', methods=['POST'])
def api_classroom_download():
    """Download assignment repositories"""
    try:
        data = request.get_json()
        assignment_id = data.get('assignment_id')
        classroom_id = data.get('classroom_id')
        
        if not assignment_id:
            return jsonify({
                "success": False,
                "error": "Assignment ID diperlukan"
            }), 400
        
        # Use organized save directory
        save_dir = current_app.config.get('UPLOAD_FOLDER_GITHUB', 'data/github')
        
        classroom = GitHubClassroom()
        
        # Set current classroom ID for organized folder structure
        if classroom_id:
            classroom.classroom_api.current_classroom_id = classroom_id
        
        # Download repositories
        downloaded_files = classroom.download_classroom_assignment_repos(
            assignment_id, 
            save_dir
        )
        
        return jsonify({
            "success": True,
            "message": f"Berhasil mendownload {len(downloaded_files)} file",
            "downloaded_files": len(downloaded_files),
            "files": [os.path.basename(f) for f in downloaded_files[:10]]  # Show first 10 files
        }), 200
        
    except Exception as e:
        print(f"Error in classroom download: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@classroom_api_bp.route('/check-access', methods=['POST'])
def api_check_access():
    """Check repository access for assignment"""
    try:
        data = request.get_json()
        assignment_id = data.get('assignment_id')
        
        if not assignment_id:
            return jsonify({
                "success": False,
                "error": "Assignment ID diperlukan"
            }), 400
        
        classroom = GitHubClassroom()
        preview_data = classroom.preview_assignment_repositories(assignment_id)
        
        # Extract access information
        access_summary = preview_data.get('access_summary', {})
        total_repos = access_summary.get('total', 0)
        accessible_repos = (
            access_summary.get('public', 0) + 
            access_summary.get('private_accessible', 0)
        )
        
        return jsonify({
            "success": True,
            "total_repositories": total_repos,
            "accessible_repositories": accessible_repos,
            "access_rate": (accessible_repos / total_repos * 100) if total_repos > 0 else 0,
            "access_summary": access_summary,
            "repositories": preview_data.get('repositories', [])
        }), 200
        
    except Exception as e:
        print(f"Error checking access: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@classroom_api_bp.route('/token-info', methods=['GET'])
def api_token_info():
    """Get GitHub token information and rate limits"""
    try:
        classroom = GitHubClassroom()
        
        # Check if authenticated
        is_authenticated = classroom.is_authenticated()
        
        if not is_authenticated:
            return jsonify({
                "success": False,
                "authenticated": False,
                "error": "GitHub token tidak valid atau tidak tersedia"
            }), 401
        
        # Get rate limit info
        rate_limit_info = classroom.get_rate_limit_info()
        
        # Get user info
        user_info = classroom.auth.make_request('user')
        
        return jsonify({
            "success": True,
            "authenticated": True,
            "user": {
                "login": user_info.get('login') if user_info else None,
                "name": user_info.get('name') if user_info else None
            },
            "rate_limit": rate_limit_info
        }), 200
        
    except Exception as e:
        print(f"Error getting token info: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def register_classroom_api_routes(app):
    """
    Register classroom API routes with the Flask application
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(classroom_api_bp)
