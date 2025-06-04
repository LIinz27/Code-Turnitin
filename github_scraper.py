# github_scraper.py (DIUBAH)

import requests
from bs4 import BeautifulSoup
import os
import re

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
    print(f"Mengunduh dari: {url}")
    try:
        r = requests.get(url, stream=True) # Gunakan stream untuk file besar
        r.raise_for_status() # Akan memunculkan HTTPError untuk status kode 4xx/5xx

        # Pastikan kita mendapatkan teks, bukan HTML
        # Jika URL adalah blob, kemungkinan besar kontennya HTML
        if "github.com/blob" in url and "raw.githubusercontent.com" not in url:
            print(f"Peringatan: URL {url} tampaknya adalah URL 'blob' GitHub. Pastikan Anda mengunduh konten raw.")
            # Anda bisa menambahkan logika di sini untuk mem-parsing HTML jika ingin mencoba mengekstrak kode
            # Atau, lebih baik lagi, pastikan URL yang masuk adalah URL raw yang benar.
            # return False # Atau tangani lebih lanjut

        with open(save_path, "wb") as f: # Gunakan 'wb' untuk konten biner
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Berhasil mengunduh ke: {save_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Gagal mengunduh {url}: {e}")
        return False

# Contoh URL raw code GitHub (Anda perlu menyesuaikan ini)
# Ini adalah daftar URL blob, yang harus diubah ke raw sebelum diunduh
urls_blob = [
    "https://github.com/Ahmadfaisal04/AHMAD-FAISAL---105841100121/blob/master/App.js",
    "https://github.com/Linzty/Muhammad_Dasril_Asdar-105841100321-lab1/blob/main/App.js",
    "https://github.com/Linzty/Muhammad_Dasril_Asdar-105841100321-lab1/blob/main/font.js"
]

if __name__ == "__main__":
    os.makedirs("data/github", exist_ok=True)
    
    for i, blob_url in enumerate(urls_blob):
        raw_url = parse_github_blob_url_to_raw(blob_url)
        if raw_url:
            # Ekstrak nama file dari URL blob untuk nama penyimpanan yang lebih baik
            file_name = blob_url.split('/')[-1]
            repo_name = blob_url.split('/')[-3]
            user_name = blob_url.split('/')[-4]
            
            # Buat nama file yang lebih unik dan informatif
            save_path = f"data/github/{user_name}_{repo_name}_{file_name}"
            
            download_raw_code(raw_url, save_path)
        else:
            print(f"Tidak dapat mem-parsing URL blob: {blob_url}. Melewati.")