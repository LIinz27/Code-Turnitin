# similarity_checker.py (DIUBAH UNTUK JS)

import os
import re

def preprocess_code(path):
    """
    Membaca file kode, menghapus komentar, menormalisasi spasi, dan
    mengembalikan set token.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        print(f"Error membaca file {path}: {e}")
        return set()

    # Hapus komentar Python (opsional, jika Anda hanya fokus pada JS)
    code = re.sub(r'#[^\n]*', '', code)
    
    # Hapus komentar JavaScript (single-line // dan multi-line /* ... */)
    code = re.sub(r'//[^\n]*', '', code)
    code = re.sub(r'/\*[\s\S]*?\*/', '', code)

    # Hapus string literals (agar tidak dianggap token yang berbeda hanya karena nilai string berbeda)
    # Ini bisa jadi rumit, tergantung seberapa agresif Anda ingin menormalisasi.
    # Contoh sederhana: ganti semua string dengan placeholder
    code = re.sub(r'"[^"]*"', 'STRING_LITERAL', code)
    code = re.sub(r"'[^']*'", 'STRING_LITERAL', code)
    code = re.sub(r'`[^`]*`', 'STRING_LITERAL', code)

    # Normalisasi spasi: ganti baris baru dan spasi berlebih dengan satu spasi
    code = re.sub(r'[\s]+', ' ', code)
    
    # Konversi ke huruf kecil (opsional, bisa mengurangi akurasi jika case-sensitivity penting)
    # code = code.lower()

    # Tokenisasi: pisahkan berdasarkan non-alfanumerik dan non-underscore
    # Ini akan memisahkan operator, kurung kurawal, dll.
    tokens = re.findall(r'[a-zA-Z0-9_]+', code)
    return set(tokens)

def jaccard_similarity(tokens_a, tokens_b):
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    if not union: # Hindari pembagian dengan nol
        return 0.0
    return len(intersection) / len(union)

# Bagian compare_all dan main __name__ == "__main__": bisa Anda gunakan di main.py sekarang
# Jika Anda ingin tetap bisa menjalankan similarity_checker.py secara mandiri:
if __name__ == "__main__":
    hasil = []
    mahasiswa_dir = "data/mahasiswa"
    github_dir = "data/github"

    # Pastikan direktori mahasiswa ada dan berisi file
    if not os.path.exists(mahasiswa_dir) or not os.listdir(mahasiswa_dir):
        print(f"Direktori '{mahasiswa_dir}' kosong atau tidak ada. Mohon masukkan file kode mahasiswa.")
    else:
        # Load all student code tokens once
        mahasiswa_codes = {}
        for m_file in os.listdir(mahasiswa_dir):
            m_path = os.path.join(mahasiswa_dir, m_file)
            if os.path.isfile(m_path):
                mahasiswa_codes[m_file] = preprocess_code(m_path)

        # Load all github code tokens once
        github_codes = {}
        if not os.path.exists(github_dir) or not os.listdir(github_dir):
            print(f"Direktori '{github_dir}' kosong atau tidak ada. Mohon jalankan scraper GitHub.")
        else:
            for g_file in os.listdir(github_dir):
                g_path = os.path.join(github_dir, g_file)
                if os.path.isfile(g_path):
                    github_codes[g_file] = preprocess_code(g_path)

        # Compare Mahasiswa vs GitHub
        print("Hasil Deteksi Kemiripan Kode Mahasiswa vs GitHub:\n")
        for m_file, tokens_m in mahasiswa_codes.items():
            for g_file, tokens_g in github_codes.items():
                score = jaccard_similarity(tokens_m, tokens_g)
                hasil.append({
                    "mahasiswa_file": m_file,
                    "github_file": g_file,
                    "score": round(score * 100, 2)
                })
        
        for r in sorted(hasil, key=lambda x: x['score'], reverse=True):
            if r['score'] > 0:
                print(f"{r['mahasiswa_file']} vs {r['github_file']} → {r['score']}% mirip")
        
        # Compare Mahasiswa vs Mahasiswa
        print("\nHasil Deteksi Kemiripan Kode Mahasiswa vs Mahasiswa:\n")
        hasil_mh_mh = []
        mahasiswa_files_list = list(mahasiswa_codes.keys())
        for i in range(len(mahasiswa_files_list)):
            for j in range(i + 1, len(mahasiswa_files_list)):
                file1 = mahasiswa_files_list[i]
                file2 = mahasiswa_files_list[j]
                
                tokens1 = mahasiswa_codes[file1]
                tokens2 = mahasiswa_codes[file2]
                
                score = jaccard_similarity(tokens1, tokens2)
                hasil_mh_mh.append({
                    "file1": file1,
                    "file2": file2,
                    "score": round(score * 100, 2)
                })
        
        for r in sorted(hasil_mh_mh, key=lambda x: x['score'], reverse=True):
            if r['score'] > 0:
                print(f"{r['file1']} vs {r['file2']} → {r['score']}% mirip")