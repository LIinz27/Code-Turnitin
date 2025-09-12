"""
Similarity Analysis API Routes
Handles code similarity analysis functionality
"""
import json
import os
from flask import Blueprint, request, jsonify, current_app
from ..scrapers.github_scraper import scrape_repo_files
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
        failed_repos = []
        
        for repo_url in student_repo_urls:
            print(f"Mulai scraping repositori mahasiswa: {repo_url}")
            try:
                downloaded = scrape_repo_files(repo_url, current_app.config['UPLOAD_FOLDER_MAHASISWA'])
                uploaded_student_files.extend(downloaded)
                print(f"Selesai scraping {repo_url}. Total file dari repo ini: {len(downloaded)}")
                
                if len(downloaded) == 0:
                    failed_repos.append(repo_url)
                    
            except Exception as e:
                print(f"Error scraping {repo_url}: {e}")
                failed_repos.append(repo_url)
        
        if not uploaded_student_files:
            error_msg = "Gagal mengunduh file kode dari repositori mahasiswa yang diberikan."
            
            if failed_repos:
                error_msg += "\n\nKemungkinan penyebab:"
                error_msg += "\n• Repository adalah private dan memerlukan GitHub token"
                error_msg += "\n• URL repository tidak valid"
                error_msg += "\n• Repository kosong atau tidak mengandung file kode yang didukung"
                error_msg += "\n• Masalah koneksi internet"
                
                if len(failed_repos) > 0:
                    error_msg += f"\n\nRepository yang gagal: {', '.join(failed_repos)}"
            
            return jsonify({
                "error": error_msg,
                "failed_repos": failed_repos,
                "suggestion": "Untuk repository private, tambahkan GITHUB_TOKEN ke environment variables atau gunakan repository public."
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
