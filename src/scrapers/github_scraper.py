import requests
import os
import re
from urllib.parse import urlparse, urljoin

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
    try:
        r = requests.get(url, stream=True, timeout=10)
        r.raise_for_status()

        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except requests.exceptions.RequestException as e:
        print(f"Gagal mengunduh {url}: {e}")
        return False

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

def scrape_repo_files(repo_url, save_dir, allowed_extensions=('.js', '.py', '.java', '.c', '.cpp', '.h', '.html', '.css', '.scss', '.jsx', '.tsx', '.ts', '.txt', '.md', '.json', '.yml', '.yaml', '.xml', '.php', '.rb', '.go', '.rs', '.cs')):
    """
    Mengunduh semua file kode dari repositori GitHub ke direktori yang ditentukan.
    Menggunakan GitHub Contents API untuk akses yang lebih reliable ke private repos.
    """
    username, repo_name = get_github_repo_info(repo_url)
    if not username or not repo_name:
        print(f"URL repositori tidak valid: {repo_url}")
        return []

    # Buat folder untuk repository ini
    repo_folder_name = f"{username}_{repo_name}"
    repo_save_dir = os.path.join(save_dir, repo_folder_name)
    os.makedirs(repo_save_dir, exist_ok=True)

    # Setup headers dengan token jika ada
    headers = {}
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'

    print(f"Mengambil daftar file dari {repo_url}...")
    
    # Define folders and files to exclude (global untuk fungsi ini)
    excluded_folders = {
        'node_modules', '.git', '.github', 'vendor', 'dist', 'build', 
        'target', 'bin', 'obj', '.vs', '.vscode', '.idea', '__pycache__',
        'cache', 'logs', 'temp', 'tmp', '.next', '.nuxt', 'coverage',
        'assets', 'images', 'img', 
        'bower_components', 'jspm_packages', 'web_modules', '.bundle',
        'lib', 'libs', 'packages', '.yarn', '.npm'
    }
    
    excluded_files = {
        '.gitignore', '.gitattributes', 'README.md', 'readme.txt',
        'LICENSE', 'license.txt', '.env', '.env.local', '.env.production',
        'package-lock.json', 'yarn.lock', 'composer.lock', 'Gemfile.lock',
        '.DS_Store', 'Thumbs.db', '*.log', '*.tmp', '*.cache',
        '.eslintrc', '.prettierrc', '.babelrc', 'webpack.config.js',
        'gulpfile.js', 'gruntfile.js', 'tsconfig.json', 'jest.config.js'
    }
    
    def should_exclude_path(path):
        """Check if path should be excluded"""
        path_parts = path.split('/')
        
        # Check if any part of the path is an excluded folder
        for part in path_parts:
            if part.lower() in excluded_folders:
                return True
        
        # Check if filename is excluded
        filename = os.path.basename(path).lower()
        if filename in excluded_files:
            return True
            
        # Check for common patterns
        if any(pattern in filename for pattern in ['.min.', '.bundle.', '.compiled.']):
            return True
        
        # Check for binary/image/video files
        binary_extensions = {
            '.exe', '.dll', '.so', '.dylib', '.jar', '.war', '.ear',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
            '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
            '.mp3', '.wav', '.ogg', '.flac', '.aac',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'
        }
        
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext in binary_extensions:
            return True
            
        return False
    
    # Method 1: Gunakan Contents API untuk akses yang lebih reliable
    downloaded_files_info = []
    
    try:
        # Ambil repository info untuk mendapatkan default branch
        repo_response = requests.get(f'https://api.github.com/repos/{username}/{repo_name}', headers=headers, timeout=15)
        if repo_response.status_code == 200:
            repo_data = repo_response.json()
            default_branch = repo_data.get('default_branch', 'main')
            print(f"✅ Repository info - Default branch: {default_branch}")
        else:
            print(f"⚠️ Cannot get repo info, using default branch")
            default_branch = 'main'
    except Exception as e:
        print(f"⚠️ Error getting repo info: {e}")
        default_branch = 'main'
    
    # Method 1: Contents API (lebih reliable untuk private repos)
    try:
        files_found = []
        
        # Function recursive untuk mengambil files dari semua folder dengan optimasi
        def get_files_recursive(path="", depth=0):
            # Limit depth untuk mencegah traversal terlalu dalam
            if depth > 10:
                print(f"    ⚠️ Skipping deep path (depth {depth}): {path}")
                return
                
            # Skip if this path should be excluded
            if path and should_exclude_path(path):
                print(f"    ⏭️ Skipping excluded path: {path}")
                return
                
            url = f'https://api.github.com/repos/{username}/{repo_name}/contents'
            if path:
                url += f'/{path}'
            url += f'?ref={default_branch}'
            
            try:
                # Reduced timeout untuk responsiveness
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    items = response.json()
                    
                    # Batch process untuk efficiency
                    files_in_dir = []
                    dirs_to_process = []
                    
                    for item in items:
                        item_path = item.get('path', '')
                        
                        # Skip excluded paths
                        if should_exclude_path(item_path):
                            continue
                            
                        if item.get('type') == 'file':
                            file_ext = os.path.splitext(item_path)[1].lower()
                            if file_ext in allowed_extensions:
                                files_in_dir.append({
                                    'path': item_path,
                                    'download_url': item.get('download_url'),
                                    'name': item.get('name')
                                })
                        elif item.get('type') == 'dir':
                            dirs_to_process.append(item_path)
                    
                    # Add files found in this directory
                    files_found.extend(files_in_dir)
                    if files_in_dir:
                        print(f"    📂 Found {len(files_in_dir)} files in {path or 'root'}")
                    
                    # Recursively process directories
                    for dir_path in dirs_to_process:
                        get_files_recursive(dir_path, depth + 1)
                        
                elif response.status_code == 403:
                    print(f"    ⚠️ API rate limit hit - waiting...")
                    import time
                    time.sleep(2)  # Brief pause for rate limiting
                else:
                    print(f"    ⚠️ Cannot access path '{path}': {response.status_code}")
            except Exception as e:
                print(f"    ❌ Error accessing path '{path}': {e}")
        
        # Start recursive file discovery
        get_files_recursive()
        
        print(f"🔍 Ditemukan {len(files_found)} file kode untuk didownload")
        
        # Download file-file tersebut dengan optimasi
        from concurrent.futures import ThreadPoolExecutor
        import threading
        
        # Thread-safe list untuk hasil download
        download_results = []
        download_lock = threading.Lock()
        
        def download_single_file(file_info):
            """Download single file dengan error handling"""
            file_path = file_info['path']
            download_url = file_info['download_url']
            file_name = file_info['name']
            
            if not download_url:
                print(f"  ⚠️ No download URL for: {file_path}")
                return None
            
            # Simpan dengan nama file yang aman
            safe_filename = file_path.replace('/', '_').replace('\\', '_')
            save_path = os.path.join(repo_save_dir, safe_filename)

            if os.path.exists(save_path):
                print(f"  ⏭️ Already exists: {file_path}")
                with download_lock:
                    download_results.append({
                        'repo_folder': repo_folder_name,
                        'file_name': safe_filename,
                        'file_path': save_path,
                        'original_path': file_path
                    })
                return save_path
            
            try:
                print(f"  📥 Downloading: {file_path}")
                # Reduced timeout untuk responsiveness
                response = requests.get(download_url, timeout=15)
                if response.status_code == 200:
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                    
                    with download_lock:
                        download_results.append({
                            'repo_folder': repo_folder_name,
                            'file_name': safe_filename,
                            'file_path': save_path,
                            'original_path': file_path
                        })
                    
                    size_kb = len(response.content) / 1024
                    print(f"    ✅ Downloaded {file_path} ({size_kb:.1f} KB)")
                    return save_path
                else:
                    print(f"    ❌ Failed to download {file_path}: HTTP {response.status_code}")
                    return None
            except Exception as e:
                print(f"    ❌ Error downloading {file_path}: {e}")
                return None
        
        # Download files dengan thread pool (tapi batasi untuk menghindari rate limiting)
        max_workers = min(3, len(files_found))  # Limit concurrent downloads
        
        if len(files_found) <= 5:
            # For small number of files, use sequential download
            for file_info in files_found:
                download_single_file(file_info)
        else:
            # For larger number of files, use parallel download with limited workers
            print(f"  🚀 Starting parallel download with {max_workers} workers...")
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(download_single_file, file_info) for file_info in files_found]
                
                # Wait for all downloads to complete
                for future in futures:
                    try:
                        future.result(timeout=30)  # 30 second timeout per file
                    except Exception as e:
                        print(f"    ❌ Download thread error: {e}")
        
        downloaded_files_info = download_results
                
    except Exception as e:
        print(f"❌ Contents API error: {e}")
        print("🔄 Fallback to Tree API...")
        
        # Fallback: Tree API (method lama)
        branches_to_try = [default_branch, 'main', 'master', 'develop']
        tree_data = None
        used_branch = None
        
        for branch in branches_to_try:
            api_url = f"https://api.github.com/repos/{username}/{repo_name}/git/trees/{branch}?recursive=1"
            
            try:
                response = requests.get(api_url, headers=headers, timeout=15)
                if response.status_code == 200:
                    tree_data = response.json()
                    used_branch = branch
                    print(f"✅ Fallback - menggunakan branch: {branch}")
                    break
                elif response.status_code == 404:
                    print(f"⚠️ Branch '{branch}' tidak ditemukan, mencoba branch lain...")
                    continue
                else:
                    response.raise_for_status()
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Error accessing branch '{branch}': {e}")
                continue
        
        if tree_data and used_branch:
            files_to_download = []
            for item in tree_data.get('tree', []):
                if item['type'] == 'blob':
                    file_path = item['path']
                    
                    # Skip excluded paths using the same filter function
                    if should_exclude_path(file_path):
                        continue
                        
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext in allowed_extensions:
                        files_to_download.append(file_path)
            
            print(f"🔍 Fallback - ditemukan {len(files_to_download)} file untuk didownload")
            
            # Untuk tree API, coba gunakan Contents API per-file untuk mendapatkan download_url
            for file_path in files_to_download:
                safe_filename = file_path.replace('/', '_').replace('\\', '_')
                save_path = os.path.join(repo_save_dir, safe_filename)
                
                if not os.path.exists(save_path):
                    print(f"  📥 Mengunduh: {file_path}")
                    
                    # Coba ambil download_url via Contents API
                    try:
                        contents_url = f'https://api.github.com/repos/{username}/{repo_name}/contents/{file_path}?ref={used_branch}'
                        contents_response = requests.get(contents_url, headers=headers, timeout=15)
                        
                        if contents_response.status_code == 200:
                            contents_data = contents_response.json()
                            download_url = contents_data.get('download_url')
                            
                            if download_url:
                                dl_response = requests.get(download_url, timeout=30)
                                if dl_response.status_code == 200:
                                    with open(save_path, 'wb') as f:
                                        f.write(dl_response.content)
                                    
                                    downloaded_files_info.append({
                                        'repo_folder': repo_folder_name,
                                        'file_name': safe_filename,
                                        'file_path': save_path,
                                        'original_path': file_path
                                    })
                                    print(f"    ✅ Berhasil via Contents API")
                                else:
                                    print(f"    ❌ Download failed: {dl_response.status_code}")
                            else:
                                print(f"    ❌ No download URL available")
                        else:
                            print(f"    ❌ Contents API failed: {contents_response.status_code}")
                            
                    except Exception as e:
                        print(f"    ❌ Error: {e}")

    print(f"✅ Selesai mengunduh dari {repo_url}. Total: {len(downloaded_files_info)} file kode.")
    return downloaded_files_info

# Jika Anda ingin menguji scraper ini secara mandiri:
if __name__ == "__main__":
    # Contoh penggunaan untuk scraping repositori penuh
    repo_urls_to_scrape = [
        "https://github.com/Linzty/Muhammad_Dasril_Asdar-105841100321-lab1", # Ini adalah URL repo, bukan file
        # "https://github.com/Ahmadfaisal04/AHMAD-FAISAL---105841100121" # Contoh repo lain
    ]
    
    output_dir = "data/github"
    os.makedirs(output_dir, exist_ok=True)
    
    # Hapus folder GitHub lama sebelum mengunduh yang baru (opsional)
    for item in os.listdir(output_dir):
        item_path = os.path.join(output_dir, item)
        try:
            if os.path.isfile(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                import shutil
                shutil.rmtree(item_path)
        except Exception as e:
            print(f"Error deleting old github item {item_path}: {e}")

    all_downloaded_github_files = []
    for repo_url in repo_urls_to_scrape:
        downloaded = scrape_repo_files(repo_url, output_dir)
        all_downloaded_github_files.extend(downloaded)
    
    print("\nSemua file GitHub yang berhasil diunduh:")
    for f in all_downloaded_github_files:
        print(f"- {f['repo_folder']}/{f['file_name']} (dari {f['original_path']})")