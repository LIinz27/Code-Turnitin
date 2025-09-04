"""
Folder Organization Utilities
Handles organized folder structure creation for classroom data
"""
import os
from typing import Optional, Dict, Any
from .assignment_manager import AssignmentManager
from .classroom_api import ClassroomAPI


class FolderOrganizer:
    """Manages organized folder structure for classroom and assignment data"""
    
    def __init__(self, assignment_manager: AssignmentManager, classroom_api: ClassroomAPI):
        """
        Initialize folder organizer
        
        Args:
            assignment_manager: Assignment manager instance
            classroom_api: Classroom API instance
        """
        self.assignment_manager = assignment_manager
        self.classroom_api = classroom_api
    
    def create_organized_save_dir(self, base_save_dir: str, assignment_id: int) -> str:
        """
        Create organized directory structure based on classroom and assignment
        
        Args:
            base_save_dir: Base directory for saving files
            assignment_id: Assignment ID
            
        Returns:
            Organized directory path
        """
        try:
            # Get assignment details
            assignment_details = self.assignment_manager.get_assignment_details(assignment_id)
            if not assignment_details:
                print("⚠️ Tidak dapat mengambil detail assignment, menggunakan struktur default")
                return os.path.join(base_save_dir, f"assignment_{assignment_id}")
            
            # Get assignment name
            assignment_title = assignment_details.get('title', f'Assignment_{assignment_id}')
            safe_assignment_name = self._sanitize_folder_name(assignment_title)
            
            # Get classroom information
            classroom_name = self._get_classroom_name()
            
            # Create structure: base_dir/Classroom_Name/Assignment_Name/
            organized_dir = os.path.join(base_save_dir, classroom_name, safe_assignment_name)
            
            print(f"📁 Struktur folder: {classroom_name}/{safe_assignment_name}")
            
            # Create directory if it doesn't exist
            os.makedirs(organized_dir, exist_ok=True)
            
            return organized_dir
            
        except Exception as e:
            print(f"⚠️ Error creating organized directory: {e}")
            fallback_dir = os.path.join(base_save_dir, f"assignment_{assignment_id}")
            os.makedirs(fallback_dir, exist_ok=True)
            return fallback_dir
    
    def _get_classroom_name(self) -> str:
        """
        Get current classroom name for folder organization
        
        Returns:
            Sanitized classroom name
        """
        classroom_name = "Unknown_Classroom"
        classroom_id = self.classroom_api.current_classroom_id
        
        if classroom_id:
            classroom_details = self.classroom_api.get_classroom_details(classroom_id)
            if classroom_details:
                classroom_name = classroom_details.get('name', f'Classroom_{classroom_id}')
                classroom_name = self._sanitize_folder_name(classroom_name)
        
        return classroom_name
    
    def _sanitize_folder_name(self, name: str) -> str:
        """
        Sanitize name for safe folder creation
        
        Args:
            name: Original name
            
        Returns:
            Sanitized folder name
        """
        # Remove invalid characters and replace spaces with underscores
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        
        # Ensure name is not empty
        if not safe_name:
            safe_name = "Unknown"
        
        return safe_name
    
    def create_student_folder(self, base_dir: str, repo_full_name: str, student_info: str) -> str:
        """
        Create folder for individual student repository
        
        Args:
            base_dir: Base directory
            repo_full_name: Full repository name (owner/repo)
            student_info: Student information string
            
        Returns:
            Student folder path
        """
        # Create folder name from repository and student info
        repo_folder_name = f"{repo_full_name.replace('/', '_')}"
        if student_info and student_info != 'unknown':
            repo_folder_name = f"{student_info}_{repo_folder_name}"
        
        student_folder = os.path.join(base_dir, repo_folder_name)
        os.makedirs(student_folder, exist_ok=True)
        
        return student_folder
    
    def get_folder_structure_info(self, base_dir: str) -> Dict[str, Any]:
        """
        Get information about folder structure
        
        Args:
            base_dir: Base directory to analyze
            
        Returns:
            Dictionary with folder structure information
        """
        info = {
            'total_classrooms': 0,
            'total_assignments': 0,
            'total_students': 0,
            'folder_tree': {}
        }
        
        if not os.path.exists(base_dir):
            return info
        
        try:
            # Count classrooms (first level directories)
            classroom_dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
            info['total_classrooms'] = len(classroom_dirs)
            
            for classroom_dir in classroom_dirs:
                classroom_path = os.path.join(base_dir, classroom_dir)
                
                # Count assignments (second level directories)
                assignment_dirs = [d for d in os.listdir(classroom_path) if os.path.isdir(os.path.join(classroom_path, d))]
                info['total_assignments'] += len(assignment_dirs)
                info['folder_tree'][classroom_dir] = {}
                
                for assignment_dir in assignment_dirs:
                    assignment_path = os.path.join(classroom_path, assignment_dir)
                    
                    # Count students (third level directories)
                    student_dirs = [d for d in os.listdir(assignment_path) if os.path.isdir(os.path.join(assignment_path, d))]
                    info['total_students'] += len(student_dirs)
                    info['folder_tree'][classroom_dir][assignment_dir] = len(student_dirs)
                    
        except Exception as e:
            print(f"Error analyzing folder structure: {e}")
        
        return info
