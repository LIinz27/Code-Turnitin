import os
import json
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Import fungsi dari skrip Anda
from github_scraper import parse_github_blob_url_to_raw, download_raw_code
from similarity_checker import preprocess_code, jaccard_similarity

app = Flask(__name__)

# Konfigurasi direktori unggahan
UPLOAD_FOLDER_MAHASISWA = 'data/mahasiswa'
UPLOAD_FOLDER_GITHUB = 'data/github' # Direkomendasikan tetap menggunakan scraper untuk ini

app.config['UPLOAD_FOLDER_MAHASISWA'] = UPLOAD_FOLDER_MAHASISWA
app.config['UPLOAD_FOLDER_GITHUB'] = UPLOAD_FOLDER_GITHUB # Untuk konsistensi

# Pastikan direktori ada
os.makedirs(UPLOAD_FOLDER_MAHASISWA, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_GITHUB, exist_ok=True)

# Helper function to clear student files (optional, for fresh runs)
def clear_student_files():
    for filename in os.listdir(app.config['UPLOAD_FOLDER_MAHASISWA']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER_MAHASISWA'], filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

# Helper function to clear github files (optional, for fresh runs)
def clear_github_files():
    for filename in os.listdir(app.config['UPLOAD_FOLDER_GITHUB']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER_GITHUB'], filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

# --- API Endpoints ---

# Endpoint untuk menyajikan file statis (HTML, CSS, JS)
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    # Menyajikan file CSS dan JS
    return send_from_directory('.', filename)

# Endpoint untuk menjalankan analisis
@app.route('/analyze_code', methods=['POST'])
def analyze_code():
    # 1. Clear previous student files (optional, but good for fresh runs)
    clear_student_files()
    
    # 2. Handle Student File Uploads
    uploaded_student_files = []
    if 'student_files' not in request.files:
        return jsonify({"error": "No student_files part in the request"}), 400
    
    files = request.files.getlist('student_files')
    if not files:
        return jsonify({"error": "No selected student file"}), 400

    for file in files:
        if file.filename == '':
            return jsonify({"error": "No selected student file"}), 400
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER_MAHASISWA'], filename)
            file.save(file_path)
            uploaded_student_files.append(filename)
    
    print(f"Uploaded student files: {uploaded_student_files}")

    # 3. Handle GitHub URL Processing (and scraping)
    github_urls_str = request.form.get('github_urls', '[]')
    try:
        github_urls = json.loads(github_urls_str)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON for github_urls"}), 400

    print(f"Received GitHub URLs: {github_urls}")
    
    # Clear previous GitHub files if you want to re-scrape everything
    # clear_github_files() # Uncomment if you want to clear GitHub data on each run

    scraped_github_files = []
    for blob_url in github_urls:
        raw_url = parse_github_blob_url_to_raw(blob_url)
        if raw_url:
            # Extract relevant parts for a good filename
            try:
                parts = blob_url.split('/')
                user_name = parts[3]
                repo_name = parts[4]
                file_name_from_url = parts[-1]
                save_filename = f"{user_name}_{repo_name}_{file_name_from_url}"
                save_path = os.path.join(app.config['UPLOAD_FOLDER_GITHUB'], save_filename)
                
                # Only download if it doesn't already exist or if we want to force refresh
                if not os.path.exists(save_path):
                    if download_raw_code(raw_url, save_path):
                        scraped_github_files.append(save_filename)
                else:
                    print(f"File {save_filename} already exists, skipping download.")
                    scraped_github_files.append(save_filename) # Still include in list if exists
            except IndexError:
                print(f"Could not parse filename from {blob_url}. Skipping.")
        else:
            print(f"Invalid GitHub blob URL format: {blob_url}. Skipping.")

    print(f"Scraped GitHub files: {scraped_github_files}")

    # 4. Perform Similarity Check
    results_mh_vs_gh = []
    results_mh_vs_mh = []

    mahasiswa_dir = app.config['UPLOAD_FOLDER_MAHASISWA']
    github_dir = app.config['UPLOAD_FOLDER_GITHUB']

    # Load all student code tokens
    mahasiswa_codes = {}
    for m_file in uploaded_student_files: # Only process newly uploaded or existing in this run
        m_path = os.path.join(mahasiswa_dir, m_file)
        if os.path.isfile(m_path):
            mahasiswa_codes[m_file] = preprocess_code(m_path)

    # Load all github code tokens (only the ones we just scraped or already existed)
    github_codes = {}
    for g_file in scraped_github_files: # Only process newly scraped or existing in this run
        g_path = os.path.join(github_dir, g_file)
        if os.path.isfile(g_path):
            github_codes[g_file] = preprocess_code(g_path)


    # Compare Mahasiswa vs GitHub
    for m_file, tokens_m in mahasiswa_codes.items():
        for g_file, tokens_g in github_codes.items():
            score = jaccard_similarity(tokens_m, tokens_g)
            results_mh_vs_gh.append({
                "source_file": m_file,
                "compared_file": g_file,
                "score": round(score * 100, 2)
            })

    # Compare Mahasiswa vs Mahasiswa
    mahasiswa_files_list = list(mahasiswa_codes.keys())
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
            
    # 5. Return Results
    return jsonify({
        "mh_vs_gh_results": results_mh_vs_gh,
        "mh_vs_mh_results": results_mh_vs_mh
    })

if __name__ == '__main__':
    app.run(debug=True) # debug=True akan otomatis me-reload server saat ada perubahan kode