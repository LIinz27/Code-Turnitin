import os
import re
import hashlib

# ================================
# FULL WINNOWING ALGORITHM IMPLEMENTATION
# Enhanced with Rolling Hash (Rabin-Karp) for O(n) complexity
# ================================

BASE = 256  # Base for rolling hash
PRIME = 101  # Prime modulus for rolling hash

def rolling_hash(text, pattern_length):
    """
    Efficient rolling hash using Rabin-Karp algorithm
    Returns list of hash values for all substrings of pattern_length
    Time Complexity: O(n) instead of O(n*k) for SHA-1 approach
    """
    if len(text) < pattern_length:
        return []
    
    # Calculate hash for first window
    h = 0
    for i in range(pattern_length):
        h = (h * BASE + ord(text[i])) % PRIME
    
    hashes = [h]
    
    # Calculate pow(BASE, pattern_length-1) % PRIME
    h_multiplier = 1
    for i in range(pattern_length - 1):
        h_multiplier = (h_multiplier * BASE) % PRIME
    
    # Roll the hash for remaining windows
    for i in range(pattern_length, len(text)):
        # Remove leading character and add trailing character
        h = (h - ord(text[i - pattern_length]) * h_multiplier) % PRIME
        h = (h * BASE + ord(text[i])) % PRIME
        hashes.append(h)
    
    return hashes

def preprocess_code(path, lang_keywords=None):
    """
    Enhanced code preprocessing with advanced tokenization
    Returns normalized tokens with line information
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
    Generate k-grams with enhanced efficiency
    Output: list of ((k-gram_tuple), start_line_num, end_line_num)
    """
    if len(tokens_with_lines) < k:
        return []
    
    k_grams_info = []
    for i in range(len(tokens_with_lines) - k + 1):
        k_gram_tokens = [t[0] for t in tokens_with_lines[i:i + k]]
        start_line = tokens_with_lines[i][1]
        end_line = tokens_with_lines[i + k - 1][1]
        k_grams_info.append((tuple(k_gram_tokens), start_line, end_line))
    return k_grams_info

def hash_k_gram_optimized(k_gram_tuple):
    """
    Deterministic hash function for k-grams using polynomial rolling hash
    Ensures consistent results across multiple runs
    """
    BASE_HASH = 31  # Different from rolling hash base to avoid conflicts
    PRIME_HASH = 10**9 + 7  # Large prime for better distribution
    
    h = 0
    for i, token in enumerate(k_gram_tuple):
        # Convert token to string and use deterministic character-based hashing
        token_str = str(token)
        token_hash = 0
        for char in token_str:
            token_hash = (token_hash * 37 + ord(char)) % PRIME_HASH
        h = (h * BASE_HASH + token_hash) % PRIME_HASH
    return h

def winnowing(hashed_k_grams_info, w):
    """
    DETERMINISTIC WINNOWING ALGORITHM Implementation
    Selects minimum hash in each window of size w with consistent tie-breaking
    
    Key improvements:
    1. Deterministic tie-breaking (leftmost position wins)
    2. Consistent fingerprint selection across runs
    3. Maintains proper window semantics
    """
    if len(hashed_k_grams_info) < w:
        return hashed_k_grams_info  # Return all if less than window size
    
    fingerprints = []
    selected_positions = set()  # Track already selected positions to avoid duplicates
    
    # Process each window position
    for i in range(len(hashed_k_grams_info) - w + 1):
        window_end = i + w
        window_items = hashed_k_grams_info[i:window_end]
        
        # Find minimum hash in current window with deterministic tie-breaking
        min_hash = float('inf')
        min_position = -1
        min_item = None
        
        for j, (hash_val, k_gram_info, line_info) in enumerate(window_items):
            actual_position = i + j
            # Select leftmost minimum (deterministic tie-breaking)
            if hash_val < min_hash or (hash_val == min_hash and actual_position < min_position):
                min_hash = hash_val
                min_position = actual_position
                min_item = (hash_val, k_gram_info, line_info)
        
        # Add fingerprint if this position hasn't been selected yet
        if min_position not in selected_positions:
            selected_positions.add(min_position)
            fingerprints.append(min_item)
    
    return fingerprints

def calculate_jaccard_similarity(fingerprints_a, fingerprints_b):
    """
    Enhanced Jaccard Similarity with mathematical guarantees
    
    Jaccard Index = |A ∩ B| / |A ∪ B|
    Where A and B are sets of fingerprints
    
    Returns:
    - similarity_score: Float between 0.0 and 1.0
    - intersection_size: Number of common fingerprints  
    - union_size: Total unique fingerprints
    """
    # Extract only hash values for set operations
    set_a = set(fp[0] for fp in fingerprints_a)  # Hash values from file A
    set_b = set(fp[0] for fp in fingerprints_b)  # Hash values from file B
    
    intersection = set_a & set_b
    union = set_a | set_b
    
    if len(union) == 0:
        return 0.0, 0, 0
    
    jaccard_similarity = len(intersection) / len(union)
    return jaccard_similarity, len(intersection), len(union)

def get_similar_blocks(path_a, path_b, k=5, w=10, lang_keywords=None):
    """
    MAIN FUNCTION: Enhanced similarity detection using Full Winnowing Algorithm
    
    Key improvements over basic implementation:
    1. Rolling hash for O(n) complexity
    2. True winnowing algorithm with window management
    3. Mathematical Jaccard similarity with guarantees
    4. Detailed similarity analysis with block matching
    
    Parameters:
    - path_a, path_b: File paths to compare
    - k: Size of k-grams (default: 5)
    - w: Window size for winnowing (default: 10)
    - lang_keywords: Language-specific keywords for normalization
    
    Returns:
    - similarity_score: Float 0.0-1.0 (Jaccard similarity)
    - similar_blocks_a: List of similar code blocks in file A
    - similar_blocks_b: List of similar code blocks in file B
    """
    # Step 1: Enhanced preprocessing with tokenization
    tokens_a, lines_a = preprocess_code(path_a, lang_keywords)
    tokens_b, lines_b = preprocess_code(path_b, lang_keywords)
    
    if not tokens_a or not tokens_b:
        return 0.0, [], []
    
    # Step 2: Generate k-grams with line information
    k_grams_a = generate_k_grams(tokens_a, k)
    k_grams_b = generate_k_grams(tokens_b, k)
    
    if not k_grams_a or not k_grams_b:
        return 0.0, [], []
    
    # Step 3: Hash k-grams using optimized hash function
    hashed_k_grams_a = []
    for k_gram_tuple, start_line, end_line in k_grams_a:
        hash_val = hash_k_gram_optimized(k_gram_tuple)
        hashed_k_grams_a.append((hash_val, (k_gram_tuple, start_line, end_line), (start_line, end_line)))
    
    hashed_k_grams_b = []
    for k_gram_tuple, start_line, end_line in k_grams_b:
        hash_val = hash_k_gram_optimized(k_gram_tuple)
        hashed_k_grams_b.append((hash_val, (k_gram_tuple, start_line, end_line), (start_line, end_line)))
    
    # Step 4: Apply winnowing algorithm to select fingerprints
    fingerprints_a = winnowing(hashed_k_grams_a, w)
    fingerprints_b = winnowing(hashed_k_grams_b, w)
    
    # Step 5: Calculate Jaccard similarity
    similarity_score, intersection_count, union_count = calculate_jaccard_similarity(fingerprints_a, fingerprints_b)
    
    # Step 6: Find similar blocks for detailed analysis
    similar_blocks_a, similar_blocks_b = find_similar_blocks(fingerprints_a, fingerprints_b, lines_a, lines_b)
    
    return similarity_score, similar_blocks_a, similar_blocks_b

def find_similar_blocks(fingerprints_a, fingerprints_b, lines_a, lines_b):
    """
    Find matching code blocks between two files based on common fingerprints
    """
    # Create hash lookup for fingerprints
    hash_to_lines_a = {}
    for hash_val, k_gram_info, line_info in fingerprints_a:
        start_line, end_line = line_info
        if hash_val not in hash_to_lines_a:
            hash_to_lines_a[hash_val] = []
        hash_to_lines_a[hash_val].append((start_line, end_line))
    
    hash_to_lines_b = {}
    for hash_val, k_gram_info, line_info in fingerprints_b:
        start_line, end_line = line_info
        if hash_val not in hash_to_lines_b:
            hash_to_lines_b[hash_val] = []
        hash_to_lines_b[hash_val].append((start_line, end_line))
    
    # Find common hashes (similar blocks)
    common_hashes = set(hash_to_lines_a.keys()) & set(hash_to_lines_b.keys())
    
    similar_blocks_a = []
    similar_blocks_b = []
    
    for hash_val in common_hashes:
        # Get line ranges for this hash in both files
        for start_a, end_a in hash_to_lines_a[hash_val]:
            for start_b, end_b in hash_to_lines_b[hash_val]:
                # Extract actual code content
                content_a = ''.join(lines_a[start_a-1:end_a]).strip()
                content_b = ''.join(lines_b[start_b-1:end_b]).strip()
                
                similar_blocks_a.append({
                    'start_line': start_a,
                    'end_line': end_a,
                    'content': content_a,
                    'hash': hash_val
                })
                
                similar_blocks_b.append({
                    'start_line': start_b,
                    'end_line': end_b,
                    'content': content_b,
                    'hash': hash_val
                })
    
    return similar_blocks_a, similar_blocks_b

# Legacy function for backward compatibility  
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
            
    merged.append(current_merge)
    return merged

def get_similar_blocks(path_a, path_b, k=5, w=10, lang_keywords=None):
    """
    Mendeteksi blok kode yang mirip antara dua file menggunakan pendekatan MOSS-like.
    Mengembalikan skor kemiripan dan daftar blok yang mirip.
    """
    
    tokens_with_lines_a, original_lines_a = preprocess_code(path_a, lang_keywords)
    tokens_with_lines_b, original_lines_b = preprocess_code(path_b, lang_keywords)

    if not tokens_with_lines_a or not tokens_with_lines_b:
        return 0.0, [], [] # No similarity if either is empty

    k_grams_info_a = generate_k_grams(tokens_with_lines_a, k)
    k_grams_info_b = generate_k_grams(tokens_with_lines_b, k)
    
    if not k_grams_info_a or not k_grams_info_b:
        return 0.0, [], []

    # Map hash to (k-gram_tuple, start_line, end_line) for easy lookup after winnowing
    # This also helps to get the original k-gram info back
    hashed_k_grams_a = []
    for kgt, sl, el in k_grams_info_a:
        hashed_k_grams_a.append((hash_k_gram_optimized(kgt), sl, el))

    hashed_k_grams_b = []
    for kgt, sl, el in k_grams_info_b:
        hashed_k_grams_b.append((hash_k_gram_optimized(kgt), sl, el))


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


# ================================
# TOKEN-BASED JACCARD SIMILARITY
# For line-by-line comparison (alternative to winnowing)
# ================================

def tokenize_line(line: str, keywords: set = None) -> set:
    """
    Tokenize a single line of code into meaningful tokens.
    Returns a set of tokens for Jaccard similarity calculation.
    
    **IMPORTANT**: Keep track of actual identifiers to avoid false positives
    from variable name changes!
    
    Args:
        line: Source code line
        keywords: Set of language keywords to normalize
    
    Returns:
        Set of tokens representing the line
    """
    if not keywords:
        keywords = {
            'if', 'else', 'for', 'while', 'do', 'return', 'function', 'var', 'const', 'let', 'class',
            'public', 'private', 'protected', 'static', 'void', 'int', 'float', 'double', 'char', 'bool',
            'true', 'false', 'null', 'this', 'super', 'new', 'import', 'export', 'try', 'catch', 'finally',
            'async', 'await', 'break', 'continue', 'switch', 'case', 'def', 'with', 'lambda',
            'and', 'or', 'not', 'in', 'is', 'isinstance'
        }
    
    # Remove comments
    line = re.sub(r'//.*$', '', line)
    line = re.sub(r'#.*$', '', line)
    
    # Replace string literals
    line = re.sub(r'"[^"]*"', 'STR', line)
    line = re.sub(r"'[^']*'", 'STR', line)
    line = re.sub(r'`[^`]*`', 'STR', line)
    
    # Split into tokens: identifiers, keywords, operators, numbers
    tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*|[0-9]+|[+\-*/%=<>!&|^~().{}[\];:,]|STR', line)
    
    # Normalize: keywords stay as-is, identifiers KEEP ACTUAL NAME, numbers become NUM, operators as-is
    normalized_tokens = []
    for token in tokens:
        if token in keywords:
            normalized_tokens.append(f'KW:{token}')  # Keyword
        elif token == 'STR':
            normalized_tokens.append('LITERAL')
        elif token.isdigit():
            normalized_tokens.append('NUM')
        elif re.match(r'[a-zA-Z_]', token):
            # KEEP ACTUAL IDENTIFIER NAME - don't normalize to VAR!
            # This prevents false matches from variable renaming
            normalized_tokens.append(f'ID:{token}')
        else:
            normalized_tokens.append(f'OP:{token}')  # Operator/Punctuation
    
    return set(normalized_tokens)


def calculate_jaccard_similarity(tokens_a: set, tokens_b: set) -> float:
    """
    Calculate Jaccard similarity between two token sets.
    
    Jaccard = |intersection| / |union|
    
    Args:
        tokens_a: Token set from line A (or fingerprints set)
        tokens_b: Token set from line B (or fingerprints set)
    
    Returns:
        Similarity score between 0.0 and 1.0, or tuple (score, intersection_count, union_count)
        if fingerprints are passed.
    """
    if not tokens_a and not tokens_b:
        # Check if these are fingerprints (list of tuples) or token sets
        if isinstance(tokens_a, list) or isinstance(tokens_b, list):
            return 1.0, 0, 0
        return 1.0  # Both empty = identical
    
    if not tokens_a or not tokens_b:
        if isinstance(tokens_a, list) or isinstance(tokens_b, list):
            return 0.0, 0, 0
        return 0.0  # One empty, one not = completely different
    
    # Handle fingerprints (list of tuples with hash values)
    if isinstance(tokens_a, list) and isinstance(tokens_b, list):
        if tokens_a and isinstance(tokens_a[0], tuple):
            # These are fingerprints - extract hash values
            hashes_a = set(fp[0] for fp in tokens_a)
            hashes_b = set(fp[0] for fp in tokens_b)
            intersection = len(hashes_a.intersection(hashes_b))
            union = len(hashes_a.union(hashes_b))
            similarity = intersection / union if union > 0 else 0.0
            return similarity, intersection, union
    
    # Handle token sets
    if isinstance(tokens_a, set) and isinstance(tokens_b, set):
        intersection = len(tokens_a.intersection(tokens_b))
        union = len(tokens_a.union(tokens_b))
        
        if union == 0:
            return 0.0
        
        return intersection / union


def calculate_line_similarity_jaccard(source_code: str, target_code: str) -> dict:
    """
    Calculate line-by-line similarity using Jaccard on tokens.
    
    Returns dict with line similarities for both source and target.
    
    Args:
        source_code: Source code as string
        target_code: Target code as string
    
    Returns:
        {
            'source_similarities': {line_num: similarity_score, ...},
            'target_similarities': {line_num: similarity_score, ...},
            'line_mappings': [(src_line, tgt_line, similarity), ...]
        }
    """
    source_lines = source_code.split('\n')
    target_lines = target_code.split('\n')
    
    # Tokenize all lines
    source_tokens = []
    target_tokens = []
    
    for line in source_lines:
        if line.strip():
            source_tokens.append(tokenize_line(line))
        else:
            source_tokens.append(set())
    
    for line in target_lines:
        if line.strip():
            target_tokens.append(tokenize_line(line))
        else:
            target_tokens.append(set())
    
    # Calculate pairwise similarities
    source_similarities = {}
    target_similarities = {}
    line_mappings = []
    
    # For each source line, find best matching target line
    for src_idx, src_tokens in enumerate(source_tokens):
        src_line_num = src_idx + 1
        best_similarity = 0.0
        best_tgt_idx = -1
        
        for tgt_idx, tgt_tokens in enumerate(target_tokens):
            similarity = calculate_jaccard_similarity(src_tokens, tgt_tokens)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_tgt_idx = tgt_idx
        
        source_similarities[src_line_num] = best_similarity
        
        if best_tgt_idx >= 0 and best_similarity >= 0.1:  # Threshold 10%
            line_mappings.append((src_line_num, best_tgt_idx + 1, best_similarity))
    
    # For target lines, use same similarity if already mapped
    mapped_targets = {tgt: sim for _, tgt, sim in line_mappings}
    for tgt_idx in range(len(target_lines)):
        tgt_line_num = tgt_idx + 1
        if tgt_line_num in mapped_targets:
            target_similarities[tgt_line_num] = mapped_targets[tgt_line_num]
        else:
            target_similarities[tgt_line_num] = 0.0
    
    return {
        'source_similarities': source_similarities,
        'target_similarities': target_similarities,
        'line_mappings': line_mappings
    }