"""
Demo Package for Code Turnitin Thesis Presentation

This package contains modules for implementing a local demo system
that showcases plagiarism detection capabilities using curated
repository data instead of live GitHub API calls.

Modules:
- demo_data_extractor: Extract and prepare demo dataset
- demo_handler: Main demo logic and operations
- demo_similarity: Local similarity analysis for demo
"""

__version__ = "1.0.0"
__author__ = "Code Turnitin Demo System"

from .demo_data_extractor import DemoDataExtractor
from .demo_handler import DemoHandler, get_demo_handler, initialize_demo
from .demo_similarity import DemoSimilarityAnalyzer, get_demo_analyzer

__all__ = [
    'DemoDataExtractor', 
    'DemoHandler', 
    'get_demo_handler', 
    'initialize_demo',
    'DemoSimilarityAnalyzer', 
    'get_demo_analyzer'
]
