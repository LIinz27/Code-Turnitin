#!/usr/bin/env python3
"""
Demo Handler for Code Turnitin Thesis Presentation

This module handles demo operations including repository loading,
data management, and coordination between demo components.

Author: Created for Code Turnitin thesis presentation
Date: September 2025
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DemoHandler:
    """Main handler for demo operations and data management."""
    
    def __init__(self, demo_data_path: Optional[str] = None):
        """Initialize the demo handler."""
        self.base_dir = Path(__file__).parent.parent.parent
        self.demo_data_path = demo_data_path or str(self.base_dir / "data" / "demo" / "demo_repositories.json")
        self.demo_data = None
        self.cached_repositories = {}
        self.session_stats = {
            'started_at': datetime.now(),
            'analyses_performed': 0,
            'repositories_compared': set(),
            'languages_used': set()
        }
        
    def load_demo_data(self) -> bool:
        """Load the demo dataset from file."""
        try:
            logger.info(f"Loading demo data from {self.demo_data_path}")
            with open(self.demo_data_path, 'r', encoding='utf-8') as f:
                self.demo_data = json.load(f)
            
            # Cache repositories by language for faster access
            self._cache_repositories()
            
            logger.info(f"Successfully loaded demo data with {self.get_total_repositories()} repositories")
            return True
            
        except FileNotFoundError:
            logger.error(f"Demo data file not found: {self.demo_data_path}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in demo data file: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error loading demo data: {e}")
            return False
    
    def _cache_repositories(self):
        """Cache repositories for efficient access."""
        if not self.demo_data:
            return
            
        self.cached_repositories = {}
        for language, repos in self.demo_data['repositories'].items():
            self.cached_repositories[language] = {
                repo['id']: repo for repo in repos
            }
    
    def get_available_languages(self) -> List[str]:
        """Get list of available programming languages."""
        if not self.demo_data:
            return []
        return list(self.demo_data['repositories'].keys())
    
    def get_repositories_by_language(self, language: str) -> List[Dict[str, Any]]:
        """Get all repositories for a specific language."""
        if not self.demo_data or language not in self.demo_data['repositories']:
            return []
        return self.demo_data['repositories'][language]
    
    def get_all_repositories(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all repositories from all languages."""
        if not self.demo_data:
            return {}
        return self.demo_data['repositories']
    
    def get_repository_by_id(self, repo_id, language: str = None) -> Optional[Dict[str, Any]]:
        """Get a specific repository by ID (handles both string and int IDs)."""
        if not self.cached_repositories:
            return None
        
        # Try to convert repo_id to int if it's a string containing only digits
        search_ids = [repo_id]
        if isinstance(repo_id, str) and repo_id.isdigit():
            search_ids.append(int(repo_id))
        elif isinstance(repo_id, int):
            search_ids.append(str(repo_id))
            
        if language and language in self.cached_repositories:
            for search_id in search_ids:
                if search_id in self.cached_repositories[language]:
                    return self.cached_repositories[language][search_id]
        
        # Search across all languages if language not specified
        for lang_repos in self.cached_repositories.values():
            for search_id in search_ids:
                if search_id in lang_repos:
                    return lang_repos[search_id]
        
        return None
    
    def get_repository_summary(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of repository information for display."""
        return {
            'id': repo.get('id'),
            'name': repo.get('name'),
            'full_name': repo.get('full_name'),
            'language': repo.get('language'),
            'description': repo.get('description', 'No description available'),
            'size_kb': repo.get('size', 0),
            'size_display': self._format_size(repo.get('size', 0)),
            'created_at': repo.get('created_at'),
            'updated_at': repo.get('updated_at'),
            'estimated_files': repo.get('estimated_files', 1),
            'analysis_priority': repo.get('analysis_priority', 'medium'),
            'demo_category': repo.get('demo_category', 'primary')
        }
    
    def _format_size(self, size_kb: int) -> str:
        """Format repository size for display."""
        if size_kb < 1:
            return "< 1 KB"
        elif size_kb < 1024:
            return f"{size_kb} KB"
        else:
            return f"{size_kb / 1024:.1f} MB"
    
    def get_comparison_candidates(self, source_repo: Dict[str, Any], 
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """Get suitable repositories for comparison with the source repository."""
        source_language = source_repo.get('language')
        source_id = source_repo.get('id')
        
        if not source_language:
            return []
        
        candidates = []
        same_language_repos = self.get_repositories_by_language(source_language)
        
        # Exclude the source repository itself
        filtered_repos = [repo for repo in same_language_repos if repo.get('id') != source_id]
        
        # Sort by analysis priority and size for better comparison candidates
        sorted_repos = sorted(filtered_repos, key=lambda x: (
            x.get('analysis_priority') == 'high',  # High priority first
            x.get('size', 0)  # Then by size
        ), reverse=True)
        
        for repo in sorted_repos[:limit]:
            candidates.append(self.get_repository_summary(repo))
        
        return candidates
    
    def record_analysis(self, source_repo_id: int, target_repo_id: int, 
                       language: str, similarity_score: float):
        """Record an analysis operation for session statistics."""
        self.session_stats['analyses_performed'] += 1
        self.session_stats['repositories_compared'].add(source_repo_id)
        self.session_stats['repositories_compared'].add(target_repo_id)
        self.session_stats['languages_used'].add(language)
        
        logger.info(f"Recorded analysis: {source_repo_id} vs {target_repo_id} ({language}) = {similarity_score:.2f}")
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get current session statistics."""
        uptime = datetime.now() - self.session_stats['started_at']
        
        return {
            'session_started': self.session_stats['started_at'].isoformat(),
            'session_uptime': str(uptime).split('.')[0],  # Remove microseconds
            'analyses_performed': self.session_stats['analyses_performed'],
            'unique_repositories': len(self.session_stats['repositories_compared']),
            'languages_used': list(self.session_stats['languages_used']),
            'total_available_repos': self.get_total_repositories(),
            'available_languages': self.get_available_languages()
        }
    
    def get_total_repositories(self) -> int:
        """Get total number of repositories in the demo dataset."""
        if not self.demo_data:
            return 0
        
        total = 0
        for repos in self.demo_data['repositories'].values():
            total += len(repos)
        return total
    
    def get_demo_metadata(self) -> Dict[str, Any]:
        """Get metadata about the demo dataset."""
        if not self.demo_data:
            return {}
        return self.demo_data.get('metadata', {})
    
    def get_language_statistics(self) -> Dict[str, Any]:
        """Get statistics for each language in the demo dataset."""
        if not self.demo_data:
            return {}
        return self.demo_data.get('statistics', {})
    
    def search_repositories(self, query: str, language: str = None) -> List[Dict[str, Any]]:
        """Search repositories by name or description."""
        if not self.demo_data:
            return []
        
        query = query.lower()
        results = []
        
        # Determine which languages to search
        languages_to_search = [language] if language else self.get_available_languages()
        
        for lang in languages_to_search:
            repos = self.get_repositories_by_language(lang)
            for repo in repos:
                # Search in name and description
                name_match = query in repo.get('name', '').lower()
                desc_match = query in repo.get('description', '').lower()
                
                if name_match or desc_match:
                    repo_summary = self.get_repository_summary(repo)
                    repo_summary['match_reason'] = []
                    
                    if name_match:
                        repo_summary['match_reason'].append('name')
                    if desc_match:
                        repo_summary['match_reason'].append('description')
                    
                    results.append(repo_summary)
        
        # Sort by relevance (name matches first, then by size)
        results.sort(key=lambda x: (
            'name' not in x['match_reason'],  # Name matches first
            -x['size_kb']  # Then by size descending
        ))
        
        return results
    
    def get_sample_repositories(self, count: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Get sample repositories from each language for quick demo."""
        samples = {}
        
        for language in self.get_available_languages():
            repos = self.get_repositories_by_language(language)
            
            # Select diverse samples (different sizes)
            if len(repos) <= count:
                selected = repos
            else:
                # Sort by size and pick spread across range
                sorted_repos = sorted(repos, key=lambda x: x.get('size', 0))
                step = len(sorted_repos) // count
                selected = [sorted_repos[i * step] for i in range(count)]
                
                # Ensure we don't miss the largest
                if sorted_repos[-1] not in selected:
                    selected[-1] = sorted_repos[-1]
            
            samples[language] = [self.get_repository_summary(repo) for repo in selected]
        
        return samples
    
    def validate_demo_setup(self) -> Tuple[bool, List[str]]:
        """Validate that the demo is properly set up."""
        issues = []
        
        # Check if demo data is loaded
        if not self.demo_data:
            if not self.load_demo_data():
                issues.append("Failed to load demo data")
                return False, issues
        
        # Check data structure - be more flexible for our focused demo
        required_keys = ['metadata', 'repositories']
        for key in required_keys:
            if key not in self.demo_data:
                issues.append(f"Missing required key in demo data: {key}")
        
        # For focused demo (like our prediksi telur ayam), check if we have enough repos in ANY language
        available_languages = self.get_available_languages()
        if not available_languages:
            issues.append("No programming languages found in demo data")
            return False, issues
        
        # Check if we have at least one language with enough repositories for meaningful demo
        has_sufficient_repos = False
        for lang in available_languages:
            repos = self.get_repositories_by_language(lang)
            if repos and len(repos) >= 5:
                has_sufficient_repos = True
                logger.info(f"Found {len(repos)} {lang} repositories for demo")
                if len(repos) < 15:
                    issues.append(f"Limited {lang} repositories ({len(repos)}) - more would improve demo variety")
                break
        
        if not has_sufficient_repos:
            issues.append("No programming language has sufficient repositories (minimum 5) for meaningful similarity comparison")
            return False, issues
        
        # Check total repository count (warning only, not blocking)
        total_repos = self.get_total_repositories()
        if total_repos < 10:
            issues.append(f"Very low total repository count ({total_repos}) - recommend at least 10")
        elif total_repos < 20:
            issues.append(f"Limited repository count ({total_repos}) - recommend at least 20 for better variety")
        
        # Consider it successful if we have critical requirements met
        critical_issues = [i for i in issues if 'Failed to load' in i or 'Missing required key' in i or 'No programming languages' in i or 'No programming language has sufficient' in i]
        success = len(critical_issues) == 0
        
        if success:
            logger.info("Demo setup validation passed")
            if issues:
                logger.info(f"Demo validation passed with {len(issues)} non-critical warnings")
        else:
            logger.error(f"Demo setup validation failed with {len(critical_issues)} critical issues")
        
        return success, issues


# Global demo handler instance for use across the application
_demo_handler = None

def get_demo_handler() -> DemoHandler:
    """Get the global demo handler instance."""
    global _demo_handler
    if _demo_handler is None:
        _demo_handler = DemoHandler()
        _demo_handler.load_demo_data()
    return _demo_handler

def initialize_demo() -> Tuple[bool, List[str]]:
    """Initialize the demo system and return setup status."""
    handler = get_demo_handler()
    return handler.validate_demo_setup()
