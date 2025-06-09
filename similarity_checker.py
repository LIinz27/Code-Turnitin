import os
import re
import hashlib

# Fungsi preprocess_code akan diubah untuk mengembalikan token dengan informasi baris
def preprocess_code(path, lang_keywords=None):
    """
    Membaca file kode, menghapus komentar, menormalisasi, mengganti identifier,
    dan mengembalikan LIST dari (token, nomor_baris_asli).
    """
    lines = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines() # Baca per baris
    except Exception as e:
        print(f"Error membaca file {path}: {e}")
        return [], [] # Mengembalikan list token kosong dan list baris asli kosong

    # Tokenizer yang menyimpan info baris
    normalized_tokens_with_lines = []
    
    # Daftar keyword bahasa yang umum (sama seperti sebelumnya)
    default_keywords = set([
        'if', 'else', 'for', 'while', 'do', 'return', 'function', 'var', 'const', 'let', 'class',
        'public', 'private', 'protected', 'static', 'void', 'int', 'float', 'double', 'char', 'bool',
        'true', 'false', 'null', 'this', 'super', 'new', 'import', 'export', 'default', 'try', 'catch', 'finally',
        'async', 'await', 'break', 'continue', 'switch', 'case', 'default', 'in', 'of', 'typeof', 'instanceof',
        'def', 'class', 'import', 'from', 'as', 'with', 'open', 'lambda', 'yield', 'None', 'True', 'False',
        'and', 'or', 'not',
    ])
    
    if lang_keywords:
        combined_keywords = default_keywords.union(set(lang_keywords))
    else:
        combined_keywords = default_keywords

    # Identifier mapping untuk normalisasi
    identifier_map = {}
    generic_id_counter = 0
    
    for line_num, original_line in enumerate(lines, 1): # Mulai dari baris 1
        processed_line = original_line # Ini akan kita modifikasi
        
        # 1. Hapus komentar pada baris ini
        processed_line = re.sub(r'//[^\n]*', '', processed_line)
        processed_line = re.sub(r'#[^\n]*', '', processed_line)

        # 2. Hapus string literals
        processed_line = re.sub(r'"[^"]*"', 'STRING_LITERAL', processed_line)
        processed_line = re.sub(r"'[^']*'", 'STRING_LITERAL', processed_line)
        processed_line = re.sub(r'`[^`]*`', 'STRING_LITERAL', processed_line)

        # 3. Normalisasi Identifier (sementara hanya pada processed_line)
        # Kumpulkan semua kata/potensi identifier di baris ini
        current_line_words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', processed_line)
        
        # Buat pemetaan lokal untuk baris ini dan terapkan
        line_replacements = []
        for word in current_line_words:
            if word not in combined_keywords: # Jika ini bukan keyword
                if word not in identifier_map: # Jika identifier baru ditemukan
                    identifier_map[word] = f'VAR_{generic_id_counter}'
                    generic_id_counter += 1
                line_replacements.append((word, identifier_map[word]))
        
        # Terapkan penggantian pada processed_line, urutkan dari yang terpanjang ke terpendek
        line_replacements.sort(key=lambda x: len(x[0]), reverse=True)
        temp_processed_line = processed_line
        for original_id, generic_id in line_replacements:
            temp_processed_line = re.sub(r'\b' + re.escape(original_id) + r'\b', generic_id, temp_processed_line)
        processed_line = temp_processed_line

        # 4. Normalisasi spasi
        processed_line = re.sub(r'[\s]+', ' ', processed_line).strip() # strip() untuk buang spasi di awal/akhir baris

        # 5. Tokenisasi akhir dan simpan dengan nomor baris
        if processed_line: # Hanya proses jika baris tidak kosong setelah normalisasi
            tokens_in_line = re.findall(r'[a-zA-Z0-9_]+', processed_line)
            for token in tokens_in_line:
                normalized_tokens_with_lines.append((token, line_num)) # Simpan (token, line_num)
    
    # Mengembalikan list token yang dinormalisasi dengan info baris asli, dan list baris asli
    return normalized_tokens_with_lines, lines


# Fungsi-fungsi lainnya (generate_k_grams, hash_k_gram, winnowing, calculate_moss_similarity) tetap sama,
# TAPI generate_k_grams dan winnowing akan perlu diubah agar membawa informasi baris.
# Mari kita perbaiki mereka secara berurutan.

def generate_k_grams(tokens_with_lines, k):
    """
    Menghasilkan k-gram dari daftar (token, nomor_baris)
    Output: list of ((k-gram_tuple), start_line_num, end_line_num)
    """
    if len(tokens_with_lines) < k:
        return []
    k_grams_info = []
    for i in range(len(tokens_with_lines) - k + 1):
        k_gram_tokens = [t[0] for t in tokens_with_lines[i : i + k]] # Hanya ambil token string
        start_line = tokens_with_lines[i][1]
        end_line = tokens_with_lines[i + k - 1][1]
        k_grams_info.append((tuple(k_gram_tokens), start_line, end_line))
    return k_grams_info

def hash_k_gram(k_gram_tuple):
    """
    Menghitung hash SHA-1 untuk k-gram tuple.
    """
    s = str(k_gram_tuple).encode('utf-8')
    return int(hashlib.sha1(s).hexdigest(), 16)

def winnowing(hashed_k_grams_info, w):
    """
    Menerapkan algoritma Winnowing untuk memilih fingerprint.
    Input: list of (hash_value, start_line, end_line)
    Output: set of (hash_value, start_line, end_line) - fingerprints
    """
    if not hashed_k_grams_info:
        return set()

    fingerprints = set()
    n = len(hashed_k_grams_info)

    # Inisialisasi jendela pertama
    window = hashed_k_grams_info[0:w]
    if not window:
        return set()

    # Fungsi pembantu untuk mendapatkan indeks hash minimum di jendela
    def get_min_hash_index(current_window):
        min_val = float('inf')
        min_idx_in_window = -1
        for i, (hash_val, _, _) in enumerate(current_window):
            if hash_val <= min_val: # Pilih yang paling kanan jika ada duplikat
                min_val = hash_val
                min_idx_in_window = i
        return min_idx_in_window

    # Iterasi melalui jendela
    for i in range(n - w + 1):
        current_window = hashed_k_grams_info[i : i + w]
        min_idx = get_min_hash_index(current_window)
        # Tambahkan hash minimum ke set fingerprint, beserta info barisnya
        fingerprints.add(current_window[min_idx])
    
    return fingerprints

def calculate_moss_similarity(fingerprints_a, fingerprints_b):
    """
    Menghitung kemiripan MOSS-like berdasarkan Jaccard Similarity dari fingerprint.
    Input: set of (hash_value, start_line, end_line)
    """
    # Untuk Jaccard, kita hanya perlu hash value-nya
    hashes_a = {fp[0] for fp in fingerprints_a}
    hashes_b = {fp[0] for fp in fingerprints_b}

    intersection = hashes_a.intersection(hashes_b)
    union = hashes_a.union(hashes_b)
    if not union:
        return 0.0
    return len(intersection) / len(union)

def merge_overlapping_segments(segments):
    """
    Menggabungkan segmen baris yang tumpang tindih atau berdekatan.
    Segments: List of {'start': int, 'end': int}
    Returns: List of merged segments
    """
    if not segments:
        return []
    
    # Urutkan berdasarkan baris awal
    sorted_segments = sorted(segments, key=lambda x: x['start'])
    
    merged = []
    current_merge = sorted_segments[0]
    
    for i in range(1, len(sorted_segments)):
        segment = sorted_segments[i]
        # Jika segmen tumpang tindih atau berdekatan (dalam 1 baris)
        if segment['start'] <= current_merge['end'] + 1:
            current_merge['end'] = max(current_merge['end'], segment['end'])
        else:
            merged.append(current_merge)
            current_merge = segment
            
    merged.append(current_merge) # Tambahkan yang terakhir
    return merged

def get_similar_blocks(path_a, path_b, k=5, w=10, lang_keywords=None):
    """
    Mendeteksi blok kode yang mirip antara dua file menggunakan pendekatan MOSS-like.
    Mengembalikan skor kemiripan dan daftar blok yang mirip.
    """
    
    tokens_with_lines_a, original_lines_a = preprocess_code(path_a, lang_keywords)
    tokens_with_lines_b, original_lines_b = preprocess_code(path_b, lang_keywords)

    if not tokens_with_lines_a or not tokens_with_lines_b:
        return 0.0, [] # No similarity if either is empty

    k_grams_info_a = generate_k_grams(tokens_with_lines_a, k)
    k_grams_info_b = generate_k_grams(tokens_with_lines_b, k)
    
    if not k_grams_info_a or not k_grams_info_b:
        return 0.0, []

    # Map hash to (k-gram_tuple, start_line, end_line) for easy lookup after winnowing
    # This also helps to get the original k-gram info back
    hashed_k_grams_a = []
    for kgt, sl, el in k_grams_info_a:
        hashed_k_grams_a.append((hash_k_gram(kgt), sl, el))

    hashed_k_grams_b = []
    for kgt, sl, el in k_grams_info_b:
        hashed_k_grams_b.append((hash_k_gram(kgt), sl, el))


    fingerprints_a = winnowing(hashed_k_grams_a, w)
    fingerprints_b = winnowing(hashed_k_grams_b, w)

    # Calculate overall similarity score
    overall_similarity = calculate_moss_similarity(fingerprints_a, fingerprints_b)

    # Find common fingerprints and map them back to original line numbers
    common_fingerprints_hashes = {fp[0] for fp in fingerprints_a}.intersection({fp[0] for fp in fingerprints_b})
    
    # Store all segments from common fingerprints
    segments_a = []
    segments_b = []

    for fp_hash, start_line, end_line in fingerprints_a:
        if fp_hash in common_fingerprints_hashes:
            segments_a.append({'start': start_line, 'end': end_line})

    for fp_hash, start_line, end_line in fingerprints_b:
        if fp_hash in common_fingerprints_hashes:
            segments_b.append({'start': start_line, 'end': end_line})

    # Merge overlapping segments to get consolidated blocks
    merged_blocks_a = merge_overlapping_segments(segments_a)
    merged_blocks_b = merge_overlapping_segments(segments_b)

    # For simplicity, we assume one-to-one mapping of merged blocks.
    # A more advanced approach would try to align blocks more accurately.
    # For initial implementation, we can just return blocks from A and B that are common.
    # The output format for frontend could be simplified to a list of blocks per file.
    
    # For now, let's just return the merged blocks for A and B.
    # This doesn't directly tell you which block in A maps to which in B,
    # but tells you *where* similar code exists in each file.
    
    # A more practical output would be a list of dicts:
    # [{'fileA_lines': [start_A, end_A], 'fileB_lines': [start_B, end_B]}]
    # This mapping is complex to get precisely from Winnowing directly.
    # For simplicity, let's return common fingerprints as raw data for now,
    # and Frontend can highlight all lines touched by these common fingerprints.
    
    # Let's refine the return value for `get_similar_blocks`
    # Return a list of {"fileA": [start_line_A, end_line_A], "fileB": [start_line_B, end_line_B]}
    # For MOSS, often it's about what percentage of A is similar to B, and vice-versa.

    # Simpler approach: Collect all common k-gram ranges from A and B, then merge them.
    # The frontend will then highlight these merged ranges.
    
    final_similar_ranges_a = []
    final_similar_ranges_b = []

    # Iterate through fingerprints of A and B, if their hash is common, add their line range
    for fp_hash_a, start_line_a, end_line_a in fingerprints_a:
        if fp_hash_a in common_fingerprints_hashes:
            final_similar_ranges_a.append({'start': start_line_a, 'end': end_line_a})

    for fp_hash_b, start_line_b, end_line_b in fingerprints_b:
        if fp_hash_b in common_fingerprints_hashes:
            final_similar_ranges_b.append({'start': start_line_b, 'end': end_line_b})

    # Merge these ranges
    merged_ranges_a = merge_overlapping_segments(final_similar_ranges_a)
    merged_ranges_b = merge_overlapping_segments(final_similar_ranges_b)

    # Return the overall similarity score and the merged line ranges for each file
    return overall_similarity, merged_ranges_a, merged_ranges_b


# Untuk pengujian mandiri (tetap sama, tapi output lebih banyak)
if __name__ == "__main__":
    if not os.path.exists("data/temp"):
        os.makedirs("data/temp")

    # Kode mirip dengan perubahan nama variabel
    code1 = """
    function calculateSum(a, b) {
        let result = a + b; // Line 3
        return result;      // Line 4
    }
    """
    code2 = """
    // This is a test file
    function computeTotal(x, y) {
        var sum_val = x + y; // Line 4
        return sum_val;      // Line 5
    }
    """
    # Kode yang berbeda
    code3 = """
    def factorial(n):
        if n == 0:
            return 1
        return n * factorial(n - 1)
    """

    with open("data/temp/code1.js", "w") as f: f.write(code1)
    with open("data/temp/code2.js", "w") as f: f.write(code2)
    with open("data/temp/code3.py", "w") as f: f.write(code3)

    print("--- Pengujian MOSS-like Similarity dengan Deteksi Blok Mirip ---")

    # Kasus 1: Kode mirip dengan perubahan nama variabel
    score, blocks_a, blocks_b = get_similar_blocks("data/temp/code1.js", "data/temp/code2.js", k=3, w=6)
    print(f"code1.js vs code2.js: {round(score * 100, 2)}% mirip")
    print(f"Blok mirip di code1.js: {blocks_a}")
    print(f"Blok mirip di code2.js: {blocks_b}")
    # Output diharapkan:
    # Blok mirip di code1.js: [{'start': 3, 'end': 4}]
    # Blok mirip di code2.js: [{'start': 4, 'end': 5}]

    # Kasus 2: Kode sangat berbeda
    score, blocks_a, blocks_b = get_similar_blocks("data/temp/code1.js", "data/temp/code3.py", k=3, w=6)
    print(f"\ncode1.js vs code3.py: {round(score * 100, 2)}% mirip")
    print(f"Blok mirip di code1.js: {blocks_a}")
    print(f"Blok mirip di code3.py: {blocks_b}")
    # Output diharapkan: blok kosong atau sangat sedikit

    # Membersihkan file dummy
    # os.remove("data/temp/code1.js")
    # os.remove("data/temp/code2.js")
    # os.remove("data/temp/code3.py")
    # os.rmdir("data/temp")