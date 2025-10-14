#!/usr/bin/env python3
"""
Demo Similarity Analyzer for Code Turnitin Thesis Presentation

This module provides similarity analysis functionality for demo mode,
working with local repository data instead of live GitHub API calls.

Author: Created for Code Turnitin thesis presentation
Date: September 2025
"""

import json
import logging
import random
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import hashlib

# Import existing similarity algorithms
import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from algorithms.similarity_checker import calculate_jaccard_similarity, winnowing, preprocess_code
    from demo.repo_downloader import RepositoryDownloader
    SIMILARITY_ALGORITHMS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import similarity algorithms: {e}")
    SIMILARITY_ALGORITHMS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DemoSimilarityAnalyzer:
    """Similarity analysis for demo mode with local data simulation."""
    
    def __init__(self):
        """Initialize the demo similarity analyzer."""
        self.algorithms = self._initialize_algorithms()
        self.mock_code_cache = {}
        self.analysis_history = []
        self.repo_downloader = RepositoryDownloader() if SIMILARITY_ALGORITHMS_AVAILABLE else None
        self.downloaded_repos_info = None
        self._load_downloaded_repos_info()
        
    def _initialize_algorithms(self) -> Dict[str, Any]:
        """Initialize available similarity algorithms."""
        algorithms = {}
        
        if SIMILARITY_ALGORITHMS_AVAILABLE:
            # Use existing algorithms from the project
            algorithms['jaccard'] = {
                'name': 'Jaccard Similarity',
                'function': self._calculate_jaccard_similarity,
                'description': 'Uses existing winnowing algorithm with Jaccard similarity'
            }
            logger.info("Initialized similarity algorithms successfully")
        else:
            # Create fallback algorithm implementations for demo
            algorithms = self._create_fallback_algorithms()
        
        return algorithms
        
    def _load_downloaded_repos_info(self):
        """Load information about downloaded repositories from multiple sources."""
        try:
            repo_info = {}
            
            # Load Java repositories info
            java_log_path = os.path.join("data", "demo_repos", "download_log.json")
            if os.path.exists(java_log_path):
                with open(java_log_path, 'r', encoding='utf-8') as f:
                    java_data = json.load(f)
                    for repo in java_data.get("successful_downloads", []):
                        repo_info[repo["name"]] = {
                            "language": "Java",
                            "path": os.path.join("data", "demo_repos", repo["name"]),
                            "size": repo.get("size_bytes", 0),
                            "files": repo.get("file_count", 0)
                        }
                logger.info(f"Loaded {len(java_data.get('successful_downloads', []))} Java repositories")
            
            # Load JavaScript repositories info
            js_log_path = os.path.join("data", "demo_repos_js_filtered", "filtered_download_log.json")
            if os.path.exists(js_log_path):
                with open(js_log_path, 'r', encoding='utf-8') as f:
                    js_data = json.load(f)
                    for repo in js_data.get("successful_downloads", []):
                        repo_info[repo["name"]] = {
                            "language": "JavaScript",
                            "path": os.path.join("data", "demo_repos_js_filtered", repo["name"]),
                            "size": repo.get("original_size", 0),
                            "files": 0  # Will be calculated if needed
                        }
                logger.info(f"Loaded {len(js_data.get('successful_downloads', []))} JavaScript repositories")
            
            # Load Python repositories info
            python_log_path = os.path.join("data", "demo_repos_python_filtered", "filtered_download_log.json")
            if os.path.exists(python_log_path):
                with open(python_log_path, 'r', encoding='utf-8') as f:
                    python_data = json.load(f)
                    # Handle both elasticsearch-4a and elasticsearch-4b categories
                    for category in ["elasticsearch-4a", "elasticsearch-4b"]:
                        if category in python_data.get("repositories", {}):
                            for repo in python_data["repositories"][category]:
                                repo_info[repo["name"]] = {
                                    "language": "Python",
                                    "path": os.path.join("data", "demo_repos_python", repo["name"]),
                                    "size": repo.get("size", 0),
                                    "files": repo.get("estimated_files", 0)
                                }
                python_repo_count = len([r for r in repo_info.values() if r["language"] == "Python"])
                logger.info(f"Loaded {python_repo_count} Python repositories")
            else:
                # Fallback: scan Python directory directly
                python_dir = os.path.join("data", "demo_repos_python")
                if os.path.exists(python_dir):
                    python_count = 0
                    for repo_name in os.listdir(python_dir):
                        repo_path = os.path.join(python_dir, repo_name)
                        if os.path.isdir(repo_path):
                            repo_info[repo_name] = {
                                "language": "Python",
                                "path": repo_path,
                                "size": 0,  # Will be calculated if needed
                                "files": 0
                            }
                            python_count += 1
                    logger.info(f"Loaded {python_count} Python repositories from directory scan")
            
            self.downloaded_repos_info = repo_info
            logger.info(f"Total downloaded repositories: {len(repo_info)}")
            
        except Exception as e:
            logger.warning(f"Could not load downloaded repositories info: {e}")
            self.downloaded_repos_info = {}
    
    def _get_real_code_from_downloaded_repo(self, repo_name: str) -> Optional[str]:
        """Get real code content from downloaded repository."""
        if not repo_name:
            return None
        
        try:
            # Look for repository directory in multiple demo paths
            demo_paths = [
                os.path.join("data", "demo_repos"),  # Java repositories
                os.path.join("data", "demo_repos_js_filtered"),  # JavaScript repositories
                os.path.join("data", "demo_repos_python"),  # Python repositories
            ]
            
            repo_dir = None
            for base_demo_path in demo_paths:
                if not os.path.exists(base_demo_path):
                    print(f"DEBUG: Demo path not found: {base_demo_path}")
                    continue
                
                target_dir = os.path.join(base_demo_path, repo_name)
                if os.path.exists(target_dir) and os.path.isdir(target_dir):
                    repo_dir = target_dir
                    print(f"DEBUG: Found exact match directory: {repo_dir}")
                    break
            
            if not repo_dir:
                print(f"DEBUG: Repository directory not found in any demo path: {repo_name}")
                return None
            
            # Read code files from the repository
            code_content = []
            file_count = 0
            
            print(f"DEBUG: Scanning directory: {repo_dir}")
            for root, dirs, files in os.walk(repo_dir):
                # Skip git, node_modules, and other unnecessary directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and 
                          d not in ['node_modules', 'vendor', 'target', 'build', 'dist', '__pycache__', 'venv', 'env', 'bin', 'lib', 'obj']]
                
                for file in files:
                    # Support multiple programming languages, exclude unnecessary files
                    if (file.endswith(('.py', '.java', '.js', '.jsx', '.ts', '.tsx', '.cpp', '.c', '.h', '.html', '.css', '.php', '.rb', '.go', '.rs', '.kt')) and
                        not file.endswith(('.min.js', '.min.css')) and
                        not file.startswith('.') and
                        'node_modules' not in root and
                        'vendor' not in root and
                        'target' not in root and
                        'build' not in root and
                        'dist' not in root):
                        file_path = os.path.join(root, file)
                        print(f"DEBUG: Processing file: {file_path}")
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read().strip()
                                if content and len(content) > 50:  # Only include substantial files
                                    relative_path = os.path.relpath(file_path, repo_dir)
                                    
                                    # Add language-specific comment format
                                    if file.endswith(('.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h', '.php', '.kt', '.go', '.rs')):
                                        code_content.append(f"// File: {relative_path}\n{content}\n")
                                    elif file.endswith(('.py', '.rb')):
                                        code_content.append(f"# File: {relative_path}\n{content}\n")
                                    elif file.endswith(('.html', '.css')):
                                        code_content.append(f"/* File: {relative_path} */\n{content}\n")
                                    else:
                                        code_content.append(f"// File: {relative_path}\n{content}\n")
                                    
                                    file_count += 1
                                    print(f"DEBUG: Added file: {relative_path} ({len(content)} chars)")
                        except Exception as e:
                            print(f"DEBUG: Could not read file {file_path}: {e}")
                            continue
            
            if code_content:
                combined_code = "\n".join(code_content)
                print(f"DEBUG: Successfully retrieved {file_count} files from repository: {repo_name} (total chars: {len(combined_code)})")
                return combined_code
            else:
                print(f"DEBUG: No substantial code files found in: {repo_name}")
                
        except Exception as e:
            print(f"DEBUG: Error retrieving real code from {repo_name}: {e}")
        
        return None
    
    def _calculate_jaccard_similarity(self, code1: str, code2: str) -> float:
        """
        Enhanced Jaccard similarity using advanced winnowing algorithm from similarity_checker.py
        
        Improvements:
        1. Uses proper winnowing algorithm implementation
        2. Rolling hash for better performance 
        3. Enhanced preprocessing with identifier normalization
        4. Deterministic fingerprint selection
        5. Better parameter tuning for accuracy
        """
        import tempfile
        import os
        
        try:
            # Create temporary files for the code content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f1:
                f1.write(code1)
                temp_file1 = f1.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f2:
                f2.write(code2)
                temp_file2 = f2.name
            
            # Import enhanced similarity functions from the robust algorithm
            from algorithms.similarity_checker import (
                preprocess_code, generate_k_grams, hash_k_gram_optimized, 
                winnowing, calculate_jaccard_similarity
            )
            
            # Balanced parameters for optimal accuracy
            k = 6  # Balanced k-gram size for good discrimination without being too strict
            w = 10  # Standard window size for stable fingerprints
            
            # Step 1: Enhanced preprocessing with identifier normalization
            tokens_a, lines_a = preprocess_code(temp_file1, None)
            tokens_b, lines_b = preprocess_code(temp_file2, None)
            
            if not tokens_a or not tokens_b:
                self._cleanup_temp_files(temp_file1, temp_file2)
                return self._fallback_similarity_calculation(code1, code2)
            
            # Step 2: Generate k-grams with line information
            k_grams_a = generate_k_grams(tokens_a, k)
            k_grams_b = generate_k_grams(tokens_b, k)
            
            if not k_grams_a or not k_grams_b:
                self._cleanup_temp_files(temp_file1, temp_file2)
                return self._fallback_similarity_calculation(code1, code2)
            
            # Step 3: Hash k-grams using optimized rolling hash
            hashed_k_grams_a = []
            for k_gram_tuple, start_line, end_line in k_grams_a:
                hash_val = hash_k_gram_optimized(k_gram_tuple)
                hashed_k_grams_a.append((hash_val, (k_gram_tuple, start_line, end_line), (start_line, end_line)))
            
            hashed_k_grams_b = []
            for k_gram_tuple, start_line, end_line in k_grams_b:
                hash_val = hash_k_gram_optimized(k_gram_tuple)
                hashed_k_grams_b.append((hash_val, (k_gram_tuple, start_line, end_line), (start_line, end_line)))
            
            # Step 4: Apply true winnowing algorithm with proper window management
            fingerprints_a = winnowing(hashed_k_grams_a, w)
            fingerprints_b = winnowing(hashed_k_grams_b, w)
            
            # Step 5: Calculate mathematical Jaccard similarity
            similarity_score, intersection_count, union_count = calculate_jaccard_similarity(fingerprints_a, fingerprints_b)
            
            # Clean up temporary files
            self._cleanup_temp_files(temp_file1, temp_file2)
            
            # Log detailed analysis for debugging
            logger.debug(f"Enhanced Jaccard Analysis: k={k}, w={w}, fingerprints_a={len(fingerprints_a)}, "
                        f"fingerprints_b={len(fingerprints_b)}, intersection={intersection_count}, "
                        f"union={union_count}, similarity={similarity_score:.4f}")
            
            return similarity_score
            
        except Exception as e:
            logger.warning(f"Error in enhanced Jaccard similarity calculation: {e}")
            # Clean up temporary files if they exist  
            self._cleanup_temp_files(
                locals().get('temp_file1', ''), 
                locals().get('temp_file2', '')
            )
            # Fallback to deterministic calculation
            return self._fallback_similarity_calculation(code1, code2)
    
    def _cleanup_temp_files(self, *file_paths):
        """Safely clean up temporary files"""
        for file_path in file_paths:
            try:
                if file_path and os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {file_path}: {e}")
    
    def _fallback_similarity_calculation(self, code1: str, code2: str) -> float:
        """
        Enhanced fallback similarity calculation when winnowing fails.
        
        Uses a more sophisticated approach than simple token matching:
        1. Code normalization (remove comments, strings, whitespace)
        2. Token-based Jaccard similarity
        3. Character-level similarity as backup
        """
        import re
        
        try:
            # Normalize code by removing comments, strings, and extra whitespace
            def normalize_code(code):
                # Remove single line comments
                code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
                code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
                
                # Remove multi-line comments  
                code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
                
                # Remove string literals
                code = re.sub(r'"[^"]*"', 'STRING', code)
                code = re.sub(r"'[^']*'", 'STRING', code)
                code = re.sub(r'`[^`]*`', 'STRING', code)
                
                # Remove extra whitespace and normalize
                code = re.sub(r'\s+', ' ', code)
                code = code.strip().lower()
                
                return code
            
            # Normalize both codes
            normalized_code1 = normalize_code(code1)
            normalized_code2 = normalize_code(code2)
            
            if not normalized_code1 and not normalized_code2:
                return 1.0  # Both empty
            if not normalized_code1 or not normalized_code2:
                return 0.0  # One empty
            
            # Method 1: Token-based Jaccard similarity
            tokens1 = set(re.findall(r'\w+', normalized_code1))
            tokens2 = set(re.findall(r'\w+', normalized_code2))
            
            if tokens1 or tokens2:
                token_intersection = len(tokens1 & tokens2)
                token_union = len(tokens1 | tokens2)
                token_similarity = token_intersection / token_union if token_union > 0 else 0.0
            else:
                token_similarity = 1.0 if not tokens1 and not tokens2 else 0.0
            
            # Method 2: Character sequence similarity (for structure)
            def char_similarity(s1, s2):
                if len(s1) == 0 and len(s2) == 0:
                    return 1.0
                if len(s1) == 0 or len(s2) == 0:
                    return 0.0
                
                # Simple character-level matching
                char_set1 = set(s1)
                char_set2 = set(s2)
                char_intersection = len(char_set1 & char_set2)
                char_union = len(char_set1 | char_set2)
                return char_intersection / char_union if char_union > 0 else 0.0
            
            char_sim = char_similarity(normalized_code1, normalized_code2)
            
            # Combine both methods (weighted average)
            final_similarity = 0.7 * token_similarity + 0.3 * char_sim
            
            logger.debug(f"Fallback calculation: token_sim={token_similarity:.3f}, "
                        f"char_sim={char_sim:.3f}, final={final_similarity:.3f}")
            
            return final_similarity
            
        except Exception as e:
            logger.warning(f"Error in fallback similarity calculation: {e}")
            # Ultimate fallback - basic string similarity
            if code1 == code2:
                return 1.0
            elif not code1 or not code2:
                return 0.0
            else:
                # Very basic similarity based on length ratio
                len1, len2 = len(code1), len(code2)
                min_len, max_len = min(len1, len2), max(len1, len2)
                return min_len / max_len if max_len > 0 else 0.0
    
    def _create_fallback_algorithms(self) -> Dict[str, Any]:
        """Create fallback algorithm implementations for demo purposes."""
        class DemoAlgorithm:
            def __init__(self, name: str, base_similarity: float):
                self.name = name
                self.base_similarity = base_similarity
            
            def calculate_similarity(self, code1: str, code2: str) -> float:
                # Create deterministic but varied similarity based on code content
                hash1 = int(hashlib.md5(code1.encode()).hexdigest()[:8], 16)
                hash2 = int(hashlib.md5(code2.encode()).hexdigest()[:8], 16)
                variation = abs(hash1 - hash2) / (2**32) * 0.4  # Max 40% variation
                return max(0.0, min(1.0, self.base_similarity + variation - 0.2))
        
        return {
            'jaccard': DemoAlgorithm('Jaccard', 0.3),
            'cosine': DemoAlgorithm('Cosine', 0.4),
            'levenshtein': DemoAlgorithm('Levenshtein', 0.35)
        }
    
    def generate_mock_code(self, repo: Dict[str, Any]) -> str:
        """Generate realistic mock code content based on repository metadata."""
        language = repo.get('language', 'Unknown')
        name = repo.get('name', 'unknown')
        size = repo.get('size', 10)
        
        # Use a deterministic seed based on repository ID for consistent results
        seed = repo.get('id', 0)
        random.seed(seed)
        
        # Generate code based on language
        if language.lower() == 'java':
            code = self._generate_java_code(name, size)
        elif language.lower() == 'javascript':
            code = self._generate_javascript_code(name, size)
        elif language.lower() == 'python':
            code = self._generate_python_code(name, size)
        else:
            code = self._generate_generic_code(name, size)
        
        # Reset random seed
        random.seed()
        
        return code
    
    def _generate_java_code(self, name: str, size: int) -> str:
        """Generate mock Java code."""
        class_name = ''.join(word.capitalize() for word in name.split('-')[:2])
        
        # Base code structure
        code_parts = [
            f"public class {class_name} {{",
            "    private String data;",
            "    private int count;",
            "",
            f"    public {class_name}() {{",
            "        this.data = \"\";",
            "        this.count = 0;",
            "    }",
            "",
            "    public void processData(String input) {",
            "        if (input != null && !input.isEmpty()) {",
            "            this.data = input.trim();",
            "            this.count++;",
            "        }",
            "    }",
            "",
            "    public String getData() {",
            "        return data;",
            "    }",
            "",
            "    public int getCount() {",
            "        return count;",
            "    }"
        ]
        
        # Add more methods based on size
        method_templates = [
            ("validate", "public boolean validate() {\n        return data != null && !data.isEmpty();\n    }"),
            ("reset", "public void reset() {\n        this.data = \"\";\n        this.count = 0;\n    }"),
            ("toString", f"public String toString() {{\n        return \"{class_name}[data=\" + data + \", count=\" + count + \"]\";\n    }}"),
            ("equals", f"public boolean equals(Object obj) {{\n        if (this == obj) return true;\n        if (obj instanceof {class_name}) {{\n            {class_name} other = ({class_name}) obj;\n            return Objects.equals(data, other.data);\n        }}\n        return false;\n    }}")
        ]
        
        methods_to_add = min(len(method_templates), max(1, size // 50))
        for i in range(methods_to_add):
            code_parts.extend(["", "    " + method_templates[i][1]])
        
        code_parts.append("}")
        
        return "\n".join(code_parts)
    
    def _generate_javascript_code(self, name: str, size: int) -> str:
        """Generate mock JavaScript code."""
        module_name = name.replace('-', '_')
        
        code_parts = [
            f"// {module_name} module",
            "class DataProcessor {",
            "    constructor() {",
            "        this.data = [];",
            "        this.config = {};",
            "    }",
            "",
            "    addData(item) {",
            "        if (item && typeof item === 'object') {",
            "            this.data.push(item);",
            "            return true;",
            "        }",
            "        return false;",
            "    }",
            "",
            "    processAll() {",
            "        return this.data.map(item => {",
            "            return {",
            "                ...item,",
            "                processed: true,",
            "                timestamp: Date.now()",
            "            };",
            "        });",
            "    }",
            "",
            "    getCount() {",
            "        return this.data.length;",
            "    }"
        ]
        
        # Add more functionality based on size
        if size > 100:
            code_parts.extend([
                "",
                "    filterData(predicate) {",
                "        return this.data.filter(predicate);",
                "    }",
                "",
                "    sortData(compareFn) {",
                "        return [...this.data].sort(compareFn);",
                "    }"
            ])
        
        if size > 200:
            code_parts.extend([
                "",
                "    exportData() {",
                "        return {",
                "            data: this.data,",
                "            config: this.config,",
                "            exported_at: new Date().toISOString()",
                "        };",
                "    }",
                "",
                "    importData(exportedData) {",
                "        if (exportedData && exportedData.data) {",
                "            this.data = exportedData.data;",
                "            this.config = exportedData.config || {};",
                "            return true;",
                "        }",
                "        return false;",
                "    }"
            ])
        
        code_parts.extend([
            "}",
            "",
            f"module.exports = DataProcessor;"
        ])
        
        return "\n".join(code_parts)
    
    def _generate_python_code(self, name: str, size: int) -> str:
        """Generate mock Python code."""
        class_name = ''.join(word.capitalize() for word in name.split('-')[:2])
        
        code_parts = [
            f'"""',
            f'{class_name} module for data processing',
            f'Generated for demo purposes',
            f'"""',
            "",
            "import json",
            "from typing import List, Dict, Any, Optional",
            "from datetime import datetime",
            "",
            f"class {class_name}:",
            '    """Main class for data processing operations."""',
            "",
            "    def __init__(self):",
            "        self.data = []",
            "        self.config = {}",
            "        self.created_at = datetime.now()",
            "",
            "    def add_item(self, item: Dict[str, Any]) -> bool:",
            '        """Add an item to the data collection."""',
            "        if isinstance(item, dict):",
            "            self.data.append(item)",
            "            return True",
            "        return False",
            "",
            "    def process_data(self) -> List[Dict[str, Any]]:",
            '        """Process all data items."""',
            "        processed = []",
            "        for item in self.data:",
            "            processed_item = {",
            "                **item,",
            "                'processed': True,",
            "                'processed_at': datetime.now().isoformat()",
            "            }",
            "            processed.append(processed_item)",
            "        return processed",
            "",
            "    def get_count(self) -> int:",
            '        """Get the number of items."""',
            "        return len(self.data)"
        ]
        
        # Add more methods based on size
        if size > 50:
            code_parts.extend([
                "",
                "    def filter_data(self, condition: callable) -> List[Dict[str, Any]]:",
                '        """Filter data based on condition."""',
                "        return [item for item in self.data if condition(item)]",
                "",
                "    def sort_data(self, key: str, reverse: bool = False) -> List[Dict[str, Any]]:",
                '        """Sort data by specified key."""',
                "        return sorted(self.data, key=lambda x: x.get(key, ''), reverse=reverse)"
            ])
        
        if size > 100:
            code_parts.extend([
                "",
                "    def save_to_file(self, filename: str) -> bool:",
                '        """Save data to JSON file."""',
                "        try:",
                "            with open(filename, 'w') as f:",
                "                json.dump({",
                "                    'data': self.data,",
                "                    'config': self.config,",
                "                    'created_at': self.created_at.isoformat()",
                "                }, f, indent=2)",
                "            return True",
                "        except Exception:",
                "            return False",
                "",
                "    def load_from_file(self, filename: str) -> bool:",
                '        """Load data from JSON file."""',
                "        try:",
                "            with open(filename, 'r') as f:",
                "                loaded = json.load(f)",
                "                self.data = loaded.get('data', [])",
                "                self.config = loaded.get('config', {})",
                "            return True",
                "        except Exception:",
                "            return False"
            ])
        
        code_parts.extend([
            "",
            "",
            "if __name__ == '__main__':",
            f"    processor = {class_name}()",
            "    print(f'Created {class_name} instance')"
        ])
        
        return "\n".join(code_parts)
    
    def _generate_generic_code(self, name: str, size: int) -> str:
        """Generate generic mock code."""
        return f"""
// Generic code for {name}
function processData(input) {{
    const data = input || [];
    const result = data.map(item => {{
        return {{
            ...item,
            processed: true,
            timestamp: Date.now()
        }};
    }});
    
    return result;
}}

function validateInput(input) {{
    return input && Array.isArray(input) && input.length > 0;
}}

module.exports = {{ processData, validateInput }};
"""
    
    def analyze_repositories(self, source_repo: Dict[str, Any], 
                           target_repos: List[Dict[str, Any]], 
                           algorithm: str = 'jaccard') -> Dict[str, Any]:
        """Perform similarity analysis between source and target repositories."""
        if algorithm not in self.algorithms:
            algorithm = 'jaccard'  # Fallback to default
        
        # Generate or get cached code for source repository
        source_code = self._get_or_generate_code(source_repo)
        
        results = {
            'source_repository': {
                'id': source_repo.get('id'),
                'name': source_repo.get('name'),
                'language': source_repo.get('language'),
                'size': source_repo.get('size')
            },
            'algorithm': algorithm,
            'algorithm_name': algorithm.title(),
            'analysis_timestamp': datetime.now().isoformat(),
            'comparisons': [],
            'summary': {
                'total_comparisons': len(target_repos),
                'high_similarity_count': 0,
                'medium_similarity_count': 0,
                'low_similarity_count': 0,
                'average_similarity': 0.0,
                'max_similarity': 0.0,
                'min_similarity': 1.0
            }
        }
        
        similarities = []
        
        for target_repo in target_repos:
            # Generate or get cached code for target repository
            target_code = self._get_or_generate_code(target_repo)
            
            # Calculate similarity using selected algorithm
            if SIMILARITY_ALGORITHMS_AVAILABLE and algorithm in self.algorithms:
                similarity_score = self.algorithms[algorithm]['function'](source_code, target_code)
            else:
                # Use fallback algorithm
                similarity_score = self.algorithms[algorithm].calculate_similarity(source_code, target_code)
            similarities.append(similarity_score)
            
            # Categorize similarity level
            if similarity_score >= 0.7:
                level = 'high'
                results['summary']['high_similarity_count'] += 1
            elif similarity_score >= 0.4:
                level = 'medium'
                results['summary']['medium_similarity_count'] += 1
            else:
                level = 'low'
                results['summary']['low_similarity_count'] += 1
            
            comparison = {
                'target_repository': {
                    'id': target_repo.get('id'),
                    'name': target_repo.get('name'),
                    'language': target_repo.get('language'),
                    'size': target_repo.get('size')
                },
                'similarity_score': round(similarity_score, 4),
                'similarity_percentage': round(similarity_score * 100, 2),
                'similarity_level': level,
                'analysis_details': {
                    'source_code_length': len(source_code),
                    'target_code_length': len(target_code),
                    'algorithm_used': algorithm
                }
            }
            
            results['comparisons'].append(comparison)
        
        # Calculate summary statistics
        if similarities:
            results['summary']['average_similarity'] = round(sum(similarities) / len(similarities), 4)
            results['summary']['max_similarity'] = round(max(similarities), 4)
            results['summary']['min_similarity'] = round(min(similarities), 4)
        
        # Sort comparisons by similarity score (highest first)
        results['comparisons'].sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Store in analysis history
        self.analysis_history.append({
            'timestamp': results['analysis_timestamp'],
            'source_repo_id': source_repo.get('id'),
            'algorithm': algorithm,
            'comparison_count': len(target_repos),
            'max_similarity': results['summary']['max_similarity']
        })
        
        logger.info(f"Completed similarity analysis: {source_repo.get('name')} vs {len(target_repos)} repos using {algorithm}")
        
        return results
    
    def get_detailed_comparison(self, source_repo: Dict[str, Any], 
                              target_repo: Dict[str, Any], 
                              algorithm: str = 'jaccard') -> Dict[str, Any]:
        """Get detailed comparison between two repositories including code diff and similarity breakdown."""
        try:
            # Get source and target code
            source_code = self._get_or_generate_code(source_repo)
            target_code = self._get_or_generate_code(target_repo)
            
            # Calculate similarity score
            if SIMILARITY_ALGORITHMS_AVAILABLE and algorithm in self.algorithms:
                similarity_score = self.algorithms[algorithm]['function'](source_code, target_code)
            else:
                similarity_score = self.algorithms[algorithm].calculate_similarity(source_code, target_code)
            
            # Generate detailed analysis
            detailed_result = {
                'source_repository': {
                    'id': source_repo.get('id'),
                    'name': source_repo.get('name'),
                    'language': source_repo.get('language'),
                    'size': source_repo.get('size'),
                    'code_length': len(source_code)
                },
                'target_repository': {
                    'id': target_repo.get('id'),
                    'name': target_repo.get('name'),
                    'language': target_repo.get('language'),
                    'size': target_repo.get('size'),
                    'code_length': len(target_code)
                },
                'similarity': {
                    'score': round(similarity_score, 4),
                    'percentage': round(similarity_score * 100, 2),
                    'level': 'high' if similarity_score >= 0.7 else ('medium' if similarity_score >= 0.4 else 'low'),
                    'algorithm': algorithm,
                    'algorithm_name': algorithm.title()
                },
                'code_comparison': {
                    'source_code': self._format_code_for_display(source_code),
                    'target_code': self._format_code_for_display(target_code),
                    'similar_blocks': self._identify_similar_blocks(source_code, target_code),
                    'diff_lines': self._generate_diff_lines(source_code, target_code)
                },
                'winnowing_details': self._get_winnowing_details(source_code, target_code) if SIMILARITY_ALGORITHMS_AVAILABLE else None,
                'analysis_timestamp': datetime.now().isoformat(),
                'comparison_stats': {
                    'source_lines': source_code.count('\n') + 1,
                    'target_lines': target_code.count('\n') + 1,
                    'similar_line_count': self._count_similar_lines(source_code, target_code),
                    'unique_source_lines': 0,  # Will be calculated
                    'unique_target_lines': 0   # Will be calculated
                }
            }
            
            return detailed_result
            
        except Exception as e:
            logger.error(f"Error in detailed comparison: {e}")
            return {
                'error': f'Detailed comparison failed: {str(e)}',
                'source_repository': {'name': source_repo.get('name', 'Unknown')},
                'target_repository': {'name': target_repo.get('name', 'Unknown')}
            }
    
    def _format_code_for_display(self, code: str, max_lines: int = 100) -> Dict[str, Any]:
        """Format code for display in the frontend with line numbers."""
        lines = code.split('\n')
        
        # Limit lines for performance
        if len(lines) > max_lines:
            displayed_lines = lines[:max_lines]
            truncated = True
        else:
            displayed_lines = lines
            truncated = False
        
        return {
            'lines': [{'number': i + 1, 'content': line} for i, line in enumerate(displayed_lines)],
            'total_lines': len(lines),
            'displayed_lines': len(displayed_lines),
            'truncated': truncated
        }
    
    def _identify_similar_blocks(self, source_code: str, target_code: str) -> List[Dict[str, Any]]:
        """Identify similar code blocks between source and target."""
        # Simplified similar block identification
        source_lines = source_code.split('\n')
        target_lines = target_code.split('\n')
        
        similar_blocks = []
        
        # Find consecutive similar lines (simplified approach)
        for i, source_line in enumerate(source_lines[:50]):  # Limit for demo
            source_line_clean = source_line.strip()
            if len(source_line_clean) < 10:  # Skip very short lines
                continue
                
            for j, target_line in enumerate(target_lines[:50]):  # Limit for demo
                target_line_clean = target_line.strip()
                if len(target_line_clean) < 10:
                    continue
                
                # Simple similarity check (can be enhanced with more sophisticated algorithms)
                if source_line_clean == target_line_clean:
                    similar_blocks.append({
                        'source_line': i + 1,
                        'target_line': j + 1,
                        'content': source_line_clean[:100],  # Truncate for display
                        'similarity': 1.0,
                        'type': 'exact_match'
                    })
                elif len(source_line_clean) > 20 and source_line_clean in target_line_clean:
                    similar_blocks.append({
                        'source_line': i + 1,
                        'target_line': j + 1,
                        'content': source_line_clean[:100],
                        'similarity': 0.8,
                        'type': 'partial_match'
                    })
        
        return similar_blocks[:20]  # Limit to first 20 matches for performance
    
    def _generate_diff_lines(self, source_code: str, target_code: str) -> List[Dict[str, Any]]:
        """Generate line-by-line diff information."""
        source_lines = source_code.split('\n')
        target_lines = target_code.split('\n')
        
        diff_lines = []
        max_lines = min(len(source_lines), len(target_lines), 50)  # Limit for demo
        
        for i in range(max_lines):
            source_line = source_lines[i] if i < len(source_lines) else ""
            target_line = target_lines[i] if i < len(target_lines) else ""
            
            if source_line.strip() == target_line.strip():
                diff_type = "identical"
            elif source_line.strip() in target_line.strip() or target_line.strip() in source_line.strip():
                diff_type = "similar"
            else:
                diff_type = "different"
            
            diff_lines.append({
                'line_number': i + 1,
                'source_content': source_line[:100],  # Truncate for display
                'target_content': target_line[:100],
                'diff_type': diff_type
            })
        
        return diff_lines
    
    def _get_winnowing_details(self, source_code: str, target_code: str) -> Dict[str, Any]:
        """Get winnowing algorithm details if available."""
        try:
            if not SIMILARITY_ALGORITHMS_AVAILABLE:
                return None
            
            # This would use the actual winnowing algorithm from similarity_checker
            # For now, return mock winnowing details
            return {
                'k_value': 5,  # Minimum match length
                'w_value': 4,  # Window size
                'source_fingerprints': 45,  # Mock values
                'target_fingerprints': 52,
                'matching_fingerprints': 18,
                'fingerprint_similarity': 0.78
            }
        except Exception as e:
            logger.warning(f"Could not get winnowing details: {e}")
            return None
    
    def _count_similar_lines(self, source_code: str, target_code: str) -> int:
        """Count the number of similar lines between source and target."""
        source_lines = set(line.strip() for line in source_code.split('\n') if line.strip())
        target_lines = set(line.strip() for line in target_code.split('\n') if line.strip())
        return len(source_lines.intersection(target_lines))
    
    def _get_or_generate_code(self, repo: Dict[str, Any]) -> str:
        """Get real code from downloaded repos or generate mock code for repository."""
        repo_id = repo.get('id')
        repo_name = repo.get('name', '')
        
        print(f"DEBUG: Getting code for repo: {repo_name} (ID: {repo_id})")
        
        # First try to get real code from downloaded repositories
        real_code = self._get_real_code_from_downloaded_repo(repo_name)
        if real_code:
            print(f"DEBUG: Using real code from {repo_name} - Length: {len(real_code)} chars")
            print(f"DEBUG: First 100 chars: {real_code[:100]}...")
            return real_code
        else:
            print(f"DEBUG: Real code not found for {repo_name}, using mock code")
        
        # Fall back to cached/generated mock code
        if repo_id not in self.mock_code_cache:
            print(f"DEBUG: Generating new mock code for {repo_id}")
            self.mock_code_cache[repo_id] = self.generate_mock_code(repo)
        else:
            print(f"DEBUG: Using cached mock code for {repo_id}")
        
        mock_code = self.mock_code_cache[repo_id]
        print(f"DEBUG: Mock code length: {len(mock_code)} chars")
        return mock_code
    
    def get_available_algorithms(self) -> List[Dict[str, str]]:
        """Get list of available similarity algorithms."""
        if SIMILARITY_ALGORITHMS_AVAILABLE:
            return [
                {
                    'id': 'jaccard',
                    'name': 'Jaccard Similarity (Winnowing)',
                    'description': 'Uses winnowing algorithm with Jaccard similarity from existing codebase'
                }
            ]
        else:
            return [
                {
                    'id': 'jaccard',
                    'name': 'Jaccard Similarity (Demo)',
                    'description': 'Demo implementation of Jaccard similarity'
                },
                {
                    'id': 'cosine',
                    'name': 'Cosine Similarity (Demo)',
                    'description': 'Demo implementation of cosine similarity'
                },
                {
                    'id': 'levenshtein',
                    'name': 'Levenshtein Distance (Demo)',
                    'description': 'Demo implementation of edit distance'
                }
            ]
    
    def compare_repositories(self, source_repo=None, target_repo=None, algorithm: str = 'jaccard', repo_id1: str = None, repo_id2: str = None) -> Dict[str, Any]:
        """Compare two repositories using the specified algorithm.
        
        Args:
            source_repo: Dictionary containing source repo metadata (with 'name' key)
            target_repo: Dictionary containing target repo metadata (with 'name' key)
            algorithm: Algorithm to use for comparison
            repo_id1: Alternative way to specify first repository by ID
            repo_id2: Alternative way to specify second repository by ID
        """
        import time
        start_time = time.time()
        
        # Support both parameter styles
        if source_repo and target_repo:
            repo_name1 = source_repo.get('name', source_repo.get('id', str(source_repo)))
            repo_name2 = target_repo.get('name', target_repo.get('id', str(target_repo)))
        elif repo_id1 and repo_id2:
            repo_name1 = repo_id1
            repo_name2 = repo_id2
        else:
            return {
                'similarity_score': 0.0,
                'algorithm_used': algorithm,
                'processing_time': time.time() - start_time,
                'error': 'Invalid parameters - provide either (source_repo, target_repo) or (repo_id1, repo_id2)',
                'details': {}
            }
        
        # Get repository codes - create repo objects for _get_or_generate_code
        repo1_obj = {'name': repo_name1, 'id': repo_name1, 'language': 'auto-detect'}
        repo2_obj = {'name': repo_name2, 'id': repo_name2, 'language': 'auto-detect'}
        
        code1 = self._get_or_generate_code(repo1_obj)
        code2 = self._get_or_generate_code(repo2_obj)
        
        if not code1 or not code2:
            return {
                'similarity_score': 0.0,
                'algorithm_used': algorithm,
                'processing_time': time.time() - start_time,
                'error': 'Failed to retrieve code for one or both repositories',
                'details': {
                    'repo1_available': bool(code1),
                    'repo2_available': bool(code2),
                    'repo1_name': repo_name1,
                    'repo2_name': repo_name2
                }
            }
        
        # Calculate similarity
        if algorithm == 'jaccard' and SIMILARITY_ALGORITHMS_AVAILABLE:
            similarity_score = self._calculate_jaccard_similarity(code1, code2)
        elif algorithm in self.algorithms:
            similarity_score = self.algorithms[algorithm].calculate_similarity(code1, code2)
        else:
            # Fallback to simple similarity
            similarity_score = self._fallback_similarity_calculation(code1, code2)
        
        processing_time = time.time() - start_time
        
        # Record the analysis
        analysis_record = {
            'timestamp': datetime.now().isoformat(),
            'repo1': repo_name1,
            'repo2': repo_name2,
            'algorithm': algorithm,
            'similarity_score': similarity_score,
            'processing_time': processing_time,
            'code1_length': len(code1),
            'code2_length': len(code2)
        }
        
        self.analysis_history.append(analysis_record)
        
        return {
            'similarity_score': similarity_score,
            'algorithm_used': algorithm,
            'processing_time': processing_time,
            'details': {
                'repo1': repo_name1,
                'repo2': repo_name2,
                'code1_length': len(code1),
                'code2_length': len(code2),
                'timestamp': analysis_record['timestamp']
            }
        }
    
    def get_analysis_history(self) -> List[Dict[str, Any]]:
        """Get history of analyses performed in this session."""
        return self.analysis_history.copy()
    
    def clear_cache(self):
        """Clear the mock code cache."""
        self.mock_code_cache.clear()
        logger.info("Cleared mock code cache")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache state."""
        return {
            'cached_repositories': len(self.mock_code_cache),
            'total_analyses': len(self.analysis_history),
            'cache_size_bytes': sum(len(code) for code in self.mock_code_cache.values())
        }


# Global demo similarity analyzer instance
_demo_analyzer = None

def get_demo_analyzer() -> DemoSimilarityAnalyzer:
    """Get the global demo similarity analyzer instance."""
    global _demo_analyzer
    if _demo_analyzer is None:
        _demo_analyzer = DemoSimilarityAnalyzer()
    return _demo_analyzer
