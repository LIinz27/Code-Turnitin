import os
import json
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import atexit

# Import fungsi dari skrip Anda
from github_scraper import parse_github_blob_url_to_raw, download_raw_code, scrape_repo_files
from similarity_checker import preprocess_code, compare_code_moss_like # UBAH IMPORT DI SINI

app = Flask(__name__)

# Konfigurasi direktori unggahan (NO CHANGES)
UPLOAD_FOLDER_MAHASISWA = 'data/mahasiswa'
UPLOAD_FOLDER_GITHUB = 'data/github'

app.config['UPLOAD_FOLDER_MAHASISWA'] = UPLOAD_FOLDER_MAHASISWA
app.config['UPLOAD_FOLDER_GITHUB'] = UPLOAD_FOLDER_GITHUB

os.makedirs(UPLOAD_FOLDER_MAHASISWA, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_GITHUB, exist_ok=True)

# Helper functions (clear_student_files, clear_github_files, index, serve_static, clear_mahasiswa_files_endpoint, clear_github_files_endpoint - NO CHANGES)
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
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

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


# Endpoint untuk menjalankan analisis (UBAH BAGIAN PERBANDINGAN)
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

    # --- BAGIAN PERBANDINGAN YANG DIUBAH ---
    # Load all student code paths
    mahasiswa_file_paths = [os.path.join(mahasiswa_dir, f) for f in uploaded_student_files if os.path.isfile(os.path.join(mahasiswa_dir, f))]

    # Load all github code paths
    github_file_paths = [os.path.join(github_dir, f) for f in scraped_github_files if os.path.isfile(os.path.join(github_dir, f))]

    print("\nMemulai perbandingan menggunakan MOSS-like...")

    if github_file_paths: # Hanya bandingkan jika ada file GitHub
        for m_path in mahasiswa_file_paths:
            m_filename = os.path.basename(m_path)
            for g_path in github_file_paths:
                g_filename = os.path.basename(g_path)
                # Panggil fungsi perbandingan MOSS-like yang baru
                score = compare_code_moss_like(m_path, g_path, k=5, w=10) # Sesuaikan k dan w jika perlu
                results_mh_vs_gh.append({
                    "source_file": m_filename,
                    "compared_file": g_filename,
                    "score": round(score * 100, 2)
                })
        print(f"Perbandingan Mahasiswa vs GitHub selesai. Total: {len(results_mh_vs_gh)} pasangan.")
    else:
        print("Tidak ada file GitHub untuk dibandingkan.")
            
    print("Analisis selesai. Mengirim hasil.")
    return jsonify({
        "mh_vs_gh_results": results_mh_vs_gh,
    })

# --- FUNGSI UNTUK PEMBERSIHAN SAAT SHUTDOWN (DENGAN PILIHAN) - NO CHANGES ---
def cleanup_on_shutdown_with_choice():
    print("\n-------------------------------------------------")
    print("Aplikasi Flask dimatikan.")
    print("Apakah Anda ingin menghapus semua file repositori yang telah diunduh (data/mahasiswa dan data/github)?")
    
    choice = input("Ketik 'ya' untuk menghapus, atau 'tidak' untuk mempertahankan: ").lower().strip()

    if choice == 'ya':
        print("Melakukan pembersihan data...")
        clear_student_files()
        clear_github_files()
        print("Pembersihan data selesai.")
    else:
        print("File repositori dipertahankan.")
    print("-------------------------------------------------")

if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    atexit.register(cleanup_on_shutdown_with_choice)


if __name__ == '__main__':
    app.run(debug=True)