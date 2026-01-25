#!/usr/bin/env python3
"""Test Token-Based Jaccard Implementation"""

from src.algorithms.similarity_checker import (
    winnowing, hash_k_gram_optimized, generate_k_grams, 
    preprocess_code, calculate_jaccard_similarity
)
import tempfile
import os

# Create simple test file
code = 'int x = 10;\nint y = 20;'
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write(code)
    temp_file = f.name

try:
    tokens, lines = preprocess_code(temp_file, None)
    print(f'Tokens type: {type(tokens)}')
    print(f'Tokens length: {len(tokens)}')
    
    if tokens:
        kgrams = generate_k_grams(tokens, 5)
        print(f'K-grams: {len(kgrams)}')
        
        hashed = [(hash_k_gram_optimized(kg[0]), kg, (kg[1], kg[2])) for kg in kgrams]
        print(f'Hashed: {len(hashed)}')
        
        fingerprints = winnowing(hashed, 4)
        print(f'Fingerprints type: {type(fingerprints)}')
        print(f'Fingerprints length: {len(fingerprints)}')
        
        if fingerprints:
            print(f'First fingerprint: {fingerprints[0]}')
            print(f'Fingerprint[0] type: {type(fingerprints[0])}')
        
        # Test calculate_jaccard_similarity with fingerprints
        result = calculate_jaccard_similarity(fingerprints, fingerprints)
        print(f'Jaccard result type: {type(result)}')
        print(f'Jaccard result: {result}')
        
finally:
    os.remove(temp_file)
