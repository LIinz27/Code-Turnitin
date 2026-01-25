#!/usr/bin/env python3
"""Debug Token-Based Jaccard tokenization"""

from src.algorithms.similarity_checker import tokenize_line, calculate_jaccard_similarity

# Test lines from the comparison
line1 = "public class Telur {"
line2 = "public class PrediksipenjualanTelurAyam {"

line3 = 'String nim = "105841113423";'
line4 = 'String nim = "105841118623";'

line5 = "int x = 3;"
line6 = "int x = 8;"

# Tokenize
tokens1 = tokenize_line(line1)
tokens2 = tokenize_line(line2)
tokens3 = tokenize_line(line3)
tokens4 = tokenize_line(line4)
tokens5 = tokenize_line(line5)
tokens6 = tokenize_line(line6)

print("=" * 60)
print("LINE COMPARISON TEST")
print("=" * 60)

print("\n[TEST 1] Class definition with different names:")
print(f"Line 1: {line1}")
print(f"Tokens 1: {sorted(tokens1)}")
print(f"\nLine 2: {line2}")
print(f"Tokens 2: {sorted(tokens2)}")
jaccard1 = calculate_jaccard_similarity(tokens1, tokens2)
print(f"Jaccard: {jaccard1:.3f} ({jaccard1*100:.1f}%)")
print(f"Intersection: {tokens1.intersection(tokens2)}")
print(f"Union: {tokens1.union(tokens2)}")

print("\n" + "=" * 60)
print("[TEST 2] String assignment with different numbers:")
print(f"Line 3: {line3}")
print(f"Tokens 3: {sorted(tokens3)}")
print(f"\nLine 4: {line4}")
print(f"Tokens 4: {sorted(tokens4)}")
jaccard2 = calculate_jaccard_similarity(tokens3, tokens4)
print(f"Jaccard: {jaccard2:.3f} ({jaccard2*100:.1f}%)")
print(f"Intersection: {tokens3.intersection(tokens4)}")
print(f"Union: {tokens3.union(tokens4)}")

print("\n" + "=" * 60)
print("[TEST 3] Integer assignment with different values:")
print(f"Line 5: {line5}")
print(f"Tokens 5: {sorted(tokens5)}")
print(f"\nLine 6: {line6}")
print(f"Tokens 6: {sorted(tokens6)}")
jaccard3 = calculate_jaccard_similarity(tokens5, tokens6)
print(f"Jaccard: {jaccard3:.3f} ({jaccard3*100:.1f}%)")
print(f"Intersection: {tokens5.intersection(tokens6)}")
print(f"Union: {tokens5.union(tokens6)}")
