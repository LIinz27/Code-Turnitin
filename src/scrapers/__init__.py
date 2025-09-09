# Scrapers package - Contains GitHub and web scraping functionality

# Main interfaces
from .github_classroom_refactored import GitHubClassroom
from .github_scraper import scrape_repo_files

# Modular components (for advanced usage)
from .github_auth import GitHubAuth
from .classroom_api import ClassroomAPI
from .assignment_manager import AssignmentManager
from .folder_organizer import FolderOrganizer
from .repository_downloader import RepositoryDownloader

__all__ = [
    'GitHubClassroom',
    'scrape_repo_files',
    'GitHubAuth',
    'ClassroomAPI',
    'AssignmentManager',
    'FolderOrganizer',
    'RepositoryDownloader'
]
