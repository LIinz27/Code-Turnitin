# main.py

import os
from github_scraper import download_raw_code # Akan disesuaikan
from similarity_checker import preprocess_code, jaccard_similarity # Akan disesuaikan

def run_github_scraper():
    print("Memulai pengunduhan kode dari GitHub...")
    # Contoh URL raw code GitHub
    # Anda perlu mengubah ini untuk mendapatkan URL raw yang benar, bukan URL blob.
    # Misalnya, Anda bisa membuat fungsi parse_github_blob_url_to_raw() di github_scraper.py
    urls = [
        "https://github.com/Ahmadfaisal04/AHMAD-FAISAL---105841100121/blob/master/App.js",
        "https://github.com/Linzty/Muhammad_Dasril_Asdar-105841100321-lab1/blob/main/App.js",
        "https://github.com/Linzty/Muhammad_Dasril_Asdar-105841100321-lab1/blob/main/font.js"
    ]

    os.makedirs("data/github", exist_ok=True)

    # *** PENTING: Perbarui fungsi download_raw_code di github_scraper.py
    # untuk mengunduh konten raw, bukan halaman blob.
    # Contoh dasar (Anda harus mengimplementasikan logika parsing URL):
    # for i, url in enumerate(urls):
    #     raw_url = parse_github_blob_url_to_raw(url) # Ini perlu diimplementasikan
    #     if raw_url:
    #         save_path = f"data/github/github_code_{i}_{os.path.basename(url).replace('.js', '')}.js" # Contoh nama file
    #         download_raw_code(raw_url, save_path)
    #         print(f"Mengunduh {raw_url} ke {save_path}")
    #     else:
    #         print(f"Gagal mem-parsing URL: {url}")
    
    # Untuk sementara, saya akan biarkan seperti kode Anda, tapi ingat ini perlu diubah
    for i, url in enumerate(urls):
        # Anda perlu mem-parsing URL di sini untuk mendapatkan URL raw content
        # Contoh sederhana (TIDAK AKURAT, HANYA ILUSTRASI):
        raw_url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        
        # Ekstrak nama file dari URL untuk nama penyimpanan yang lebih baik
        file_name = url.split('/')[-1]
        repo_name = url.split('/')[-3] # Mungkin nama repo
        user_name = url.split('/')[-4] # Mungkin nama user

        save_path = f"data/github/{user_name}_{repo_name}_{file_name}"
        
        print(f"Mengunduh {raw_url} ke {save_path}")
        download_raw_code(raw_url, save_path)
        print(f"Selesai mengunduh.")

def run_similarity_check():
    print("\nMemulai deteksi kemiripan kode...")
    
    # Perbandingan Mahasiswa vs GitHub
    print("\n--- Mahasiswa vs GitHub ---")
    results_mh_vs_gh = []
    mahasiswa_dir = "data/mahasiswa"
    github_dir = "data/github"

    # Pastikan direktori mahasiswa ada dan berisi file
    if not os.path.exists(mahasiswa_dir) or not os.listdir(mahasiswa_dir):
        print(f"Direktori '{mahasiswa_dir}' kosong atau tidak ada. Mohon masukkan file kode mahasiswa.")
        return

    # Pastikan direktori github ada dan berisi file
    if not os.path.exists(github_dir) or not os.listdir(github_dir):
        print(f"Direktori '{github_dir}' kosong atau tidak ada. Mohon jalankan scraper GitHub.")
        return

    for m_file in os.listdir(mahasiswa_dir):
        m_path = os.path.join(mahasiswa_dir, m_file)
        if not os.path.isfile(m_path): # Skip directories
            continue
        tokens_m = preprocess_code(m_path)

        for g_file in os.listdir(github_dir):
            g_path = os.path.join(github_dir, g_file)
            if not os.path.isfile(g_path): # Skip directories
                continue
            tokens_g = preprocess_code(g_path)

            score = jaccard_similarity(tokens_m, tokens_g)
            results_mh_vs_gh.append({
                "source_file": m_file,
                "compared_file": g_file,
                "score": round(score * 100, 2),
                "type": "Mahasiswa vs GitHub"
            })
    
    for r in sorted(results_mh_vs_gh, key=lambda x: x['score'], reverse=True):
        if r['score'] > 0: # Hanya tampilkan jika ada kemiripan
            print(f"{r['source_file']} vs {r['compared_file']} → {r['score']}% mirip")

    # Perbandingan Mahasiswa vs Mahasiswa (Penting untuk Turnitin)
    print("\n--- Mahasiswa vs Mahasiswa ---")
    results_mh_vs_mh = []
    mahasiswa_files = [os.path.join(mahasiswa_dir, f) for f in os.listdir(mahasiswa_dir) if os.path.isfile(os.path.join(mahasiswa_dir, f))]

    for i in range(len(mahasiswa_files)):
        for j in range(i + 1, len(mahasiswa_files)): # Hindari perbandingan dengan diri sendiri dan duplikat
            file1_path = mahasiswa_files[i]
            file2_path = mahasiswa_files[j]

            tokens1 = preprocess_code(file1_path)
            tokens2 = preprocess_code(file2_path)

            score = jaccard_similarity(tokens1, tokens2)
            results_mh_vs_mh.append({
                "source_file": os.path.basename(file1_path),
                "compared_file": os.path.basename(file2_path),
                "score": round(score * 100, 2),
                "type": "Mahasiswa vs Mahasiswa"
            })
    
    for r in sorted(results_mh_vs_mh, key=lambda x: x['score'], reverse=True):
        if r['score'] > 0: # Hanya tampilkan jika ada kemiripan
            print(f"{r['source_file']} vs {r['compared_file']} → {r['score']}% mirip")


if __name__ == "__main__":
    # Buat direktori data jika belum ada
    os.makedirs("data/mahasiswa", exist_ok=True)
    os.makedirs("data/github", exist_ok=True)

    print("Selamat datang di Code Turnitin Project!")
    print("Pastikan Anda memiliki file kode mahasiswa di 'data/mahasiswa'.")
    print("--------------------------------------------------")

    choice = input("Pilih aksi:\n1. Unduh kode GitHub (Jalankan Scraper)\n2. Periksa Kemiripan Kode\nPilihan Anda (1/2): ")

    if choice == '1':
        run_github_scraper()
    elif choice == '2':
        run_similarity_check()
    else:
        print("Pilihan tidak valid.")