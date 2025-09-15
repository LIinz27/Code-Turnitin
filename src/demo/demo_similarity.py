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
        """Calculate Jaccard similarity using existing winnowing algorithm."""
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
            
            # Import additional functions needed
            from algorithms.similarity_checker import preprocess_code, generate_k_grams, hash_k_gram_optimized
            
            # Follow the existing workflow
            k = 5  # k-gram size
            w = 10  # window size
            
            # Step 1: Preprocess code
            tokens_a, lines_a = preprocess_code(temp_file1, None)
            tokens_b, lines_b = preprocess_code(temp_file2, None)
            
            if not tokens_a or not tokens_b:
                # Clean up and return fallback
                os.unlink(temp_file1)
                os.unlink(temp_file2)
                return self._fallback_similarity_calculation(code1, code2)
            
            # Step 2: Generate k-grams
            k_grams_a = generate_k_grams(tokens_a, k)
            k_grams_b = generate_k_grams(tokens_b, k)
            
            if not k_grams_a or not k_grams_b:
                # Clean up and return fallback
                os.unlink(temp_file1)
                os.unlink(temp_file2)
                return self._fallback_similarity_calculation(code1, code2)
            
            # Step 3: Hash k-grams
            hashed_k_grams_a = []
            for k_gram_tuple, start_line, end_line in k_grams_a:
                hash_val = hash_k_gram_optimized(k_gram_tuple)
                hashed_k_grams_a.append((hash_val, (k_gram_tuple, start_line, end_line), (start_line, end_line)))
            
            hashed_k_grams_b = []
            for k_gram_tuple, start_line, end_line in k_grams_b:
                hash_val = hash_k_gram_optimized(k_gram_tuple)
                hashed_k_grams_b.append((hash_val, (k_gram_tuple, start_line, end_line), (start_line, end_line)))
            
            # Step 4: Apply winnowing
            fingerprints_a = winnowing(hashed_k_grams_a, w)
            fingerprints_b = winnowing(hashed_k_grams_b, w)
            
            # Step 5: Calculate Jaccard similarity
            similarity_score, intersection_count, union_count = calculate_jaccard_similarity(fingerprints_a, fingerprints_b)
            
            # Clean up temporary files
            os.unlink(temp_file1)
            os.unlink(temp_file2)
            
            return similarity_score
            
        except Exception as e:
            logger.warning(f"Error in Jaccard similarity calculation: {e}")
            # Clean up temporary files if they exist
            try:
                if 'temp_file1' in locals():
                    os.unlink(temp_file1)
                if 'temp_file2' in locals():
                    os.unlink(temp_file2)
            except:
                pass
            # Fallback to deterministic calculation
            return self._fallback_similarity_calculation(code1, code2)
    
    def _fallback_similarity_calculation(self, code1: str, code2: str) -> float:
        """Fallback similarity calculation when winnowing fails."""
        # Simple token-based similarity for demo purposes
        tokens1 = set(code1.split())
        tokens2 = set(code2.split())
        
        if not tokens1 and not tokens2:
            return 1.0
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0
    
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
