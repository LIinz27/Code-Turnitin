"""
Assignment Management Operations
Handles assignment discovery, details, and student repository management
"""
from typing import List, Dict, Any, Optional
from .github_auth import GitHubAuth
from .classroom_api import ClassroomAPI


class AssignmentManager:
    """Manages GitHub Classroom assignments and student repositories"""
    
    def __init__(self, auth: GitHubAuth, classroom_api: ClassroomAPI):
        """
        Initialize assignment manager
        
        Args:
            auth: GitHub authentication instance
            classroom_api: Classroom API instance
        """
        self.auth = auth
        self.classroom_api = classroom_api
        
        # Assignment keywords for filtering
        self.assignment_keywords = [
            'tugas', 'assignment', 'project', 'lab', 'final', 
            'ujian', 'uts', 'uas', 'quiz', 'homework'
        ]
        
        # GitHub Classroom patterns
        self.classroom_patterns = ['created by GitHub Classroom', 'github classroom']
    
    def get_classroom_assignments(self, classroom_id: int) -> List[Dict[str, Any]]:
        """
        Get assignments for a classroom
        
        Args:
            classroom_id: Classroom ID
            
        Returns:
            List of assignment dictionaries
        """
        print(f"Mengambil daftar assignment untuk classroom {classroom_id}...")
        
        # Try direct API first
        assignments = self.auth.make_request(f'classrooms/{classroom_id}/assignments')
        
        if assignments and len(assignments) > 0:
            print(f"Found {len(assignments)} assignments via API")
            return assignments if isinstance(assignments, list) else [assignments]
        
        # Fallback to organization repositories
        print("API tidak mengembalikan assignments, mencoba dari organization repositories...")
        return self._get_assignments_from_org_repos(classroom_id)
    
    def _get_assignments_from_org_repos(self, classroom_id: int) -> List[Dict[str, Any]]:
        """
        Get assignments from organization repositories
        
        Args:
            classroom_id: Classroom ID
            
        Returns:
            List of assignment-like dictionaries
        """
        org_login = self.classroom_api.get_organization_from_classroom(classroom_id)
        if not org_login:
            print("Tidak bisa mendapatkan organization login")
            return []
        
        print(f"Mencari assignments di organization: {org_login}")
        
        # Get organization repositories
        org_repos = self.auth.make_request(f'orgs/{org_login}/repos', params={'per_page': 100})
        
        if not org_repos:
            print("Tidak bisa mendapatkan organization repositories")
            return []
        
        return self._filter_assignment_repositories(org_repos)
    
    def _filter_assignment_repositories(self, repositories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter repositories that are likely assignments
        
        Args:
            repositories: List of repository dictionaries
            
        Returns:
            List of filtered assignment dictionaries
        """
        assignments = []
        
        for repo in repositories:
            repo_name = repo.get('name', '').lower()
            repo_desc = (repo.get('description') or '').lower()
            
            # Check if repo contains assignment keywords
            is_assignment = any(
                keyword in repo_name or keyword in repo_desc 
                for keyword in self.assignment_keywords
            )
            
            # Check for GitHub Classroom generated repositories
            is_classroom_repo = any(
                pattern in repo_desc 
                for pattern in self.classroom_patterns
            )
            
            # Additional checks
            is_template = 'template' in repo_name or 'starter' in repo_name
            has_multiple_forks = repo.get('forks_count', 0) > 5
            
            if is_assignment or is_template or has_multiple_forks or is_classroom_repo:
                assignment = self._create_assignment_from_repo(repo)
                assignments.append(assignment)
        
        print(f"Found {len(assignments)} potential assignments from organization repositories")
        
        # Sort by priority score and update date
        assignments.sort(
            key=lambda x: (x.get('priority_score', 0), x.get('updated_at', '')), 
            reverse=True
        )
        
        return assignments
    
    def _create_assignment_from_repo(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create assignment dictionary from repository data
        
        Args:
            repo: Repository dictionary
            
        Returns:
            Assignment dictionary
        """
        repo_name = repo.get('name', '').lower()
        
        # Calculate priority score
        priority_score = 0
        if 'final' in repo_name:
            priority_score += 100
        if 'tugas' in repo_name:
            priority_score += 80
        if 'lab' in repo_name:
            priority_score += 40
        if 'assignment' in repo_name:
            priority_score += 50
        if 'project' in repo_name:
            priority_score += 30
        
        priority_score += repo.get('forks_count', 0) * 5
        
        return {
            'id': repo.get('id'),
            'title': repo.get('name'),
            'slug': repo.get('name'),
            'description': repo.get('description', ''),
            'html_url': repo.get('html_url'),
            'type': 'Repository-based',
            'language': repo.get('language'),
            'created_at': repo.get('created_at'),
            'updated_at': repo.get('updated_at'),
            'forks_count': repo.get('forks_count', 0),
            'stargazers_count': repo.get('stargazers_count', 0),
            'size': repo.get('size', 0),
            'accepted': repo.get('forks_count', 0),
            'deadline': None,
            'priority_score': priority_score,
            'repository': {
                'id': repo.get('id'),
                'name': repo.get('name'),
                'full_name': repo.get('full_name'),
                'html_url': repo.get('html_url'),
                'clone_url': repo.get('clone_url'),
                'ssh_url': repo.get('ssh_url')
            }
        }
    
    def get_assignment_details(self, assignment_id: int) -> Optional[Dict[str, Any]]:
        """
        Get assignment details by ID
        
        Args:
            assignment_id: Assignment ID
            
        Returns:
            Assignment details or None
        """
        print(f"Mengambil detail assignment {assignment_id}...")
        return self.auth.make_request(f'assignments/{assignment_id}')
    
    def get_accepted_assignments(self, assignment_id: int, page: int = 1, per_page: int = 100) -> List[Dict[str, Any]]:
        """
        Get accepted assignments (student repositories)
        
        Args:
            assignment_id: Assignment ID
            page: Page number
            per_page: Items per page
            
        Returns:
            List of accepted assignment dictionaries
        """
        print(f"Mengambil student repositories untuk assignment {assignment_id}...")
        params = {'page': page, 'per_page': per_page}
        
        accepted = self.auth.make_request(f'assignments/{assignment_id}/accepted_assignments', params)
        
        if accepted is None:
            return []
        
        # If response is a list
        if isinstance(accepted, list):
            return accepted
        
        # If response is single object, wrap in list
        return [accepted] if accepted else []
    
    def get_assignment_grades(self, assignment_id: int) -> Optional[Dict[str, Any]]:
        """
        Get assignment grades (optional)
        
        Args:
            assignment_id: Assignment ID
            
        Returns:
            Grades data or None
        """
        print(f"Mengambil grades untuk assignment {assignment_id}...")
        return self.auth.make_request(f'assignments/{assignment_id}/grades')
