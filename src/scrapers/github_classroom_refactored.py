"""
GitHub Classroom Main Interface
Simplified wrapper that coordinates all classroom operations
"""
from typing import List, Dict, Any, Optional, Tuple
from .github_auth import GitHubAuth
from .classroom_api import ClassroomAPI
from .assignment_manager import AssignmentManager
from .folder_organizer import FolderOrganizer
from .repository_downloader import RepositoryDownloader


class GitHubClassroom:
    """
    Main interface for GitHub Classroom operations
    Coordinates authentication, API calls, and file downloads
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub Classroom interface
        
        Args:
            github_token: GitHub personal access token
        """
        # Initialize core components
        self.auth = GitHubAuth(github_token)
        self.classroom_api = ClassroomAPI(self.auth)
        self.assignment_manager = AssignmentManager(self.auth, self.classroom_api)
        self.folder_organizer = FolderOrganizer(self.assignment_manager, self.classroom_api)
        self.repository_downloader = RepositoryDownloader(
            self.auth, self.assignment_manager, self.folder_organizer
        )
        
        # Legacy compatibility
        self.github_token = self.auth.github_token
        self.base_headers = self.auth.base_headers
        self.api_base = self.auth.api_base
    
    # ===== Core API Methods =====
    
    def get_classrooms(self) -> List[Dict[str, Any]]:
        """Get list of accessible classrooms"""
        return self.classroom_api.get_classrooms()
    
    def extract_classroom_id(self, classroom_url: str) -> Optional[int]:
        """Extract classroom ID from URL"""
        return self.classroom_api.extract_classroom_id(classroom_url)
    
    def get_classroom_details(self, classroom_id: int) -> Optional[Dict[str, Any]]:
        """Get classroom details by ID"""
        return self.classroom_api.get_classroom_details(classroom_id)
    
    def get_classroom_assignments(self, classroom_id: int) -> List[Dict[str, Any]]:
        """Get assignments for a classroom"""
        return self.assignment_manager.get_classroom_assignments(classroom_id)
    
    def get_assignment_details(self, assignment_id: int) -> Optional[Dict[str, Any]]:
        """Get assignment details by ID"""
        return self.assignment_manager.get_assignment_details(assignment_id)
    
    def get_accepted_assignments(self, assignment_id: int, page: int = 1, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get accepted assignments (student repositories)"""
        return self.assignment_manager.get_accepted_assignments(assignment_id, page, per_page)
    
    def get_assignment_grades(self, assignment_id: int) -> Optional[Dict[str, Any]]:
        """Get assignment grades"""
        return self.assignment_manager.get_assignment_grades(assignment_id)
    
    # ===== Download Operations =====
    
    def download_classroom_assignment_repos(
        self, 
        assignment_id: int, 
        save_dir: str, 
        allowed_extensions: Optional[Tuple[str, ...]] = None
    ) -> List[str]:
        """
        Download all student repositories for a specific assignment
        
        Args:
            assignment_id: Assignment ID
            save_dir: Directory to save files
            allowed_extensions: Allowed file extensions
            
        Returns:
            List of downloaded file paths
        """
        return self.repository_downloader.download_classroom_assignment_repos(
            assignment_id, save_dir, allowed_extensions
        )
    
    def preview_assignment_repositories(self, assignment_id: int) -> Dict[str, Any]:
        """Preview repositories without downloading"""
        return self.repository_downloader.preview_assignment_repositories(assignment_id)
    
    # ===== Folder Management =====
    
    def get_folder_structure_info(self, base_dir: str) -> Dict[str, Any]:
        """Get information about folder structure"""
        return self.folder_organizer.get_folder_structure_info(base_dir)
    
    # ===== Legacy Compatibility Methods =====
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Legacy method for backward compatibility"""
        return self.auth.make_request(endpoint, params)
    
    def _create_organized_save_dir(self, base_save_dir: str, assignment_id: int) -> str:
        """Legacy method for backward compatibility"""
        return self.folder_organizer.create_organized_save_dir(base_save_dir, assignment_id)
    
    # ===== Utility Methods =====
    
    def is_authenticated(self) -> bool:
        """Check if GitHub authentication is valid"""
        return self.auth.is_authenticated()
    
    def get_rate_limit_info(self) -> Optional[Dict[str, Any]]:
        """Get GitHub API rate limit information"""
        return self.auth.make_request('rate_limit')
    
    def validate_setup(self) -> Dict[str, Any]:
        """
        Validate the setup and return status information
        
        Returns:
            Dictionary with validation results
        """
        validation = {
            'authenticated': False,
            'token_valid': False,
            'api_accessible': False,
            'classrooms_accessible': False,
            'rate_limit': None,
            'errors': []
        }
        
        try:
            # Check authentication
            if self.auth.github_token:
                validation['authenticated'] = True
                
                # Test API access
                user_info = self.auth.make_request('user')
                if user_info:
                    validation['token_valid'] = True
                    validation['api_accessible'] = True
                    
                    # Test classroom access
                    classrooms = self.get_classrooms()
                    validation['classrooms_accessible'] = True
                    
                    # Get rate limit info
                    validation['rate_limit'] = self.get_rate_limit_info()
                    
                else:
                    validation['errors'].append('Invalid GitHub token or API not accessible')
            else:
                validation['errors'].append('No GitHub token provided')
                
        except Exception as e:
            validation['errors'].append(f'Setup validation error: {e}')
        
        return validation
