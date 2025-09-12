#!/usr/bin/env python3
"""
Repository Downloader for Code Turnitin Demo

This module downloads real repositories from GitHub for authentic
similarity analysis in thesis presentation.

Author: Created for Code Turnitin thesis presentation
Date: September 2025
"""

import os
import json
import subprocess
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RepositoryDownloader:
    """Downloads and manages real repositories for demo system."""
    
    def __init__(self, download_dir: Optional[str] = None):
        """Initialize the repository downloader."""
        self.base_dir = Path(__file__).parent.parent.parent
        self.download_dir = Path(download_dir) if download_dir else self.base_dir / "data" / "demo_repos"
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.demo_data_path = self.base_dir / "data" / "demo" / "demo_repositories.json"
        self.download_log_path = self.download_dir / "download_log.json"
        
        self.downloaded_repos = {}
        self.load_download_log()
        
    def load_download_log(self):
        """Load existing download log."""
        if self.download_log_path.exists():
            try:
                with open(self.download_log_path, 'r', encoding='utf-8') as f:
                    self.downloaded_repos = json.load(f)
                logger.info(f"Loaded download log with {len(self.downloaded_repos)} entries")
            except Exception as e:
                logger.warning(f"Could not load download log: {e}")
                self.downloaded_repos = {}
    
    def save_download_log(self):
        """Save download log to file."""
        try:
            with open(self.download_log_path, 'w', encoding='utf-8') as f:
                json.dump(self.downloaded_repos, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save download log: {e}")
    
    def select_template_repositories(self) -> Dict[str, List[Dict[str, Any]]]:
        """Select the best template repositories for download."""
        
        # Load demo data
        with open(self.demo_data_path, 'r', encoding='utf-8') as f:
            demo_data = json.load(f)
        
        selected_repos = {
            'Java': [],
            'JavaScript': [],
            'Python': []
        }
        
        # Selection criteria for each language
        selection_patterns = {
            'Java': [
                'lab-6-',     # Lab assignments (similar structure)
                'text-kucing-', # Text processing assignments
                'telur-ayam-',  # Prediction assignments
                'lab-5-'       # Another lab series
            ],
            'JavaScript': [
                'tugas-pemrograman-web-2-',  # Web programming assignments
                'final-web-lanjut-',         # Final web projects
                'tugas-web-'                 # Web assignments
            ],
            'Python': [
                'tugas-elasticsearch-',  # Elasticsearch assignments
                'tugas-elastic-',        # Elastic assignments
                'elasticsearch-'         # Elasticsearch projects
            ]
        }
        
        for language in demo_data['repositories']:
            repos = demo_data['repositories'][language]
            lang_selected = []
            
            # Get repositories matching patterns
            for pattern in selection_patterns.get(language, []):
                matching_repos = [r for r in repos if pattern in r['name']]
                
                # Sort by size (prefer medium-sized repos for analysis)
                matching_repos.sort(key=lambda x: abs(x.get('size', 0) - 20))  # Prefer ~20KB repos
                
                # Take up to 2-3 repos per pattern
                lang_selected.extend(matching_repos[:3])
            
            # Remove duplicates and limit total per language
            seen_ids = set()
            unique_repos = []
            for repo in lang_selected:
                if repo['id'] not in seen_ids:
                    unique_repos.append(repo)
                    seen_ids.add(repo['id'])
            
            selected_repos[language] = unique_repos[:8]  # Max 8 per language
        
        # Log selection summary
        total_selected = sum(len(repos) for repos in selected_repos.values())
        logger.info(f"Selected {total_selected} repositories for download:")
        for lang, repos in selected_repos.items():
            logger.info(f"  {lang}: {len(repos)} repositories")
            for repo in repos:
                logger.info(f"    - {repo['name']} ({repo['size']}KB)")
        
        return selected_repos
    
    def is_git_available(self) -> bool:
        """Check if git is available in the system."""
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def download_repository(self, repo: Dict[str, Any]) -> Tuple[bool, str]:
        """Download a single repository."""
        repo_id = repo['id']
        repo_name = repo['name']
        clone_url = repo.get('clone_url', '').replace('.git', '')
        
        if not clone_url:
            return False, "No clone URL available"
        
        # Check if already downloaded
        if str(repo_id) in self.downloaded_repos:
            existing_path = Path(self.downloaded_repos[str(repo_id)]['local_path'])
            if existing_path.exists():
                logger.info(f"Repository {repo_name} already downloaded")
                return True, str(existing_path)
        
        # Create local directory
        local_dir = self.download_dir / f"{repo_name}-{repo_id}"
        
        try:
            # Clone the repository
            logger.info(f"Downloading {repo_name} from {clone_url}")
            
            cmd = ['git', 'clone', f"{clone_url}.git", str(local_dir)]
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=60  # 60 second timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error(f"Failed to clone {repo_name}: {error_msg}")
                return False, f"Git clone failed: {error_msg}"
            
            # Verify download
            if not local_dir.exists() or not (local_dir / '.git').exists():
                return False, "Repository not properly cloned"
            
            # Record successful download
            self.downloaded_repos[str(repo_id)] = {
                'repo_name': repo_name,
                'clone_url': clone_url,
                'local_path': str(local_dir),
                'downloaded_at': time.time(),
                'language': repo.get('language'),
                'size_kb': repo.get('size', 0)
            }
            
            logger.info(f"Successfully downloaded {repo_name}")
            return True, str(local_dir)
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout downloading {repo_name}")
            # Clean up partial download
            if local_dir.exists():
                shutil.rmtree(local_dir, ignore_errors=True)
            return False, "Download timeout"
            
        except Exception as e:
            logger.error(f"Error downloading {repo_name}: {e}")
            # Clean up partial download
            if local_dir.exists():
                shutil.rmtree(local_dir, ignore_errors=True)
            return False, f"Download error: {str(e)}"
    
    def download_selected_repositories(self, max_per_language: int = 5) -> Dict[str, Any]:
        """Download selected repositories for demo."""
        
        if not self.is_git_available():
            logger.error("Git is not available. Please install Git first.")
            return {
                'success': False,
                'error': 'Git not available',
                'downloaded': {},
                'failed': {}
            }
        
        # Select repositories
        selected_repos = self.select_template_repositories()
        
        download_results = {
            'success': True,
            'downloaded': {},
            'failed': {},
            'summary': {
                'total_attempted': 0,
                'total_downloaded': 0,
                'total_failed': 0
            }
        }
        
        for language, repos in selected_repos.items():
            download_results['downloaded'][language] = []
            download_results['failed'][language] = []
            
            # Limit per language
            repos_to_download = repos[:max_per_language]
            
            for repo in repos_to_download:
                download_results['summary']['total_attempted'] += 1
                
                logger.info(f"Downloading {language} repository: {repo['name']}")
                success, path_or_error = self.download_repository(repo)
                
                if success:
                    download_results['downloaded'][language].append({
                        'repo': repo,
                        'local_path': path_or_error
                    })
                    download_results['summary']['total_downloaded'] += 1
                else:
                    download_results['failed'][language].append({
                        'repo': repo,
                        'error': path_or_error
                    })
                    download_results['summary']['total_failed'] += 1
                
                # Brief pause between downloads
                time.sleep(1)
        
        # Save download log
        self.save_download_log()
        
        # Summary
        logger.info("Download summary:")
        logger.info(f"  Total attempted: {download_results['summary']['total_attempted']}")
        logger.info(f"  Successfully downloaded: {download_results['summary']['total_downloaded']}")
        logger.info(f"  Failed: {download_results['summary']['total_failed']}")
        
        return download_results
    
    def get_downloaded_repositories(self) -> Dict[str, Any]:
        """Get information about downloaded repositories."""
        downloaded_info = {
            'total_count': len(self.downloaded_repos),
            'by_language': {},
            'repositories': []
        }
        
        # Group by language
        by_language = {}
        for repo_id, repo_info in self.downloaded_repos.items():
            language = repo_info.get('language', 'Unknown')
            if language not in by_language:
                by_language[language] = []
            by_language[language].append(repo_info)
        
        downloaded_info['by_language'] = by_language
        
        # Add repository details with file analysis
        for repo_id, repo_info in self.downloaded_repos.items():
            local_path = Path(repo_info['local_path'])
            
            repo_details = {
                'id': repo_id,
                'name': repo_info['repo_name'],
                'language': repo_info.get('language'),
                'local_path': str(local_path),
                'exists': local_path.exists(),
                'file_count': 0,
                'code_files': []
            }
            
            # Analyze files if repository exists
            if local_path.exists():
                repo_details.update(self._analyze_repository_files(local_path))
            
            downloaded_info['repositories'].append(repo_details)
        
        return downloaded_info
    
    def _analyze_repository_files(self, repo_path: Path) -> Dict[str, Any]:
        """Analyze files in a downloaded repository."""
        
        # Code file extensions
        code_extensions = {
            '.java': 'Java',
            '.js': 'JavaScript', 
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.py': 'Python',
            '.html': 'HTML',
            '.css': 'CSS',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C/C++',
            '.php': 'PHP'
        }
        
        code_files = []
        total_files = 0
        
        try:
            for file_path in repo_path.rglob('*'):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    total_files += 1
                    
                    # Check if it's a code file
                    if file_path.suffix.lower() in code_extensions:
                        try:
                            # Get file size and basic info
                            file_size = file_path.stat().st_size
                            relative_path = file_path.relative_to(repo_path)
                            
                            # Read first few lines to check if it's actually code
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                first_lines = f.read(1000)  # First 1000 chars
                            
                            code_files.append({
                                'path': str(relative_path),
                                'full_path': str(file_path),
                                'extension': file_path.suffix.lower(),
                                'language': code_extensions[file_path.suffix.lower()],
                                'size_bytes': file_size,
                                'preview': first_lines[:200] + '...' if len(first_lines) > 200 else first_lines
                            })
                            
                        except Exception as e:
                            logger.debug(f"Could not analyze file {file_path}: {e}")
                            
        except Exception as e:
            logger.error(f"Error analyzing repository {repo_path}: {e}")
        
        return {
            'file_count': total_files,
            'code_files': code_files,
            'code_file_count': len(code_files)
        }
    
    def cleanup_downloads(self):
        """Clean up all downloaded repositories."""
        if self.download_dir.exists():
            shutil.rmtree(self.download_dir)
            self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.downloaded_repos = {}
        self.save_download_log()
        logger.info("Cleaned up all downloaded repositories")


def main():
    """Main function to download demo repositories."""
    print("Repository Downloader for Code Turnitin Demo")
    print("=" * 50)
    
    downloader = RepositoryDownloader()
    
    # Check git availability
    if not downloader.is_git_available():
        print("❌ Git is not available. Please install Git first.")
        return False
    
    print("✅ Git is available")
    print("🔍 Selecting repositories for download...")
    
    # Download repositories
    results = downloader.download_selected_repositories(max_per_language=4)
    
    print("\n📊 Download Results:")
    print(f"✅ Successfully downloaded: {results['summary']['total_downloaded']}")
    print(f"❌ Failed downloads: {results['summary']['total_failed']}")
    
    if results['summary']['total_downloaded'] > 0:
        print("\n📁 Downloaded repositories by language:")
        for lang, repos in results['downloaded'].items():
            if repos:
                print(f"\n  {lang}:")
                for item in repos:
                    repo = item['repo']
                    print(f"    ✓ {repo['name']} ({repo['size']}KB)")
    
    if results['summary']['total_failed'] > 0:
        print("\n❌ Failed downloads:")
        for lang, failed in results['failed'].items():
            if failed:
                print(f"\n  {lang}:")
                for item in failed:
                    repo = item['repo']
                    print(f"    ✗ {repo['name']}: {item['error']}")
    
    return results['summary']['total_downloaded'] > 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
