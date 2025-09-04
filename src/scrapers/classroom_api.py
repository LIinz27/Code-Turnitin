"""
GitHub Classroom API Operations
Handles classroom-specific API calls and data processing
"""
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from .github_auth import GitHubAuth


class ClassroomAPI:
    """Handles GitHub Classroom API operations"""
    
    def __init__(self, auth: GitHubAuth):
        """
        Initialize classroom API handler
        
        Args:
            auth: GitHub authentication instance
        """
        self.auth = auth
        self.current_classroom_id = None
    
    def get_classrooms(self) -> List[Dict[str, Any]]:
        """
        Get list of accessible classrooms
        
        Returns:
            List of classroom dictionaries
        """
        print("Mengambil daftar classroom...")
        classrooms = self.auth.make_request('classrooms')
        
        if classrooms is None:
            return []
        
        # If response is a list
        if isinstance(classrooms, list):
            return classrooms
        
        # If response is single object, wrap in list
        return [classrooms] if classrooms else []
    
    def extract_classroom_id(self, classroom_url: str) -> Optional[int]:
        """
        Extract classroom ID from classroom URL
        
        Args:
            classroom_url: GitHub Classroom URL
            
        Returns:
            Classroom ID or None
        """
        if not classroom_url:
            return None
            
        # If already a number, return directly
        if classroom_url.isdigit():
            return int(classroom_url)
        
        # For classroom URLs, lookup actual ID from API
        try:
            classrooms = self.get_classrooms()
            for classroom in classrooms:
                if classroom.get('url') == classroom_url:
                    return classroom.get('id')
        except Exception as e:
            print(f"Error during classroom lookup: {e}")
        
        # Fallback: extract first number from URL
        parsed = urlparse(classroom_url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if len(path_parts) >= 2 and path_parts[0] == 'classrooms':
            classroom_id_part = path_parts[1]
            # Get number before first dash
            if '-' in classroom_id_part:
                first_part = classroom_id_part.split('-')[0]
                if first_part.isdigit():
                    return int(first_part)
            # If no dash, get all digits
            classroom_id = ''.join(c for c in classroom_id_part if c.isdigit())
            return int(classroom_id) if classroom_id else None
        
        return None
    
    def get_classroom_details(self, classroom_id: int) -> Optional[Dict[str, Any]]:
        """
        Get classroom details by ID
        
        Args:
            classroom_id: Classroom ID
            
        Returns:
            Classroom details dictionary or None
        """
        print(f"Mengambil detail classroom {classroom_id}...")
        self.current_classroom_id = classroom_id
        return self.auth.make_request(f'classrooms/{classroom_id}')
    
    def get_organization_from_classroom(self, classroom_id: int) -> Optional[str]:
        """
        Get organization login from classroom
        
        Args:
            classroom_id: Classroom ID
            
        Returns:
            Organization login or None
        """
        classroom_details = self.get_classroom_details(classroom_id)
        if not classroom_details:
            return None
        
        organization = classroom_details.get('organization', {})
        return organization.get('login')
