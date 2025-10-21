#!/usr/bin/env python3
"""
File-by-File Comparison Engine for Code Turnitin

This module implements granular file-level similarity analysis for enhanced 
plagiarism detection accuracy. It addresses limitations of concatenated 
repository analysis by providing:

1. Individual file similarity analysis
2. File importance weighting
3. Structural similarity assessment
4. Enhanced partial plagiarism detection

Author: Code Turnitin Development Team
Date: October 2025
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from datetime import datetime

# Import existing similarity algorithms
from .similarity_checker import calculate_jaccard_similarity, winnowing, preprocess_code, hash_k_gram_optimized, generate_k_grams

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FileInfo:
    """Information about a source code file."""
    path: str
    relative_path: str
    filename: str
    extension: str
    size_bytes: int
    lines_count: int
    importance_weight: float
    file_type: str  # 'core', 'config', 'test', 'documentation'

@dataclass
class FileSimilarity:
    """Similarity result between two files."""
    source_file: FileInfo
    target_file: FileInfo
    similarity_score: float
    similar_blocks: List[Dict[str, Any]]
    winnowing_fingerprints: int
    matched_fingerprints: int
    analysis_metadata: Dict[str, Any]

@dataclass
class RepositorySimilarity:
    """Complete repository comparison result."""
    source_repo_id: str
    target_repo_id: str
    overall_similarity: float
    weighted_similarity: float
    file_similarities: List[FileSimilarity]
    structural_similarity: Dict[str, float]
    analysis_summary: Dict[str, Any]
    processing_time: float

class FileClassifier:
    """Classifies files by importance and type for weighted analysis."""
    
    # File extension mappings
    CODE_EXTENSIONS = {'.py', '.js', '.java', '.cpp', '.c', '.h', '.hpp', '.cs', '.php', '.rb', '.go', '.rs', '.kt', '.swift', '.ts'}
    CONFIG_EXTENSIONS = {'.json', '.xml', '.yaml', '.yml', '.ini', '.conf', '.config', '.env', '.properties'}
    DOC_EXTENSIONS = {'.md', '.txt', '.rst', '.doc', '.docx', '.pdf'}
    TEST_PATTERNS = {'test', 'tests', 'spec', 'specs', '__test__', '__tests__'}
    
    @classmethod
    def classify_file(cls, file_path: str, repo_root: str) -> FileInfo:
        """Classify a file and determine its importance weight."""
        path_obj = Path(file_path)
        relative_path = os.path.relpath(file_path, repo_root)
        
        # Basic file information
        filename = path_obj.name
        extension = path_obj.suffix.lower()
        
        # Calculate file size and lines
        size_bytes = 0
        lines_count = 0
        try:
            size_bytes = os.path.getsize(file_path)
            if extension in cls.CODE_EXTENSIONS:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines_count = sum(1 for _ in f)
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
        
        # Determine file type and importance
        file_type, importance_weight = cls._determine_importance(relative_path, filename, extension)
        
        return FileInfo(
            path=file_path,
            relative_path=relative_path,
            filename=filename,
            extension=extension,
            size_bytes=size_bytes,
            lines_count=lines_count,
            importance_weight=importance_weight,
            file_type=file_type
        )
    
    @classmethod
    def _determine_importance(cls, relative_path: str, filename: str, extension: str) -> Tuple[str, float]:
        """Determine file type and importance weight."""
        relative_lower = relative_path.lower()
        filename_lower = filename.lower()
        
        # Test files (lowest importance)
        if any(pattern in relative_lower for pattern in cls.TEST_PATTERNS):
            return 'test', 0.3
        
        # Configuration files
        if extension in cls.CONFIG_EXTENSIONS:
            return 'config', 0.4
        
        # Documentation files
        if extension in cls.DOC_EXTENSIONS:
            return 'documentation', 0.2
        
        # Core source code files
        if extension in cls.CODE_EXTENSIONS:
            # Main/entry point files get highest weight
            if any(main_name in filename_lower for main_name in ['main', 'app', 'index', 'server']):
                return 'core', 1.0
            
            # Utility and library files
            if any(util_name in filename_lower for util_name in ['util', 'helper', 'lib', 'common', 'shared']):
                return 'core', 0.7
            
            # Regular source files
            return 'core', 0.8
        
        # Unknown file types
        return 'other', 0.1

class FileComparisonEngine:
    """Core engine for file-by-file repository comparison."""
    
    def __init__(self, k: int = 6, w: int = 10, similarity_threshold: float = 0.1):
        """
        Initialize the file comparison engine.
        
        Args:
            k: K-gram size for winnowing algorithm
            w: Window size for winnowing algorithm
            similarity_threshold: Minimum similarity to consider files related
        """
        self.k = k
        self.w = w
        self.similarity_threshold = similarity_threshold
        self.file_classifier = FileClassifier()
    
    def analyze_repositories(self, source_repo_path: str, target_repo_path: str, 
                           source_repo_id: str, target_repo_id: str) -> RepositorySimilarity:
        """
        Perform comprehensive file-by-file analysis between two repositories.
        
        Args:
            source_repo_path: Path to source repository
            target_repo_path: Path to target repository
            source_repo_id: ID of source repository
            target_repo_id: ID of target repository
            
        Returns:
            RepositorySimilarity object with detailed analysis results
        """
        start_time = datetime.now()
        
        try:
            # Discover and classify files
            source_files = self._discover_files(source_repo_path)
            target_files = self._discover_files(target_repo_path)
            
            logger.info(f"Found {len(source_files)} source files and {len(target_files)} target files")
            
            # Perform file-by-file comparisons
            file_similarities = self._compare_all_files(source_files, target_files)
            
            # Calculate overall similarities
            overall_similarity = self._calculate_overall_similarity(file_similarities)
            weighted_similarity = self._calculate_weighted_similarity(file_similarities)
            
            # Analyze structural similarity
            structural_similarity = self._analyze_structural_similarity(source_files, target_files)
            
            # Generate analysis summary
            analysis_summary = self._generate_analysis_summary(file_similarities, source_files, target_files)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return RepositorySimilarity(
                source_repo_id=source_repo_id,
                target_repo_id=target_repo_id,
                overall_similarity=overall_similarity,
                weighted_similarity=weighted_similarity,
                file_similarities=file_similarities,
                structural_similarity=structural_similarity,
                analysis_summary=analysis_summary,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Repository analysis failed: {e}")
            # Return empty result on error
            processing_time = (datetime.now() - start_time).total_seconds()
            return RepositorySimilarity(
                source_repo_id=source_repo_id,
                target_repo_id=target_repo_id,
                overall_similarity=0.0,
                weighted_similarity=0.0,
                file_similarities=[],
                structural_similarity={},
                analysis_summary={'error': str(e)},
                processing_time=processing_time
            )
    
    def _discover_files(self, repo_path: str) -> List[FileInfo]:
        """Discover and classify all relevant files in a repository."""
        files = []
        
        try:
            for root, dirs, filenames in os.walk(repo_path):
                # Skip .git and other version control directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    
                    # Skip binary and hidden files
                    if filename.startswith('.') or self._is_binary_file(file_path):
                        continue
                    
                    # Only process relevant file types
                    if self._is_relevant_file(filename):
                        file_info = self.file_classifier.classify_file(file_path, repo_path)
                        files.append(file_info)
        
        except Exception as e:
            logger.error(f"Error discovering files in {repo_path}: {e}")
        
        return files
    
    def _is_binary_file(self, file_path: str) -> bool:
        """Check if a file is binary (non-text)."""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except:
            return True
    
    def _is_relevant_file(self, filename: str) -> bool:
        """Check if a file is relevant for similarity analysis."""
        extension = Path(filename).suffix.lower()
        relevant_extensions = {'.py', '.js', '.java', '.cpp', '.c', '.h', '.hpp', '.cs', 
                             '.php', '.rb', '.go', '.rs', '.kt', '.swift', '.ts', '.json'}
        return extension in relevant_extensions
    
    def _compare_all_files(self, source_files: List[FileInfo], target_files: List[FileInfo]) -> List[FileSimilarity]:
        """Compare all relevant file pairs between source and target repositories."""
        file_similarities = []
        
        # Use threading for parallel comparison
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_pair = {}
            
            for source_file in source_files:
                for target_file in target_files:
                    # Only compare files of the same type and similar purpose
                    if self._should_compare_files(source_file, target_file):
                        future = executor.submit(self._compare_files, source_file, target_file)
                        future_to_pair[future] = (source_file, target_file)
            
            # Collect results
            for future in as_completed(future_to_pair):
                try:
                    similarity = future.result()
                    if similarity and similarity.similarity_score >= self.similarity_threshold:
                        file_similarities.append(similarity)
                except Exception as e:
                    source_file, target_file = future_to_pair[future]
                    logger.error(f"Error comparing {source_file.filename} with {target_file.filename}: {e}")
        
        # Sort by similarity score (highest first)
        file_similarities.sort(key=lambda x: x.similarity_score, reverse=True)
        return file_similarities
    
    def _should_compare_files(self, source_file: FileInfo, target_file: FileInfo) -> bool:
        """Determine if two files should be compared."""
        # Same extension
        if source_file.extension != target_file.extension:
            return False
        
        # Both must be code files
        if source_file.file_type not in ['core', 'config'] or target_file.file_type not in ['core', 'config']:
            return False
        
        # Skip very small files
        if source_file.lines_count < 5 or target_file.lines_count < 5:
            return False
        
        return True
    
    def _compare_files(self, source_file: FileInfo, target_file: FileInfo) -> Optional[FileSimilarity]:
        """Compare two individual files using the winnowing algorithm."""
        try:
            # Preprocess both files
            source_tokens, source_lines = preprocess_code(source_file.path)
            target_tokens, target_lines = preprocess_code(target_file.path)
            
            if not source_tokens or not target_tokens:
                return None
            
            # Generate k-grams
            source_k_grams = generate_k_grams(source_tokens, self.k)
            target_k_grams = generate_k_grams(target_tokens, self.k)
            
            if not source_k_grams or not target_k_grams:
                return None
            
            # Hash k-grams
            source_hashed = [(hash_k_gram_optimized(kg[0]), kg, (kg[1], kg[2])) for kg in source_k_grams]
            target_hashed = [(hash_k_gram_optimized(kg[0]), kg, (kg[1], kg[2])) for kg in target_k_grams]
            
            # Apply winnowing
            source_fingerprints = winnowing(source_hashed, self.w)
            target_fingerprints = winnowing(target_hashed, self.w)
            
            # Calculate similarity
            similarity_score, intersection_count, union_count = calculate_jaccard_similarity(source_fingerprints, target_fingerprints)
            
            # Find similar blocks
            similar_blocks = self._find_similar_blocks(source_fingerprints, target_fingerprints, 
                                                     source_lines, target_lines)
            
            # Create analysis metadata
            metadata = {
                'source_k_grams': len(source_k_grams),
                'target_k_grams': len(target_k_grams),
                'source_fingerprints': len(source_fingerprints),
                'target_fingerprints': len(target_fingerprints),
                'intersection_count': intersection_count,
                'union_count': union_count,
                'algorithm_params': {'k': self.k, 'w': self.w}
            }
            
            return FileSimilarity(
                source_file=source_file,
                target_file=target_file,
                similarity_score=similarity_score,
                similar_blocks=similar_blocks,
                winnowing_fingerprints=len(source_fingerprints) + len(target_fingerprints),
                matched_fingerprints=intersection_count,
                analysis_metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error comparing files {source_file.filename} and {target_file.filename}: {e}")
            return None
    
    def _find_similar_blocks(self, source_fingerprints: List, target_fingerprints: List,
                           source_lines: List[str], target_lines: List[str]) -> List[Dict[str, Any]]:
        """Find similar code blocks between two files."""
        similar_blocks = []
        
        try:
            # Create hash to line mapping
            source_hash_to_lines = {}
            target_hash_to_lines = {}
            
            for hash_val, k_gram_info, line_info in source_fingerprints:
                if hash_val not in source_hash_to_lines:
                    source_hash_to_lines[hash_val] = []
                source_hash_to_lines[hash_val].append(line_info)
            
            for hash_val, k_gram_info, line_info in target_fingerprints:
                if hash_val not in target_hash_to_lines:
                    target_hash_to_lines[hash_val] = []
                target_hash_to_lines[hash_val].append(line_info)
            
            # Find matching hashes
            matching_hashes = set(source_hash_to_lines.keys()) & set(target_hash_to_lines.keys())
            
            for hash_val in matching_hashes:
                for source_line_info in source_hash_to_lines[hash_val]:
                    for target_line_info in target_hash_to_lines[hash_val]:
                        source_start, source_end = source_line_info
                        target_start, target_end = target_line_info
                        
                        # Get the actual code lines
                        source_code = '\n'.join(source_lines[source_start-1:source_end])
                        target_code = '\n'.join(target_lines[target_start-1:target_end])
                        
                        similar_blocks.append({
                            'hash': hash_val,
                            'source_lines': {'start': source_start, 'end': source_end},
                            'target_lines': {'start': target_start, 'end': target_end},
                            'source_code': source_code.strip(),
                            'target_code': target_code.strip()
                        })
            
            # Sort by source line number
            similar_blocks.sort(key=lambda x: x['source_lines']['start'])
            
        except Exception as e:
            logger.error(f"Error finding similar blocks: {e}")
        
        return similar_blocks
    
    def _calculate_overall_similarity(self, file_similarities: List[FileSimilarity]) -> float:
        """Calculate overall repository similarity (simple average)."""
        if not file_similarities:
            return 0.0
        
        total_similarity = sum(fs.similarity_score for fs in file_similarities)
        return total_similarity / len(file_similarities)
    
    def _calculate_weighted_similarity(self, file_similarities: List[FileSimilarity]) -> float:
        """Calculate weighted repository similarity based on file importance."""
        if not file_similarities:
            return 0.0
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for fs in file_similarities:
            # Use the maximum weight between source and target files
            weight = max(fs.source_file.importance_weight, fs.target_file.importance_weight)
            weighted_sum += fs.similarity_score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _analyze_structural_similarity(self, source_files: List[FileInfo], 
                                     target_files: List[FileInfo]) -> Dict[str, float]:
        """Analyze structural similarity between repositories."""
        try:
            # Directory structure similarity
            source_dirs = set(os.path.dirname(f.relative_path) for f in source_files)
            target_dirs = set(os.path.dirname(f.relative_path) for f in target_files)
            
            dir_similarity = len(source_dirs & target_dirs) / len(source_dirs | target_dirs) if (source_dirs | target_dirs) else 0.0
            
            # File naming patterns
            source_names = set(f.filename for f in source_files)
            target_names = set(f.filename for f in target_files)
            
            name_similarity = len(source_names & target_names) / len(source_names | target_names) if (source_names | target_names) else 0.0
            
            # File type distribution
            source_types = {}
            target_types = {}
            
            for f in source_files:
                source_types[f.extension] = source_types.get(f.extension, 0) + 1
            
            for f in target_files:
                target_types[f.extension] = target_types.get(f.extension, 0) + 1
            
            # Calculate type distribution similarity
            all_types = set(source_types.keys()) | set(target_types.keys())
            type_similarity = 0.0
            
            if all_types:
                for ext in all_types:
                    source_count = source_types.get(ext, 0)
                    target_count = target_types.get(ext, 0)
                    total_source = sum(source_types.values())
                    total_target = sum(target_types.values())
                    
                    if total_source > 0 and total_target > 0:
                        source_ratio = source_count / total_source
                        target_ratio = target_count / total_target
                        type_similarity += 1.0 - abs(source_ratio - target_ratio)
                
                type_similarity /= len(all_types)
            
            return {
                'directory_similarity': dir_similarity,
                'filename_similarity': name_similarity,
                'file_type_similarity': type_similarity,
                'overall_structural': (dir_similarity + name_similarity + type_similarity) / 3
            }
            
        except Exception as e:
            logger.error(f"Error analyzing structural similarity: {e}")
            return {'directory_similarity': 0.0, 'filename_similarity': 0.0, 
                   'file_type_similarity': 0.0, 'overall_structural': 0.0}
    
    def _generate_analysis_summary(self, file_similarities: List[FileSimilarity],
                                 source_files: List[FileInfo], target_files: List[FileInfo]) -> Dict[str, Any]:
        """Generate summary statistics for the analysis."""
        if not file_similarities:
            return {
                'total_comparisons': 0,
                'significant_similarities': 0,
                'exact_copies': 0,
                'modified_copies': 0,
                'unique_files': len(source_files),
                'similarity_distribution': {}
            }
        
        # Categorize similarities
        exact_copies = len([fs for fs in file_similarities if fs.similarity_score >= 0.9])
        modified_copies = len([fs for fs in file_similarities if 0.7 <= fs.similarity_score < 0.9])
        significant_similarities = len([fs for fs in file_similarities if fs.similarity_score >= 0.3])
        
        # Similarity distribution
        distribution = {'0.0-0.3': 0, '0.3-0.5': 0, '0.5-0.7': 0, '0.7-0.9': 0, '0.9-1.0': 0}
        
        for fs in file_similarities:
            score = fs.similarity_score
            if score < 0.3:
                distribution['0.0-0.3'] += 1
            elif score < 0.5:
                distribution['0.3-0.5'] += 1
            elif score < 0.7:
                distribution['0.5-0.7'] += 1
            elif score < 0.9:
                distribution['0.7-0.9'] += 1
            else:
                distribution['0.9-1.0'] += 1
        
        return {
            'total_comparisons': len(file_similarities),
            'significant_similarities': significant_similarities,
            'exact_copies': exact_copies,
            'modified_copies': modified_copies,
            'unique_files': len(source_files) - len(set(fs.source_file.filename for fs in file_similarities)),
            'similarity_distribution': distribution,
            'top_similar_files': [
                {
                    'source': fs.source_file.filename,
                    'target': fs.target_file.filename,
                    'similarity': fs.similarity_score
                } for fs in file_similarities[:5]
            ]
        }

# Utility function for demo integration
def analyze_demo_repositories(source_repo_path: str, target_repo_path: str,
                            source_repo_id: str, target_repo_id: str,
                            k: int = 6, w: int = 10) -> RepositorySimilarity:
    """
    Convenience function for analyzing demo repositories.
    
    Args:
        source_repo_path: Path to source repository
        target_repo_path: Path to target repository  
        source_repo_id: ID of source repository
        target_repo_id: ID of target repository
        k: K-gram size (default: 6)
        w: Window size (default: 10)
        
    Returns:
        RepositorySimilarity object with detailed analysis
    """
    engine = FileComparisonEngine(k=k, w=w)
    return engine.analyze_repositories(source_repo_path, target_repo_path, 
                                     source_repo_id, target_repo_id)