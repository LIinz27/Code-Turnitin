#!/usr/bin/env python3
"""
Demo Data Extractor for Code Turnitin Thesis Presentation

This module extracts a curated subset of repositories from the Lab-IF dataset
for use in thesis presentation demos. It selects repositories based on primary
programming languages and ensures balanced representation.

Author: Created for Code Turnitin thesis presentation
Date: September 2025
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DemoDataExtractor:
    """Extract and prepare demo dataset from Lab-IF repository analysis."""
    
    def __init__(self, source_file: str, output_file: str):
        self.source_file = Path(source_file)
        self.output_file = Path(output_file)
        self.target_languages = ['Java', 'JavaScript', 'Python']
        self.repos_per_language = 20
        
    def load_source_data(self) -> List[Dict[str, Any]]:
        """Load the original Lab-IF dataset."""
        logger.info(f"Loading source data from {self.source_file}")
        
        with open(self.source_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded {len(data)} repositories from source dataset")
        return data
    
    def filter_by_language(self, repositories: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
        """Filter repositories by primary programming language."""
        filtered = []
        
        for repo in repositories:
            # Basic language and name check
            if (repo.get('language') == language and 
                repo.get('name')):
                
                # Different criteria for each language based on availability
                if language == 'Java':
                    # More permissive for Java (include smaller repos)
                    if repo.get('size', 0) > 1:
                        filtered.append(repo)
                elif language == 'JavaScript':
                    # Standard criteria for JavaScript
                    if (repo.get('size', 0) > 10 and
                        not repo.get('fork', False) and
                        'test' not in repo.get('name', '').lower() and
                        'example' not in repo.get('name', '').lower()):
                        filtered.append(repo)
                elif language == 'Python':
                    # Standard criteria for Python
                    if (repo.get('size', 0) > 10 and
                        not repo.get('fork', False) and
                        'test' not in repo.get('name', '').lower() and
                        'example' not in repo.get('name', '').lower()):
                        filtered.append(repo)
        
        logger.info(f"Found {len(filtered)} {language} repositories")
        return filtered
    
    def select_representative_repos(self, repositories: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
        """Select representative repositories ensuring diversity."""
        if len(repositories) <= count:
            return repositories
        
        # Sort by various criteria to ensure diversity
        # 1. Size diversity (small, medium, large projects)
        sorted_by_size = sorted(repositories, key=lambda x: x.get('size', 0))
        
        # 2. Activity diversity (different update dates)
        sorted_by_activity = sorted(repositories, key=lambda x: x.get('updated_at', ''))
        
        # 3. Name diversity (different naming patterns)
        sorted_by_name = sorted(repositories, key=lambda x: x.get('name', ''))
        
        selected = []
        used_indices = set()
        
        # Select from each category to ensure diversity
        categories = [sorted_by_size, sorted_by_activity, sorted_by_name]
        repos_per_category = count // len(categories)
        remainder = count % len(categories)
        
        for i, category in enumerate(categories):
            category_count = repos_per_category + (1 if i < remainder else 0)
            step = max(1, len(category) // max(1, category_count))
            
            for j in range(0, len(category), step):
                if len(selected) >= count:
                    break
                    
                original_index = repositories.index(category[j])
                if original_index not in used_indices:
                    selected.append(category[j])
                    used_indices.add(original_index)
                    
                    if len(selected) >= count:
                        break
        
        # Fill remaining slots randomly if needed
        while len(selected) < count and len(used_indices) < len(repositories):
            remaining = [repo for i, repo in enumerate(repositories) if i not in used_indices]
            if remaining:
                random_repo = random.choice(remaining)
                selected.append(random_repo)
                used_indices.add(repositories.index(random_repo))
        
        return selected[:count]
    
    def create_demo_entry(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        """Create a demo-friendly entry from repository data."""
        return {
            'id': repo.get('id'),
            'name': repo.get('name'),
            'full_name': repo.get('full_name'),
            'description': repo.get('description', 'No description provided'),
            'language': repo.get('language'),
            'size': repo.get('size', 0),
            'created_at': repo.get('created_at'),
            'updated_at': repo.get('updated_at'),
            'html_url': repo.get('html_url'),
            'clone_url': repo.get('clone_url'),
            'default_branch': repo.get('default_branch', 'main'),
            'topics': repo.get('topics', []),
            # Demo-specific metadata
            'demo_category': 'primary',
            'analysis_priority': 'high' if repo.get('size', 0) > 100 else 'medium',
            'estimated_files': max(1, repo.get('size', 0) // 10),  # Rough estimation
        }
    
    def generate_demo_dataset(self) -> Dict[str, Any]:
        """Generate the complete demo dataset."""
        logger.info("Starting demo dataset generation...")
        
        # Load source data
        all_repositories = self.load_source_data()
        
        demo_data = {
            'metadata': {
                'source': 'Lab-IF Repository Analysis',
                'source_date': '2025-09-10',
                'demo_created': '2025-09-12',
                'total_source_repos': len(all_repositories),
                'target_languages': self.target_languages,
                'repos_per_language': self.repos_per_language,
                'selection_criteria': [
                    'Non-fork repositories',
                    'Minimum 10KB size',
                    'Excludes test/demo/tutorial repos',
                    'Diverse size and activity patterns'
                ]
            },
            'repositories': {},
            'statistics': {}
        }
        
        # Extract repositories for each language
        total_selected = 0
        for language in self.target_languages:
            logger.info(f"Processing {language} repositories...")
            
            # Filter by language
            language_repos = self.filter_by_language(all_repositories, language)
            
            # Select representative subset
            selected_repos = self.select_representative_repos(language_repos, self.repos_per_language)
            
            # Convert to demo format
            demo_repos = [self.create_demo_entry(repo) for repo in selected_repos]
            
            # Store in dataset
            demo_data['repositories'][language] = demo_repos
            demo_data['statistics'][language] = {
                'available_repos': len(language_repos),
                'selected_repos': len(demo_repos),
                'avg_size': sum(repo['size'] for repo in demo_repos) / len(demo_repos) if demo_repos else 0,
                'size_range': {
                    'min': min(repo['size'] for repo in demo_repos) if demo_repos else 0,
                    'max': max(repo['size'] for repo in demo_repos) if demo_repos else 0
                }
            }
            
            total_selected += len(demo_repos)
            logger.info(f"Selected {len(demo_repos)} {language} repositories")
        
        # Add overall statistics
        demo_data['statistics']['overall'] = {
            'total_demo_repos': total_selected,
            'coverage_percentage': (total_selected / len(all_repositories)) * 100,
            'languages_covered': len(self.target_languages)
        }
        
        logger.info(f"Demo dataset generated with {total_selected} repositories")
        return demo_data
    
    def save_demo_dataset(self, demo_data: Dict[str, Any]):
        """Save the demo dataset to file."""
        logger.info(f"Saving demo dataset to {self.output_file}")
        
        # Ensure output directory exists
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save with pretty formatting for readability
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(demo_data, f, indent=2, ensure_ascii=False)
        
        logger.info("Demo dataset saved successfully")
    
    def print_summary(self, demo_data: Dict[str, Any]):
        """Print a summary of the generated demo dataset."""
        print("\n" + "="*60)
        print("DEMO DATASET GENERATION SUMMARY")
        print("="*60)
        
        metadata = demo_data['metadata']
        statistics = demo_data['statistics']
        
        print(f"Source: {metadata['source']}")
        print(f"Total Source Repositories: {metadata['total_source_repos']:,}")
        print(f"Demo Creation Date: {metadata['demo_created']}")
        
        print("\nLanguage Distribution:")
        for lang in self.target_languages:
            stats = statistics[lang]
            print(f"  {lang:>12}: {stats['selected_repos']:>2} repos (from {stats['available_repos']:>4} available)")
            print(f"               Avg Size: {stats['avg_size']:>7.1f} KB")
            print(f"               Range: {stats['size_range']['min']:>4}-{stats['size_range']['max']:>5} KB")
        
        overall = statistics['overall']
        print(f"\nOverall Statistics:")
        print(f"  Total Demo Repos: {overall['total_demo_repos']}")
        print(f"  Coverage: {overall['coverage_percentage']:.2f}% of source dataset")
        print(f"  Languages: {overall['languages_covered']}")
        
        print("\n" + "="*60)
        print("Ready for Phase 2: Demo Backend Implementation")
        print("="*60)


def main():
    """Main execution function for demo data extraction."""
    # Set up file paths
    base_dir = Path(__file__).parent.parent.parent
    source_file = base_dir / "tests" / "repo_analysis_Lab-IF_20250910_141914.json"
    output_file = base_dir / "data" / "demo" / "demo_repositories.json"
    
    # Create extractor and generate dataset
    extractor = DemoDataExtractor(str(source_file), str(output_file))
    
    try:
        # Generate demo dataset
        demo_data = extractor.generate_demo_dataset()
        
        # Save to file
        extractor.save_demo_dataset(demo_data)
        
        # Print summary
        extractor.print_summary(demo_data)
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating demo dataset: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
