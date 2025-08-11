import os
import json
from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename

def load_env_file():
    """
    Manually load .env file if python-dotenv is not available
    """
    env_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"').strip("'")
                    os.environ[key] = value
        print(f"DEBUG: Loaded GITHUB_TOKEN from .env file")

# Try to load environment variables
try:
    from dotenv import load_dotenv
    # Load root .env if present
    load_dotenv()
    # Explicitly load config/.env (current project keeps token there)
    config_env_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
    if os.path.exists(config_env_path):
        load_dotenv(dotenv_path=config_env_path, override=True)
    # Fallback: if still no GITHUB_TOKEN, attempt manual loader
    if not os.getenv('GITHUB_TOKEN'):
        load_env_file()
except ImportError:
    print("DEBUG: python-dotenv not available, using manual .env loading")
    load_env_file()

# Import functions from reorganized structure
from src.scrapers.github_scraper import parse_github_blob_url_to_raw, download_raw_code, scrape_repo_files
from src.scrapers.github_search import auto_search_candidate_repos, load_cache
from src.algorithms.similarity_checker import preprocess_code, get_similar_blocks

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Konfigurasi direktori unggahan
UPLOAD_FOLDER_MAHASISWA = 'data/mahasiswa'
UPLOAD_FOLDER_GITHUB = 'data/github'

app.config['UPLOAD_FOLDER_MAHASISWA'] = UPLOAD_FOLDER_MAHASISWA
app.config['UPLOAD_FOLDER_GITHUB'] = UPLOAD_FOLDER_GITHUB

os.makedirs(UPLOAD_FOLDER_MAHASISWA, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_GITHUB, exist_ok=True)

# Helper functions (clear_student_files, clear_github_files, etc. - NO CHANGES)
def clear_student_files():
    print(f"Membersihkan folder: {app.config['UPLOAD_FOLDER_MAHASISWA']}")
    count = 0
    for filename in os.listdir(app.config['UPLOAD_FOLDER_MAHASISWA']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER_MAHASISWA'], filename)
        try:
            if os.path.isfile(file_path) and not file_path.endswith('.gitkeep'):
                os.unlink(file_path)
                count += 1
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
    print(f"Berhasil menghapus {count} file mahasiswa.")
    return count

def clear_github_files():
    print(f"Membersihkan folder: {app.config['UPLOAD_FOLDER_GITHUB']}")
    count = 0
    for filename in os.listdir(app.config['UPLOAD_FOLDER_GITHUB']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER_GITHUB'], filename)
        try:
            if os.path.isfile(file_path) and not file_path.endswith('.gitkeep'):
                os.unlink(file_path)
                count += 1
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
    print(f"Berhasil menghapus {count} file GitHub.")
    return count

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auto-search')
def auto_search_page():
    return render_template('auto_search.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/clear_mahasiswa_files', methods=['POST'])
def clear_mahasiswa_files_endpoint():
    try:
        clear_student_files()
        return jsonify({"message": "Semua file mahasiswa berhasil dihapus."}), 200
    except Exception as e:
        print(f"Error di endpoint /clear_mahasiswa_files: {e}")
        return jsonify({"error": "Gagal menghapus file mahasiswa.", "details": str(e)}), 500

@app.route('/clear_github_files', methods=['POST'])
def clear_github_files_endpoint():
    try:
        clear_github_files()
        return jsonify({"message": "Semua file GitHub berhasil dihapus."}), 200
    except Exception as e:
        print(f"Error di endpoint /clear_github_files: {e}")
        return jsonify({"error": "Gagal menghapus file GitHub.", "details": str(e)}), 500

# Endpoint: Untuk mengambil konten file kode asli (NO CHANGES)
@app.route('/get_code_content', methods=['POST'])
def get_code_content():
    data = request.get_json()
    filename = data.get('filename')
    file_type = data.get('file_type') # 'mahasiswa' atau 'github'

    if not filename or not file_type:
        return jsonify({"error": "Filename and file_type are required."}), 400

    base_dir = ""
    if file_type == 'mahasiswa':
        base_dir = app.config['UPLOAD_FOLDER_MAHASISWA']
    elif file_type == 'github':
        base_dir = app.config['UPLOAD_FOLDER_GITHUB']
    else:
        return jsonify({"error": "Invalid file_type."}), 400

    file_path = os.path.join(base_dir, filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found."}), 404
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return jsonify({"content": content}), 200
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return jsonify({"error": f"Could not read file content: {str(e)}"}), 500


# Endpoint untuk menjalankan analisis (NO CHANGES)
@app.route('/analyze_code', methods=['POST'])
def analyze_code():
    print("\n--- Memulai Analisis ---")
    
    clear_student_files() 
    
    student_repo_urls_str = request.form.get('student_repo_urls', '[]')
    try:
        student_repo_urls = json.loads(student_repo_urls_str)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON for student_repo_urls"}), 400

    print(f"URL Repositori Mahasiswa diterima: {student_repo_urls}")
    
    uploaded_student_files = [] 
    if not student_repo_urls:
        return jsonify({"error": "Mohon tambahkan setidaknya satu URL repositori mahasiswa."}), 400

    for repo_url in student_repo_urls:
        print(f"Mulai scraping repositori mahasiswa: {repo_url}")
        downloaded = scrape_repo_files(repo_url, app.config['UPLOAD_FOLDER_MAHASISWA'])
        uploaded_student_files.extend(downloaded)
        print(f"Selesai scraping {repo_url}. Total file dari repo ini: {len(downloaded)}")
    
    if not uploaded_student_files:
        return jsonify({
            "error": "Gagal mengunduh file kode dari repositori mahasiswa yang diberikan. "
                     "Pastikan URL repositori benar dan mengandung file kode yang didukung (mis. .js, .py, .java, dll.)."
        }), 400

    github_urls_str = request.form.get('github_urls', '[]')
    try:
        github_repo_urls = json.loads(github_urls_str)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON for github_urls"}), 400

    print(f"URL Repositori GitHub diterima: {github_repo_urls}")
    
    clear_github_files()

    scraped_github_files = []
    if github_repo_urls:
        for repo_url in github_repo_urls:
            print(f"Mulai scraping repositori pembanding: {repo_url}")
            downloaded = scrape_repo_files(repo_url, app.config['UPLOAD_FOLDER_GITHUB'])
            scraped_github_files.extend(downloaded)
            print(f"Selesai scraping {repo_url}. Total file dari repo ini: {len(downloaded)}")
        
        if not scraped_github_files:
            return jsonify({
                "error": "Gagal mengunduh file kode dari repositori GitHub pembanding yang diberikan. "
                         "Pastikan URL repositori benar dan mengandung file kode yang didukung (mis. .js, .py, .java, dll.)."
            }), 400
    else:
         print("Tidak ada URL GitHub pembanding yang diberikan.")

    results_mh_vs_gh = []

    mahasiswa_dir = app.config['UPLOAD_FOLDER_MAHASISWA']
    github_dir = app.config['UPLOAD_FOLDER_GITHUB']

    mahasiswa_file_paths = [os.path.join(mahasiswa_dir, f) for f in uploaded_student_files if os.path.isfile(os.path.join(mahasiswa_dir, f))]
    github_file_paths = [os.path.join(github_dir, f) for f in scraped_github_files if os.path.isfile(os.path.join(github_dir, f))]

    print("\nMemulai perbandingan menggunakan MOSS-like...")

    if github_file_paths:
        for m_path in mahasiswa_file_paths:
            m_filename = os.path.basename(m_path)
            for g_path in github_file_paths:
                g_filename = os.path.basename(g_path)
                score, blocks_mhs, blocks_gh = get_similar_blocks(m_path, g_path, k=5, w=10) # Sesuaikan k dan w jika perlu
                
                results_mh_vs_gh.append({
                    "source_file": m_filename,
                    "compared_file": g_filename,
                    "score": round(score * 100, 2),
                    "similar_blocks_mhs": blocks_mhs, 
                    "similar_blocks_gh": blocks_gh    
                })
        print(f"Perbandingan Mahasiswa vs GitHub selesai. Total: {len(results_mh_vs_gh)} pasangan.")
    else:
        print("Tidak ada file GitHub untuk dibandingkan.")
            
    print("Analisis selesai. Mengirim hasil.")
    return jsonify({
        "mh_vs_gh_results": results_mh_vs_gh,
    })

# ---------------- Auto Search Endpoints -----------------
@app.route('/auto_search/init', methods=['POST'])
def auto_search_init():
    data = request.get_json(force=True, silent=True) or {}
    student_repo_urls = data.get('student_repo_urls') or []
    if not isinstance(student_repo_urls, list) or not student_repo_urls:
        return jsonify({'error': 'student_repo_urls harus berupa list dan tidak boleh kosong'}), 400

    clear_student_files()
    try:
        cache_id, candidates = auto_search_candidate_repos(student_repo_urls, app.config['UPLOAD_FOLDER_MAHASISWA'], cache_dir='data/cache', top_n=5)
    except Exception as e:
        print(f"Error auto_search_candidate_repos: {e}")
        return jsonify({'error': 'Gagal melakukan pencarian otomatis', 'details': str(e)}), 500

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
    return jsonify({'cache_id': cache_id, 'candidates': response_candidates})

@app.route('/auto_search/confirm', methods=['POST'])
def auto_search_confirm():
    data = request.get_json(force=True, silent=True) or {}
    cache_id = data.get('cache_id')
    selected_repos = data.get('selected_repos') or []
    if not cache_id or not selected_repos:
        return jsonify({'error': 'cache_id dan selected_repos wajib diisi'}), 400

    cache_payload = load_cache(cache_id, 'data/cache')
    if not cache_payload:
        return jsonify({'error': 'Cache tidak ditemukan atau kadaluarsa'}), 404

    clear_github_files()
    for full_name in selected_repos:
        repo_url = f'https://github.com/{full_name}'
        print(f"[AUTO] Scraping selected repo: {repo_url}")
        scrape_repo_files(repo_url, app.config['UPLOAD_FOLDER_GITHUB'])

    results = []
    mahasiswa_dir = app.config['UPLOAD_FOLDER_MAHASISWA']
    github_dir = app.config['UPLOAD_FOLDER_GITHUB']
    mahasiswa_files = [f for f in os.listdir(mahasiswa_dir) if os.path.isfile(os.path.join(mahasiswa_dir, f))]
    github_files = [f for f in os.listdir(github_dir) if os.path.isfile(os.path.join(github_dir, f))]
    for m in mahasiswa_files:
        for g in github_files:
            m_path = os.path.join(mahasiswa_dir, m)
            g_path = os.path.join(github_dir, g)
            score, blocks_m, blocks_g = get_similar_blocks(m_path, g_path, k=5, w=10)
            results.append({
                'source_file': m,
                'compared_file': g,
                'score': round(score*100,2),
                'similar_blocks_mhs': blocks_m,
                'similar_blocks_gh': blocks_g
            })
    return jsonify({'mh_vs_auto_results': results})

# --- Hapus fungsi pembersihan saat shutdown ---
# def cleanup_on_shutdown_with_choice():
#     print("\n-------------------------------------------------")
#     print("Aplikasi Flask dimatikan.")
#     print("Apakah Anda ingin menghapus semua file repositori yang telah diunduh (data/mahasiswa dan data/github)?")
#     
#     choice = input("Ketik 'ya' untuk menghapus, atau 'tidak' untuk mempertahankan: ").lower().strip()
# 
#     if choice == 'ya':
#         print("Melakukan pembersihan data...")
#         clear_student_files()
#         clear_github_files()
#         print("Pembersihan data selesai.")
#     else:
#         print("File repositori dipertahankan.")
#     print("-------------------------------------------------")
# 
# if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
#     atexit.register(cleanup_on_shutdown_with_choice)


if __name__ == '__main__':
    app.run(debug=True)
