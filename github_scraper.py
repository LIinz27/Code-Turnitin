import requests
import os
import re
from urllib.parse import urlparse, urljoin

# Fungsi yang sudah ada (parse_github_blob_url_to_raw dan download_raw_code) tetap sama

def parse_github_blob_url_to_raw(blob_url):
    """
    Mengubah URL GitHub 'blob' menjadi URL konten raw.
    Contoh:
    https://github.com/user/repo/blob/branch/path/to/file.js
    menjadi
    https://raw.githubusercontent.com/user/repo/branch/path/to/file.js
    """
    match = re.match(r'https://github.com/([^/]+)/([^/]+)/blob/([^/]+)/(.*)', blob_url)
    if match:
        user, repo, branch, path = match.groups()
        raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}"
        return raw_url
    return None

def download_raw_code(url, save_path):
    """
    Mengunduh konten raw dari URL ke path penyimpanan.
    """
    # print(f"Mengunduh dari: {url}") # Uncomment for debugging
    try:
        r = requests.get(url, stream=True, timeout=10) # Tambahkan timeout
        r.raise_for_status() # Akan memunculkan HTTPError untuk status kode 4xx/5xx

        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        # print(f"Berhasil mengunduh ke: {save_path}") # Uncomment for debugging
        return True
    except requests.exceptions.RequestException as e:
        print(f"Gagal mengunduh {url}: {e}")
        return False

# --- FUNGSI BARU UNTUK MENGUNDUH SELURUH REPO ---
def get_github_repo_info(repo_url):
    """
    Mengekstrak username, repository name dari URL repo GitHub.
    Contoh: https://github.com/user/repo -> user, repo
    """
    parsed_url = urlparse(repo_url)
    path_segments = [s for s in parsed_url.path.split('/') if s]
    if len(path_segments) >= 2:
        username = path_segments[0]
        repo_name = path_segments[1]
        return username, repo_name
    return None, None

def scrape_repo_files(repo_url, save_dir, allowed_extensions=('.js', '.py', '.java', '.c', '.cpp', '.h')):
    """
    Mengunduh semua file kode dari repositori GitHub ke direktori yang ditentukan.
    Menggunakan GitHub API untuk mendapatkan daftar file.
    """
    username, repo_name = get_github_repo_info(repo_url)
    if not username or not repo_name:
        print(f"URL repositori tidak valid: {repo_url}")
        return []

    api_url = f"https://api.github.com/repos/{username}/{repo_name}/git/trees/main?recursive=1"
    # Atau 'master' jika 'main' tidak ada. Bisa juga deteksi default branch.
    # Untuk skripsi, gunakan default branch atau parameterkan.

    headers = {}
    # Anda bisa menambahkan Personal Access Token (PAT) di sini untuk rate limit yang lebih tinggi:
    # GITHUB_TOKEN = os.getenv('GITHUB_TOKEN') # Pastikan Anda menyetel environment variable ini
    # if GITHUB_TOKEN:
    #     headers['Authorization'] = f'token {GITHUB_TOKEN}'

    print(f"Mengambil daftar file dari {repo_url}...")
    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        tree_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Gagal mengambil daftar file dari API GitHub {api_url}: {e}")
        return []

    downloaded_files_names = []
    if 'tree' in tree_data:
        for item in tree_data['tree']:
            if item['type'] == 'blob': # 'blob' berarti file
                file_path = item['path']
                file_ext = os.path.splitext(file_path)[1].lower()

                if file_ext in allowed_extensions:
                    raw_file_url = f"https://raw.githubusercontent.com/{username}/{repo_name}/main/{file_path}"
                    # Pastikan 'main' cocok dengan branch yang Anda ambil dari API.
                    # Jika 'main' tidak ditemukan, coba 'master' atau ambil dari response API.

                    # Buat nama file unik untuk penyimpanan lokal
                    local_filename = f"{username}_{repo_name}_{file_path.replace('/', '_')}"
                    save_path = os.path.join(save_dir, local_filename)

                    if not os.path.exists(save_path):
                        print(f"  Mengunduh: {file_path}")
                        if download_raw_code(raw_file_url, save_path):
                            downloaded_files_names.append(local_filename)
                    else:
                        # print(f"  Sudah ada: {file_path}") # Uncomment if you want to see skipped files
                        downloaded_files_names.append(local_filename) # Masih anggap ini sebagai file yang "diambil"

    print(f"Selesai mengunduh file dari {repo_url}. Total: {len(downloaded_files_names)} file kode.")
    return downloaded_files_names

# Jika Anda ingin menguji scraper ini secara mandiri:
if __name__ == "__main__":
    # Contoh penggunaan untuk scraping repositori penuh
    repo_urls_to_scrape = [
        "https://github.com/Linzty/Muhammad_Dasril_Asdar-105841100321-lab1", # Ini adalah URL repo, bukan file
        # "https://github.com/Ahmadfaisal04/AHMAD-FAISAL---105841100121" # Contoh repo lain
    ]
    
    output_dir = "data/github"
    os.makedirs(output_dir, exist_ok=True)
    
    # Hapus file GitHub lama sebelum mengunduh yang baru (opsional)
    for filename in os.listdir(output_dir):
        file_path = os.path.join(output_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting old github file {file_path}: {e}")

    all_downloaded_github_files = []
    for repo_url in repo_urls_to_scrape:
        downloaded = scrape_repo_files(repo_url, output_dir)
        all_downloaded_github_files.extend(downloaded)
    
    print("\nSemua file GitHub yang berhasil diunduh:")
    for f in all_downloaded_github_files:
        print(f"- {f}")