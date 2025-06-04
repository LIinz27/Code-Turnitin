import os
import json
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Import fungsi dari skrip Anda
from github_scraper import parse_github_blob_url_to_raw, download_raw_code, scrape_repo_files
from similarity_checker import preprocess_code, jaccard_similarity

app = Flask(__name__)

# Konfigurasi direktori unggahan
UPLOAD_FOLDER_MAHASISWA = 'data/mahasiswa'
UPLOAD_FOLDER_GITHUB = 'data/github'

app.config['UPLOAD_FOLDER_MAHASISWA'] = UPLOAD_FOLDER_MAHASISWA
app.config['UPLOAD_FOLDER_GITHUB'] = UPLOAD_FOLDER_GITHUB

# Pastikan direktori ada
os.makedirs(UPLOAD_FOLDER_MAHASISWA, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_GITHUB, exist_ok=True)

# Helper function to clear student files (optional, for fresh runs)
def clear_student_files():
    print(f"Membersihkan folder: {app.config['UPLOAD_FOLDER_MAHASISWA']}")
    count = 0
    for filename in os.listdir(app.config['UPLOAD_FOLDER_MAHASISWA']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER_MAHASISWA'], filename)
        try:
            # Pastikan hanya menghapus file, bukan subdirektori atau file khusus seperti .gitkeep
            if os.path.isfile(file_path) and not file_path.endswith('.gitkeep'):
                os.unlink(file_path)
                count += 1
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
    print(f"Berhasil menghapus {count} file mahasiswa.")
    return count

# Helper function to clear github files (optional, for fresh runs)
def clear_github_files():
    print(f"Membersihkan folder: {app.config['UPLOAD_FOLDER_GITHUB']}")
    count = 0
    for filename in os.listdir(app.config['UPLOAD_FOLDER_GITHUB']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER_GITHUB'], filename)
        try:
            # Pastikan hanya menghapus file, bukan subdirektori atau file khusus seperti .gitkeep
            if os.path.isfile(file_path) and not file_path.endswith('.gitkeep'):
                os.unlink(file_path)
                count += 1
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
    print(f"Berhasil menghapus {count} file GitHub.")
    return count

# --- API Endpoints ---

# Endpoint untuk menyajikan file statis (HTML, CSS, JS)
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    # Menyajikan file CSS dan JS
    return send_from_directory('.', filename)

# NEW ENDPOINT: Clear Mahasiswa Files
@app.route('/clear_mahasiswa_files', methods=['POST'])
def clear_mahasiswa_files_endpoint():
    try:
        clear_student_files()
        return jsonify({"message": "Semua file mahasiswa berhasil dihapus."}), 200
    except Exception as e:
        print(f"Error di endpoint /clear_mahasiswa_files: {e}")
        return jsonify({"error": "Gagal menghapus file mahasiswa.", "details": str(e)}), 500

# NEW ENDPOINT: Clear GitHub Files
@app.route('/clear_github_files', methods=['POST'])
def clear_github_files_endpoint():
    try:
        clear_github_files()
        return jsonify({"message": "Semua file GitHub berhasil dihapus."}), 200
    except Exception as e:
        print(f"Error di endpoint /clear_github_files: {e}")
        return jsonify({"error": "Gagal menghapus file GitHub.", "details": str(e)}), 500


# Endpoint untuk menjalankan analisis
@app.route('/analyze_code', methods=['POST'])
def analyze_code():
    print("\n--- Memulai Analisis ---")
    
    # 1. Clear previous student files for a fresh run
    # Kita tetap memanggil ini karena setiap kali analisis dijalankan, kita menganggap unggahan yang baru adalah input utama.
    clear_student_files() 
    
    # 2. Handle Student File Uploads
    uploaded_student_files = []
    if 'student_files' not in request.files:
        print("No 'student_files' part in the request. Continuing without student files.")
    else:
        files = request.files.getlist('student_files')
        if not files or all(f.filename == '' for f in files):
            print("No selected student file(s).")
        else:
            for file in files:
                if file.filename: # Pastikan nama file tidak kosong
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER_MAHASISWA'], filename)
                    file.save(file_path)
                    uploaded_student_files.append(filename)
            print(f"File mahasiswa diunggah: {uploaded_student_files}")
    
    if not uploaded_student_files:
        return jsonify({"error": "Mohon unggah setidaknya satu file kode mahasiswa."}), 400

    # 3. Handle GitHub Repository URLs (and scraping)
    github_urls_str = request.form.get('github_urls', '[]')
    try:
        github_repo_urls = json.loads(github_urls_str) # Kini ini adalah URL repo
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON for github_urls"}), 400

    print(f"URL Repositori GitHub diterima: {github_repo_urls}")
    
    # Clear previous GitHub files (penting jika Anda ingin selalu scrape ulang)
    clear_github_files()

    scraped_github_files = []
    for repo_url in github_repo_urls:
        print(f"Mulai scraping repositori: {repo_url}")
        # Panggil fungsi scrape_repo_files yang baru
        downloaded = scrape_repo_files(repo_url, app.config['UPLOAD_FOLDER_GITHUB'])
        scraped_github_files.extend(downloaded)
        print(f"Selesai scraping {repo_url}. Total file dari repo ini: {len(downloaded)}")
    
    if not scraped_github_files and github_repo_urls: # Jika ada URL tapi tidak ada file yang di-scrape
        print("Tidak ada file kode yang ditemukan dari URL GitHub yang diberikan atau terjadi masalah saat scraping.")
        # Anda bisa memilih untuk mengembalikan error di sini jika file GitHub wajib ada
        # return jsonify({"error": "Tidak ada file GitHub yang berhasil di-scrape atau diunduh dari URL yang diberikan."}), 400
    elif not scraped_github_files and not github_repo_urls:
         print("Tidak ada URL GitHub yang diberikan.")


    # 4. Perform Similarity Check
    results_mh_vs_gh = []
    results_mh_vs_mh = []

    mahasiswa_dir = app.config['UPLOAD_FOLDER_MAHASISWA']
    github_dir = app.config['UPLOAD_FOLDER_GITHUB']

    # Load all student code tokens
    mahasiswa_codes = {}
    for m_file in uploaded_student_files:
        m_path = os.path.join(mahasiswa_dir, m_file)
        if os.path.isfile(m_path):
            mahasiswa_codes[m_file] = preprocess_code(m_path)

    # Load all github code tokens (only the ones we just scraped or already existed from repo scrape)
    github_codes = {}
    for g_file in scraped_github_files:
        g_path = os.path.join(github_dir, g_file)
        if os.path.isfile(g_path):
            github_codes[g_file] = preprocess_code(g_path)

    print("\nMemulai perbandingan...")

    # Compare Mahasiswa vs GitHub
    if github_codes: # Hanya bandingkan jika ada file GitHub
        for m_file, tokens_m in mahasiswa_codes.items():
            for g_file, tokens_g in github_codes.items():
                score = jaccard_similarity(tokens_m, tokens_g)
                results_mh_vs_gh.append({
                    "source_file": m_file,
                    "compared_file": g_file,
                    "score": round(score * 100, 2)
                })
        print(f"Perbandingan Mahasiswa vs GitHub selesai. Total: {len(results_mh_vs_gh)} pasangan.")
    else:
        print("Tidak ada file GitHub untuk dibandingkan.")

    # Compare Mahasiswa vs Mahasiswa
    mahasiswa_files_list = list(mahasiswa_codes.keys())
    if len(mahasiswa_files_list) > 1: # Hanya bandingkan jika ada lebih dari 1 file mahasiswa
        for i in range(len(mahasiswa_files_list)):
            for j in range(i + 1, len(mahasiswa_files_list)):
                file1 = mahasiswa_files_list[i]
                file2 = mahasiswa_files_list[j]
                
                tokens1 = mahasiswa_codes[file1]
                tokens2 = mahasiswa_codes[file2]
                
                score = jaccard_similarity(tokens1, tokens2)
                results_mh_vs_mh.append({
                    "file1": file1,
                    "file2": file2,
                    "score": round(score * 100, 2)
                })
        print(f"Perbandingan Mahasiswa vs Mahasiswa selesai. Total: {len(results_mh_vs_mh)} pasangan.")
    else:
        print("Tidak cukup file mahasiswa untuk perbandingan antar-mahasiswa.")
            
    # 5. Return Results
    print("Analisis selesai. Mengirim hasil.")
    return jsonify({
        "mh_vs_gh_results": results_mh_vs_gh,
        "mh_vs_mh_results": results_mh_vs_mh
    })

if __name__ == '__main__':
    app.run(debug=True)