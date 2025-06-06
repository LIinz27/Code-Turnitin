import os
import re
import hashlib # Untuk hashing yang lebih kuat

def preprocess_code(path, lang_keywords=None):
    """
    Membaca file kode, menghapus komentar, menormalisasi spasi, mengganti identifier,
    dan mengembalikan LIST token.
    Menambahkan parameter lang_keywords untuk daftar keyword bahasa.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        print(f"Error membaca file {path}: {e}")
        return [] # Return empty list if error

    # 1. Hapus komentar (general untuk JS/Python, bisa diperluas)
    code = re.sub(r'//[^\n]*', '', code)  # Single-line JS
    code = re.sub(r'/\*[\s\S]*?\*/', '', code) # Multi-line JS
    code = re.sub(r'#[^\n]*', '', code)   # Python comments

    # 2. Hapus string literals
    code = re.sub(r'"[^"]*"', 'STRING_LITERAL', code)
    code = re.sub(r"'[^']*'", 'STRING_LITERAL', code)
    code = re.sub(r'`[^`]*`', 'STRING_LITERAL', code) # Template literals JS

    # 3. Normalisasi Identifier (MOSES-like)
    # Daftar keyword bahasa yang umum. Ini bisa diperluas atau jadi parameter.
    default_keywords = set([
        'if', 'else', 'for', 'while', 'do', 'return', 'function', 'var', 'const', 'let', 'class',
        'public', 'private', 'protected', 'static', 'void', 'int', 'float', 'double', 'char', 'bool',
        'true', 'false', 'null', 'this', 'super', 'new', 'import', 'export', 'default', 'try', 'catch', 'finally',
        'async', 'await', 'break', 'continue', 'switch', 'case', 'default', 'in', 'of', 'typeof', 'instanceof',
        'def', 'class', 'import', 'from', 'as', 'with', 'open', 'lambda', 'yield', 'None', 'True', 'False',
        'and', 'or', 'not', # Python logic
        # Tambahkan lebih banyak keyword sesuai kebutuhan bahasa yang ingin didukung
    ])
    
    if lang_keywords:
        combined_keywords = default_keywords.union(set(lang_keywords))
    else:
        combined_keywords = default_keywords

    # Cari semua kemungkinan identifier (kata-kata alfanumerik)
    # Menggunakan regex yang lebih spesifik untuk identifier (bukan hanya kata)
    all_words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', code)
    
    identifier_map = {}
    generic_id_counter = 0

    # Lakukan penggantian identifier pada copy dari kode asli
    temp_code = code
    replacements = [] # Simpan pasangan (original, replacement)

    for word in all_words:
        # Hanya ganti jika bukan keyword dan belum pernah diganti
        if word not in combined_keywords and word not in identifier_map:
            # Gunakan prefix berbeda untuk variabel dan fungsi jika bisa dibedakan (lebih canggih)
            # Untuk sederhana, gunakan VAR_
            identifier_map[word] = f'VAR_{generic_id_counter}'
            replacements.append((word, identifier_map[word]))
            generic_id_counter += 1
    
    # Lakukan penggantian secara aman menggunakan word boundary
    # Iterasi dari yang terpanjang ke terpendek untuk menghindari penggantian parsial
    replacements.sort(key=lambda x: len(x[0]), reverse=True)
    for original_id, generic_id in replacements:
        # Gunakan re.escape untuk menangani identifier yang mungkin mengandung karakter khusus regex
        temp_code = re.sub(r'\b' + re.escape(original_id) + r'\b', generic_id, temp_code)
    
    code = temp_code # Update kode setelah normalisasi identifier

    # 4. Normalisasi spasi: ganti baris baru dan spasi berlebih dengan satu spasi
    code = re.sub(r'[\s]+', ' ', code)
    
    # 5. Tokenisasi akhir: pisahkan berdasarkan non-alfanumerik dan non-underscore
    # Return LIST of tokens for k-gram generation
    tokens = re.findall(r'[a-zA-Z0-9_]+', code)
    return tokens

def generate_k_grams(tokens, k):
    """
    Menghasilkan k-gram dari daftar token.
    K-gram adalah tuple dari k token berurutan.
    """
    if len(tokens) < k:
        return []
    k_grams = []
    for i in range(len(tokens) - k + 1):
        k_grams.append(tuple(tokens[i : i + k]))
    return k_grams

def hash_k_gram(k_gram):
    """
    Menghitung hash SHA-1 untuk k-gram.
    Mengubah tuple token menjadi string sebelum hashing.
    """
    s = str(k_gram).encode('utf-8')
    return int(hashlib.sha1(s).hexdigest(), 16)

def winnowing(hashes, w):
    """
    Menerapkan algoritma Winnowing untuk memilih fingerprint.
    hashes: daftar hash k-gram
    w: ukuran jendela
    """
    if not hashes:
        return set()

    fingerprints = set()
    n = len(hashes)

    # Inisialisasi jendela pertama
    window = hashes[0:w]
    if not window: # Handle case where w is very small or hashes is empty
        return set()

    # Fungsi pembantu untuk mendapatkan indeks hash minimum di jendela
    def get_min_hash_index(current_window):
        min_val = float('inf')
        min_idx_in_window = -1
        for i, val in enumerate(current_window):
            if val <= min_val: # Pilih yang paling kanan jika ada duplikat
                min_val = val
                min_idx_in_window = i
        return min_idx_in_window

    # Iterasi melalui jendela
    for i in range(n - w + 1):
        current_window = hashes[i : i + w]
        min_idx = get_min_hash_index(current_window)
        # Tambahkan hash minimum ke set fingerprint
        fingerprints.add(current_window[min_idx])
    
    return fingerprints


def calculate_moss_similarity(fingerprints_a, fingerprints_b):
    """
    Menghitung kemiripan MOSS-like berdasarkan Jaccard Similarity dari fingerprint.
    """
    intersection = fingerprints_a.intersection(fingerprints_b)
    union = fingerprints_a.union(fingerprints_b)
    if not union:
        return 0.0 # Hindari pembagian dengan nol
    return len(intersection) / len(union)

# Fungsi utama perbandingan yang akan dipanggil dari app.py
def compare_code_moss_like(path_a, path_b, k=5, w=10, lang_keywords=None):
    """
    Membandingkan dua file kode menggunakan pendekatan MOSS-like (Winnowing).
    Args:
        path_a (str): Jalur ke file kode pertama.
        path_b (str): Jalur ke file kode kedua.
        k (int): Ukuran k-gram.
        w (int): Ukuran jendela Winnowing.
        lang_keywords (set): Set keyword spesifik bahasa untuk normalisasi.

    Returns:
        float: Skor kemiripan antara 0.0 dan 1.0.
    """
    
    # Pre-process dan dapatkan list token
    tokens_a = preprocess_code(path_a, lang_keywords)
    tokens_b = preprocess_code(path_b, lang_keywords)

    if not tokens_a or not tokens_b:
        # Jika salah satu file kosong setelah pre-processing, kemiripan 0
        return 0.0

    # Generate k-grams
    k_grams_a = generate_k_grams(tokens_a, k)
    k_grams_b = generate_k_grams(tokens_b, k)
    
    if not k_grams_a or not k_grams_b:
        return 0.0

    # Hash k-grams
    hashes_a = [hash_k_gram(kg) for kg in k_grams_a]
    hashes_b = [hash_k_gram(kg) for kg in k_grams_b]

    # Apply Winnowing to get fingerprints
    fingerprints_a = winnowing(hashes_a, w)
    fingerprints_b = winnowing(hashes_b, w)

    # Calculate MOSS-like similarity (Jaccard of fingerprints)
    similarity_score = calculate_moss_similarity(fingerprints_a, fingerprints_b)
    return similarity_score

# Untuk pengujian mandiri
if __name__ == "__main__":
    # Buat file dummy untuk pengujian
    if not os.path.exists("data/temp"):
        os.makedirs("data/temp")

    code1 = """
    function calculateSum(a, b) {
        let result = a + b;
        return result;
    }
    """
    code2 = """
    // This is a test file
    function computeTotal(x, y) {
        var sum_val = x + y; // Changed variable names
        return sum_val;
    }
    """
    code3 = """
    def add_numbers(num1, num2):
        res = num1 + num2
        return res
    """
    code4 = """
    // Completely different code
    function factorial(n) {
        if (n === 0) return 1;
        return n * factorial(n - 1);
    }
    """

    with open("data/temp/code1.js", "w") as f: f.write(code1)
    with open("data/temp/code2.js", "w") as f: f.write(code2)
    with open("data/temp/code3.py", "w") as f: f.write(code3)
    with open("data/temp/code4.js", "w") as f: f.write(code4)

    print("--- Pengujian MOSS-like Similarity ---")

    # Kasus 1: Kode mirip dengan perubahan nama variabel
    score1_2 = compare_code_moss_like("data/temp/code1.js", "data/temp/code2.js", k=3, w=6)
    print(f"code1.js vs code2.js: {round(score1_2 * 100, 2)}% mirip (diharapkan tinggi)")

    # Kasus 2: Kode sangat berbeda
    score1_4 = compare_code_moss_like("data/temp/code1.js", "data/temp/code4.js", k=3, w=6)
    print(f"code1.js vs code4.js: {round(score1_4 * 100, 2)}% mirip (diharapkan rendah)")

    # Kasus 3: Bahasa berbeda (diharapkan rendah, kecuali ada kemiripan struktural)
    score1_3 = compare_code_moss_like("data/temp/code1.js", "data/temp/code3.py", k=3, w=6)
    print(f"code1.js vs code3.py: {round(score1_3 * 100, 2)}% mirip (diharapkan rendah)")
    
    # Membersihkan file dummy
    # os.remove("data/temp/code1.js")
    # os.remove("data/temp/code2.js")
    # os.remove("data/temp/code3.py")
    # os.remove("data/temp/code4.js")
    # os.rmdir("data/temp") # Hanya jika folder kosong