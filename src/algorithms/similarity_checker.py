import os
import re
import hashlib

BASE = 256
PRIME = 101

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
    Enhanced code preprocessing with advanced tokenization.
    Returns normalized tokens with line information.
    """
    lines = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file {path}: {e}")
        return [], []

    normalized_tokens_with_lines = []
    
    default_keywords = set([
        'if', 'else', 'for', 'while', 'do', 'return', 'function', 'var', 'const', 'let', 'class',
        'public', 'private', 'protected', 'static', 'void', 'int', 'float', 'double', 'char', 'bool',
        'true', 'false', 'null', 'this', 'super', 'new', 'import', 'export', 'default', 'try', 'catch', 'finally',
        'async', 'await', 'break', 'continue', 'switch', 'case', 'default', 'in', 'of', 'typeof', 'instanceof',
        'def', 'class', 'import', 'from', 'as', 'with', 'open', 'lambda', 'yield', 'None', 'True', 'False',
        'and', 'or', 'not',
    ])
    
    combined_keywords = default_keywords.union(set(lang_keywords)) if lang_keywords else default_keywords
    identifier_map = {}
    generic_id_counter = 0
    
    for line_num, original_line in enumerate(lines, 1):
        processed_line = original_line
        
        processed_line = re.sub(r'//[^\n]*', '', processed_line)
        processed_line = re.sub(r'#[^\n]*', '', processed_line)
        processed_line = re.sub(r'"[^"]*"', 'STRING_LITERAL', processed_line)
        processed_line = re.sub(r"'[^']*'", 'STRING_LITERAL', processed_line)
        processed_line = re.sub(r'`[^`]*`', 'STRING_LITERAL', processed_line)

        current_line_words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', processed_line)
        
        line_replacements = []
        for word in current_line_words:
            if word not in combined_keywords:
                if word not in identifier_map:
                    identifier_map[word] = f'VAR_{generic_id_counter}'
                    generic_id_counter += 1
                line_replacements.append((word, identifier_map[word]))
        
        line_replacements.sort(key=lambda x: len(x[0]), reverse=True)
        temp_processed_line = processed_line
        for original_id, generic_id in line_replacements:
            temp_processed_line = re.sub(r'\b' + re.escape(original_id) + r'\b', generic_id, temp_processed_line)
        processed_line = temp_processed_line

        processed_line = re.sub(r'[\s]+', ' ', processed_line).strip()

        if processed_line:
            tokens_in_line = re.findall(r'[a-zA-Z0-9_]+', processed_line)
            for token in tokens_in_line:
                normalized_tokens_with_lines.append((token, line_num))
    
    return normalized_tokens_with_lines, lines


# Fungsi-fungsi lainnya (generate_k_grams, hash_k_gram, winnowing, calculate_moss_similarity) tetap sama,
# TAPI generate_k_grams dan winnowing akan perlu diubah agar membawa informasi baris.
# Mari kita perbaiki mereka secara berurutan.

def generate_k_grams(tokens_with_lines, k):
    """
    Generate k-grams with line information.
    Returns: list of ((k-gram_tuple), start_line_num, end_line_num)
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
    DETERMINISTIC WINNOWING ALGORITHM Implementation.
    Selects minimum hash in each window of size w.
    """
    if len(hashed_k_grams_info) < w:
        return hashed_k_grams_info
    
    fingerprints = []
    selected_positions = set()
    
    for i in range(len(hashed_k_grams_info) - w + 1):
        window_end = i + w
        window_items = hashed_k_grams_info[i:window_end]
        
        min_hash = float('inf')
        min_position = -1
        min_item = None
        
        for j, (hash_val, k_gram_info, line_info) in enumerate(window_items):
            actual_position = i + j
            if hash_val < min_hash or (hash_val == min_hash and actual_position < min_position):
                min_hash = hash_val
                min_position = actual_position
                min_item = (hash_val, k_gram_info, line_info)
        
        if min_position not in selected_positions:
            selected_positions.add(min_position)
            fingerprints.append(min_item)
    
    return fingerprints

def calculate_jaccard_similarity(fingerprints_a, fingerprints_b):
    """
    Jaccard Similarity calculation.
    
    Jaccard Index = |A ∩ B| / |A ∪ B|
    
    Returns: (similarity_score, intersection_size, union_size)
    """
    set_a = set(fp[0] for fp in fingerprints_a)
    set_b = set(fp[0] for fp in fingerprints_b)
    
    intersection = set_a & set_b
    union = set_a | set_b
    
    if len(union) == 0:
        return 0.0, 0, 0
    
    jaccard_similarity = len(intersection) / len(union)
    return jaccard_similarity, len(intersection), len(union)

def get_similar_blocks(path_a, path_b, k=5, w=10, lang_keywords=None):
    """
    Main function: Enhanced similarity detection using Winnowing Algorithm.
    
    Parameters:
    - path_a, path_b: File paths to compare
    - k: Size of k-grams (default: 5)
    - w: Window size for winnowing (default: 10)
    - lang_keywords: Language-specific keywords
    
    Returns: (similarity_score, similar_blocks_a, similar_blocks_b)
    """
    tokens_a, lines_a = preprocess_code(path_a, lang_keywords)
    tokens_b, lines_b = preprocess_code(path_b, lang_keywords)
    
    if not tokens_a or not tokens_b:
        return 0.0, [], []
    
    k_grams_a = generate_k_grams(tokens_a, k)
    k_grams_b = generate_k_grams(tokens_b, k)
    
    if not k_grams_a or not k_grams_b:
        return 0.0, [], []
    
    hashed_k_grams_a = []
    for k_gram_tuple, start_line, end_line in k_grams_a:
        hash_val = hash_k_gram_optimized(k_gram_tuple)
        hashed_k_grams_a.append((hash_val, (k_gram_tuple, start_line, end_line), (start_line, end_line)))
    
    hashed_k_grams_b = []
    for k_gram_tuple, start_line, end_line in k_grams_b:
        hash_val = hash_k_gram_optimized(k_gram_tuple)
        hashed_k_grams_b.append((hash_val, (k_gram_tuple, start_line, end_line), (start_line, end_line)))
    
    fingerprints_a = winnowing(hashed_k_grams_a, w)
    fingerprints_b = winnowing(hashed_k_grams_b, w)
    
    similarity_score, intersection_count, union_count = calculate_jaccard_similarity(fingerprints_a, fingerprints_b)
    
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

def calculate_moss_similarity(fingerprints_a, fingerprints_b):
    """
    Calculate MOSS-like similarity based on Jaccard Similarity of fingerprints.
    """
    hashes_a = {fp[0] for fp in fingerprints_a}
    hashes_b = {fp[0] for fp in fingerprints_b}

    intersection = hashes_a.intersection(hashes_b)
    union = hashes_a.union(hashes_b)
    if not union:
        return 0.0
    return len(intersection) / len(union)

def merge_overlapping_segments(segments):
    """Merge overlapping or adjacent segments."""
    if not segments:
        return []
    
    sorted_segments = sorted(segments, key=lambda x: x['start'])
    
    merged = []
    current_merge = sorted_segments[0]
    
    for i in range(1, len(sorted_segments)):
        segment = sorted_segments[i]
        if segment['start'] <= current_merge['end'] + 1:
            current_merge['end'] = max(current_merge['end'], segment['end'])
        else:
            merged.append(current_merge)
            current_merge = segment
            
    merged.append(current_merge)
    return merged

def get_similar_blocks(path_a, path_b, k=5, w=10, lang_keywords=None):
    """
    Detect similar code blocks between two files using Winnowing Algorithm.
    Returns: (similarity_score, merged_ranges_a, merged_ranges_b)
    """
    
    tokens_with_lines_a, original_lines_a = preprocess_code(path_a, lang_keywords)
    tokens_with_lines_b, original_lines_b = preprocess_code(path_b, lang_keywords)

    if not tokens_with_lines_a or not tokens_with_lines_b:
        return 0.0, [], []

    k_grams_info_a = generate_k_grams(tokens_with_lines_a, k)
    k_grams_info_b = generate_k_grams(tokens_with_lines_b, k)
    
    if not k_grams_info_a or not k_grams_info_b:
        return 0.0, [], []

    hashed_k_grams_a = []
    for kgt, sl, el in k_grams_info_a:
        hashed_k_grams_a.append((hash_k_gram_optimized(kgt), sl, el))

    hashed_k_grams_b = []
    for kgt, sl, el in k_grams_info_b:
        hashed_k_grams_b.append((hash_k_gram_optimized(kgt), sl, el))

    fingerprints_a = winnowing(hashed_k_grams_a, w)
    fingerprints_b = winnowing(hashed_k_grams_b, w)

    overall_similarity = calculate_moss_similarity(fingerprints_a, fingerprints_b)

    common_fingerprints_hashes = {fp[0] for fp in fingerprints_a}.intersection({fp[0] for fp in fingerprints_b})
    
    final_similar_ranges_a = []
    final_similar_ranges_b = []

    for fp_hash_a, start_line_a, end_line_a in fingerprints_a:
        if fp_hash_a in common_fingerprints_hashes:
            final_similar_ranges_a.append({'start': start_line_a, 'end': end_line_a})

    for fp_hash_b, start_line_b, end_line_b in fingerprints_b:
        if fp_hash_b in common_fingerprints_hashes:
            final_similar_ranges_b.append({'start': start_line_b, 'end': end_line_b})

    merged_ranges_a = merge_overlapping_segments(final_similar_ranges_a)
    merged_ranges_b = merge_overlapping_segments(final_similar_ranges_b)

    return overall_similarity, merged_ranges_a, merged_ranges_b


# Testing section
if __name__ == "__main__":
    if not os.path.exists("data/temp"):
        os.makedirs("data/temp")

    code1 = """
    function calculateSum(a, b) {
        let result = a + b;
        return result;
    }
    """
    code2 = """
    function computeTotal(x, y) {
        var sum_val = x + y;
        return sum_val;
    }
    """
    code3 = """
    def factorial(n):
        if n == 0:
            return 1
        return n * factorial(n - 1)
    """

    with open("data/temp/code1.js", "w") as f: f.write(code1)
    with open("data/temp/code2.js", "w") as f: f.write(code2)
    with open("data/temp/code3.py", "w") as f: f.write(code3)

    print("--- Testing Similarity Detection ---")

    score, blocks_a, blocks_b = get_similar_blocks("data/temp/code1.js", "data/temp/code2.js", k=3, w=6)
    print(f"code1.js vs code2.js: {round(score * 100, 2)}% similar")
    print(f"Similar blocks in code1.js: {blocks_a}")
    print(f"Similar blocks in code2.js: {blocks_b}")

    score, blocks_a, blocks_b = get_similar_blocks("data/temp/code1.js", "data/temp/code3.py", k=3, w=6)
    print(f"\ncode1.js vs code3.py: {round(score * 100, 2)}% similar")
    print(f"Similar blocks in code1.js: {blocks_a}")
    print(f"Similar blocks in code3.py: {blocks_b}")


# ================================
# TOKEN-BASED JACCARD SIMILARITY
# For line-by-line comparison (alternative to winnowing)
# ================================

def tokenize_line(line: str, keywords: set = None) -> set:
    """
    Tokenize a single line of code into meaningful tokens.
    Returns a set of tokens for Jaccard similarity calculation.
    """
    if not keywords:
        keywords = {
            'if', 'else', 'for', 'while', 'do', 'return', 'function', 'var', 'const', 'let', 'class',
            'public', 'private', 'protected', 'static', 'void', 'int', 'float', 'double', 'char', 'bool',
            'true', 'false', 'null', 'this', 'super', 'new', 'import', 'export', 'try', 'catch', 'finally',
            'async', 'await', 'break', 'continue', 'switch', 'case', 'def', 'with', 'lambda',
            'and', 'or', 'not', 'in', 'is', 'isinstance'
        }
    
    line = re.sub(r'//.*$', '', line)
    line = re.sub(r'#.*$', '', line)
    line = re.sub(r'"[^"]*"', 'STR', line)
    line = re.sub(r"'[^']*'", 'STR', line)
    line = re.sub(r'`[^`]*`', 'STR', line)
    
    tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*|[0-9]+|[+\-*/%=<>!&|^~().{}[\];:,]|STR', line)
    
    normalized_tokens = []
    for token in tokens:
        if token in keywords:
            normalized_tokens.append(f'KW:{token}')
        elif token == 'STR':
            normalized_tokens.append('LITERAL')
        elif token.isdigit():
            normalized_tokens.append('NUM')
        elif re.match(r'[a-zA-Z_]', token):
            normalized_tokens.append(f'ID:{token}')
        else:
            normalized_tokens.append(f'OP:{token}')
    
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
    """
    source_lines = source_code.split('\n')
    target_lines = target_code.split('\n')
    
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
    
    source_similarities = {}
    target_similarities = {}
    line_mappings = []
    
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
        
        if best_tgt_idx >= 0 and best_similarity >= 0.1:
            line_mappings.append((src_line_num, best_tgt_idx + 1, best_similarity))
    
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