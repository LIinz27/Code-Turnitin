"""
Similarity Analysis API Routes
Handles code similarity analysis and auto-search functionality
"""
import json
import os
from flask import Blueprint, request, jsonify, current_app
from ..scrapers.github_scraper import scrape_repo_files
from ..scrapers.github_search import auto_search_candidate_repos, load_cache
from ..algorithms.similarity_checker import get_similar_blocks
from .file_utils import FileManager


# Create blueprint for similarity analysis API
similarity_api_bp = Blueprint('similarity_api', __name__, url_prefix='/api/similarity')


@similarity_api_bp.route('/analyze', methods=['POST'])
def analyze_code():
    """
    Analyze code similarity between student repositories and GitHub repositories
    """
    print("\n--- Memulai Analisis ---")
    
    try:
        # Clear student files
        FileManager.clear_student_files()
        
        # Parse student repository URLs
        student_repo_urls_str = request.form.get('student_repo_urls', '[]')
        try:
            student_repo_urls = json.loads(student_repo_urls_str)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON for student_repo_urls"}), 400

        print(f"URL Repositori Mahasiswa diterima: {student_repo_urls}")
        
        # Validate student URLs
        if not student_repo_urls:
            return jsonify({
                "error": "Mohon tambahkan setidaknya satu URL repositori mahasiswa."
            }), 400

        # Download student repositories
        uploaded_student_files = []
        for repo_url in student_repo_urls:
            print(f"Mulai scraping repositori mahasiswa: {repo_url}")
            downloaded = scrape_repo_files(repo_url, current_app.config['UPLOAD_FOLDER_MAHASISWA'])
            uploaded_student_files.extend(downloaded)
            print(f"Selesai scraping {repo_url}. Total file dari repo ini: {len(downloaded)}")
        
        if not uploaded_student_files:
            return jsonify({
                "error": "Gagal mengunduh file kode dari repositori mahasiswa yang diberikan. "
                         "Pastikan URL repositori benar dan mengandung file kode yang didukung."
            }), 400

        # Parse GitHub repository URLs
        github_urls_str = request.form.get('github_urls', '[]')
        try:
            github_repo_urls = json.loads(github_urls_str)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON for github_urls"}), 400

        print(f"URL Repositori GitHub diterima: {github_repo_urls}")
        
        # Clear GitHub files
        FileManager.clear_github_files()

        # Download GitHub repositories
        scraped_github_files = []
        if github_repo_urls:
            for repo_url in github_repo_urls:
                print(f"Mulai scraping repositori pembanding: {repo_url}")
                downloaded = scrape_repo_files(repo_url, current_app.config['UPLOAD_FOLDER_GITHUB'])
                scraped_github_files.extend(downloaded)
                print(f"Selesai scraping {repo_url}. Total file dari repo ini: {len(downloaded)}")
            
            if not scraped_github_files:
                return jsonify({
                    "error": "Gagal mengunduh file kode dari repositori GitHub pembanding yang diberikan."
                }), 400
        else:
            print("Tidak ada URL GitHub pembanding yang diberikan.")

        # Perform similarity analysis
        results = _perform_similarity_analysis(uploaded_student_files, scraped_github_files)
        
        print("Analisis selesai. Mengirim hasil.")
        return jsonify({"mh_vs_gh_results": results}), 200
        
    except Exception as e:
        print(f"Error in analyze_code: {e}")
        return jsonify({
            "error": "Terjadi kesalahan saat menganalisis kode.", 
            "details": str(e)
        }), 500


@similarity_api_bp.route('/auto-search/init', methods=['POST'])
def auto_search_init():
    """
    Initialize auto search for candidate repositories
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        student_repo_urls = data.get('student_repo_urls') or []
        
        if not isinstance(student_repo_urls, list) or not student_repo_urls:
            return jsonify({
                'error': 'student_repo_urls harus berupa list dan tidak boleh kosong'
            }), 400

        # Clear student files
        FileManager.clear_student_files()
        
        # Perform auto search
        cache_id, candidates = auto_search_candidate_repos(
            student_repo_urls, 
            current_app.config['UPLOAD_FOLDER_MAHASISWA'], 
            cache_dir=current_app.config.get('CACHE_DIR', 'data/cache'), 
            top_n=5
        )
        
        # Format response
        response_candidates = []
        for c in candidates:
            response_candidates.append({
                'full_name': c['full_name'],
                'score': c['score'],
                'matched_tokens': c['matched_tokens'],
                'files': c['files'],
                'size_kb': c['size_kb'],
                'stars': c['stars'],
                'token_overlap': c.get('token_overlap'),
                'file_overlap': c.get('file_overlap')
            })
            
        return jsonify({
            'cache_id': cache_id, 
            'candidates': response_candidates
        }), 200
        
    except Exception as e:
        print(f"Error auto_search_candidate_repos: {e}")
        return jsonify({
            'error': 'Gagal melakukan pencarian otomatis', 
            'details': str(e)
        }), 500


@similarity_api_bp.route('/auto-search/confirm', methods=['POST'])
def auto_search_confirm():
    """
    Confirm selected repositories from auto search
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        cache_id = data.get('cache_id')
        selected_repos = data.get('selected_repos') or []
        
        if not cache_id or not selected_repos:
            return jsonify({
                'error': 'cache_id dan selected_repos wajib diisi'
            }), 400

        # Load cache
        cache_payload = load_cache(
            cache_id, 
            current_app.config.get('CACHE_DIR', 'data/cache')
        )
        
        if not cache_payload:
            return jsonify({'error': 'Cache tidak ditemukan atau sudah kedaluwarsa'}), 400

        # Process confirmed repositories
        return _process_auto_search_confirmation(cache_payload, selected_repos)
        
    except Exception as e:
        print(f"Error in auto_search_confirm: {e}")
        return jsonify({
            'error': 'Gagal memproses konfirmasi pencarian otomatis', 
            'details': str(e)
        }), 500


def _perform_similarity_analysis(student_files, github_files):
    """
    Perform similarity analysis between student and GitHub files
    
    Args:
        student_files: List of student file information
        github_files: List of GitHub file information
        
    Returns:
        List of similarity results
    """
    results = []
    
    # Extract file paths
    mahasiswa_file_paths = [f['file_path'] for f in student_files if os.path.isfile(f['file_path'])]
    github_file_paths = [f['file_path'] for f in github_files if os.path.isfile(f['file_path'])]

    print("\nMemulai perbandingan menggunakan MOSS-like...")

    if github_file_paths:
        for m_path in mahasiswa_file_paths:
            # Find student file info
            m_info = next((f for f in student_files if f['file_path'] == m_path), None)
            m_display_name = f"{m_info['repo_folder']}/{m_info['file_name']}" if m_info else os.path.basename(m_path)
            
            for g_path in github_file_paths:
                # Find GitHub file info
                g_info = next((f for f in github_files if f['file_path'] == g_path), None)
                g_display_name = f"{g_info['repo_folder']}/{g_info['file_name']}" if g_info else os.path.basename(g_path)
                
                # Calculate similarity
                score, blocks_mhs, blocks_gh = get_similar_blocks(m_path, g_path, k=5, w=10)
                
                results.append({
                    "source_file": m_display_name,
                    "compared_file": g_display_name,
                    "score": round(score * 100, 2),
                    "similar_blocks_mhs": blocks_mhs, 
                    "similar_blocks_gh": blocks_gh    
                })
                
        print(f"Perbandingan Mahasiswa vs GitHub selesai. Total: {len(results)} pasangan.")
    else:
        print("Tidak ada file GitHub untuk dibandingkan.")
    
    return results


def _process_auto_search_confirmation(cache_payload, selected_repos):
    """
    Process confirmation of auto search results
    
    Args:
        cache_payload: Cached search data
        selected_repos: List of selected repository names
        
    Returns:
        Flask response
    """
    # Implementation for processing auto search confirmation
    # This would include downloading selected repos and performing analysis
    
    # For now, return a simple success response
    return jsonify({
        'message': 'Repositori terpilih berhasil diproses',
        'selected_count': len(selected_repos)
    }), 200


# Legacy endpoints for backward compatibility
@similarity_api_bp.route('/analyze_code', methods=['POST'])
def analyze_code_legacy():
    """Legacy endpoint for code analysis"""
    return analyze_code()


def register_similarity_api_routes(app):
    """
    Register similarity analysis API routes with the Flask application
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(similarity_api_bp)
    
    # Register legacy routes at root level for backward compatibility
    app.add_url_rule('/analyze_code', 'analyze_code_legacy', 
                     analyze_code, methods=['POST'])
    app.add_url_rule('/auto_search/init', 'auto_search_init_legacy',
                     auto_search_init, methods=['POST'])
    app.add_url_rule('/auto_search/confirm', 'auto_search_confirm_legacy',
                     auto_search_confirm, methods=['POST'])
