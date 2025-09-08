"""
Repository Download Operations
Handles downloading files from GitHub repositories with various strategies
"""
import os
import time
from typing import List, Dict, Any, Tuple, Optional
from .github_auth import GitHubAuth
from .assignment_manager import AssignmentManager
from .folder_organizer import FolderOrganizer
from .github_scraper import scrape_repo_files


class RepositoryDownloader:
    """Handles downloading repositories and files from GitHub"""
    
    def __init__(self, auth: GitHubAuth, assignment_manager: AssignmentManager, folder_organizer: FolderOrganizer):
        """
        Initialize repository downloader
        
        Args:
            auth: GitHub authentication instance
            assignment_manager: Assignment manager instance
            folder_organizer: Folder organizer instance
        """
        self.auth = auth
        self.assignment_manager = assignment_manager
        self.folder_organizer = folder_organizer
        
        # Default allowed file extensions
        self.default_extensions = (
            '.js', '.py', '.java', '.c', '.cpp', '.h', '.html', '.css', '.scss',
            '.jsx', '.tsx', '.ts', '.txt', '.md', '.json', '.yml', '.yaml',
            '.xml', '.php', '.rb', '.go', '.rs', '.cs'
        )
    
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
        if allowed_extensions is None:
            allowed_extensions = self.default_extensions
            
        print(f"Memulai download repository untuk assignment {assignment_id}...")
        
        # Create organized folder structure
        organized_save_dir = self.folder_organizer.create_organized_save_dir(save_dir, assignment_id)
        print(f"📁 Data akan disimpan di: {organized_save_dir}")
        
        # Get accepted assignments using GitHub Classroom API
        print(f"🔍 Mencari accepted assignments untuk assignment ID: {assignment_id}")
        accepted_assignments = self.assignment_manager.get_accepted_assignments(assignment_id)
        
        if not accepted_assignments:
            print("❌ Tidak ada student repository yang ditemukan via GitHub Classroom API.")
            print("   Kemungkinan penyebab:")
            print("   - Assignment ID tidak valid")
            print("   - Token GitHub tidak memiliki akses ke classroom")
            print("   - Assignment belum memiliki submissions")
            print("   - Repository sudah dihapus atau di-private")
            
            # Try fallback method
            print("🔍 Mencoba fallback ke pencarian manual...")
            return self._download_from_repository_id(assignment_id, organized_save_dir, allowed_extensions)
        
        print(f"✅ Ditemukan {len(accepted_assignments)} accepted assignments")
        return self._download_accepted_assignments(accepted_assignments, organized_save_dir, allowed_extensions)
    
    def _download_accepted_assignments(
        self, 
        accepted_assignments: List[Dict[str, Any]], 
        save_dir: str, 
        allowed_extensions: Tuple[str, ...]
    ) -> List[str]:
        """
        Download files from accepted assignments
        
        Args:
            accepted_assignments: List of accepted assignment data
            save_dir: Directory to save files
            allowed_extensions: Allowed file extensions
            
        Returns:
            List of downloaded file paths
        """
        downloaded_files = []
        total_repos = len(accepted_assignments)
        
        print(f"✅ Ditemukan {total_repos} student repository. Mulai download...")
        
        # Progress tracking
        start_time = time.time()
        
        for i, assignment in enumerate(accepted_assignments, 1):
            repository = assignment.get('repository', {})
            repo_url = repository.get('html_url')
            repo_full_name = repository.get('full_name')
            students = assignment.get('students', [])
            
            if not repo_url:
                print(f"  [{i}/{total_repos}] ⚠️ Skipping - No repository URL found")
                continue
            
            # Get student info for file naming
            student_names = [student.get('login', 'unknown') for student in students]
            student_info = '_'.join(student_names) if student_names else 'unknown'
            
            # Progress information
            elapsed = time.time() - start_time
            eta = (elapsed / i) * (total_repos - i) if i > 0 else 0
            print(f"  [{i}/{total_repos}] 📥 Downloading from {repo_full_name} (Student: {student_info})")
            print(f"    Progress: {(i/total_repos)*100:.1f}% | Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s")
            
            # Check if already downloaded
            repo_folder_name = f"{repo_full_name.replace('/', '_')}"
            repo_save_path = os.path.join(save_dir, repo_folder_name)
            if os.path.exists(repo_save_path) and os.listdir(repo_save_path):
                print(f"    -> ⏭️ Already downloaded, skipping...")
                continue
            
            # Check repository accessibility
            if repo_full_name:
                accessibility = self._check_repository_accessibility(repo_full_name)
                if accessibility['status'] == 'private_no_access':
                    print(f"    -> ❌ Private repository - no access")
                    continue
                elif accessibility['status'] == 'not_found':
                    print(f"    -> ❌ Repository not found")
                    continue
                else:
                    print(f"    -> ✅ Repository accessible ({accessibility['status']})")
            
            try:
                # Download files from this repository
                repo_files = self._download_repo_files(repo_url, save_dir, student_info, allowed_extensions)
                downloaded_files.extend(repo_files)
                print(f"    -> ✅ Downloaded {len(repo_files)} files")
            except Exception as e:
                print(f"    -> ❌ Error downloading from {repo_url}: {e}")
                continue
        
        print(f"\n📊 Download selesai. Total file downloaded: {len(downloaded_files)}")
        return downloaded_files
    
    def _download_from_repository_id(
        self, 
        repo_id: int, 
        save_dir: str, 
        allowed_extensions: Tuple[str, ...]
    ) -> List[str]:
        """
        Download from repository ID (fallback method)
        
        Args:
            repo_id: Repository ID
            save_dir: Directory to save files
            allowed_extensions: Allowed file extensions
            
        Returns:
            List of downloaded file paths
        """
        print(f"🔍 Attempting to download from repository ID: {repo_id}")
        print(f"⚠️ Repository ID {repo_id} tidak dapat diakses langsung.")
        print(f"   Ini biasanya terjadi karena repository private atau tidak tersedia.")
        print(f"   Coba gunakan GitHub Classroom API atau pastikan token memiliki akses.")
        
        # Instead of trying to access by ID, return empty list
        # The calling function should handle this gracefully
        return []
    
    def _download_repo_files(
        self, 
        repo_url: str, 
        save_dir: str, 
        student_info: str, 
        allowed_extensions: Tuple[str, ...]
    ) -> List[str]:
        """
        Download files from a single repository
        
        Args:
            repo_url: Repository URL
            save_dir: Directory to save files
            student_info: Student information
            allowed_extensions: Allowed file extensions
            
        Returns:
            List of downloaded file paths
        """
        try:
            # Use the existing github_scraper module
            downloaded_files = scrape_repo_files(
                repo_url=repo_url,
                save_dir=save_dir,
                allowed_extensions=allowed_extensions
            )
            return downloaded_files
        except Exception as e:
            print(f"Error downloading repository files: {e}")
            return []
    
    def _check_repository_accessibility(self, repo_full_name: str) -> Dict[str, Any]:
        """
        Check if repository is accessible
        
        Args:
            repo_full_name: Full repository name (owner/repo)
            
        Returns:
            Dictionary with accessibility status
        """
        try:
            repo_data = self.auth.make_request(f'repos/{repo_full_name}')
            
            if repo_data is None:
                return {'status': 'not_found', 'message': 'Repository not found'}
            
            is_private = repo_data.get('private', False)
            
            if is_private:
                return {'status': 'private_accessible', 'message': 'Private repository with access'}
            else:
                return {'status': 'public', 'message': 'Public repository'}
                
        except Exception as e:
            return {'status': 'error', 'message': f'Error checking accessibility: {e}'}
    
    def preview_assignment_repositories(self, assignment_id: int) -> Dict[str, Any]:
        """
        Preview repositories without downloading
        
        Args:
            assignment_id: Assignment ID
            
        Returns:
            Preview data dictionary
        """
        print(f"🔍 Preview repositories for assignment: {assignment_id}")
        
        preview_data = {
            'repositories': [],
            'estimated_files': 0,
            'access_summary': {
                'public': 0,
                'private_accessible': 0,
                'private_no_access': 0,
                'not_found': 0,
                'total': 0
            },
            'method_used': 'unknown'
        }
        
        # Try GitHub Classroom accepted assignments API
        try:
            print("📡 Fetching accepted assignments...")
            accepted_assignments = self.assignment_manager.get_accepted_assignments(assignment_id)
            if accepted_assignments:
                preview_data['method_used'] = 'github_classroom_api'
                print(f"✅ Found {len(accepted_assignments)} accepted assignments")
                preview_data = self._process_preview_data_fast(accepted_assignments, preview_data)
            else:
                print("❌ No accepted assignments found")
                
        except Exception as e:
            print(f"Error during preview: {e}")
        
        return preview_data
    
    def _process_preview_data_fast(
        self, 
        accepted_assignments: List[Dict[str, Any]], 
        preview_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process preview data with optimized performance (skip accessibility checks for speed)
        
        Args:
            accepted_assignments: List of accepted assignments
            preview_data: Preview data to update
            
        Returns:
            Updated preview data
        """
        print(f"🚀 Fast processing {len(accepted_assignments)} repositories...")
        
        for assignment in accepted_assignments:
            repository = assignment.get('repository', {})
            repo_full_name = repository.get('full_name')
            
            if repo_full_name:
                # Skip accessibility check for speed - assume accessible
                is_private = repository.get('private', False)
                
                # Quick status determination based on privacy
                if is_private:
                    accessibility_status = 'private_accessible'  # Assume accessible since it's in accepted assignments
                else:
                    accessibility_status = 'public'
                
                repo_info = {
                    'name': repo_full_name,
                    'full_name': repo_full_name,
                    'html_url': repository.get('html_url'),
                    'students': [s.get('login') for s in assignment.get('students', [])],
                    'accessibility': {
                        'status': accessibility_status,
                        'message': 'Status determined without API check for speed'
                    },
                    'private': is_private,
                    'estimated_files': 10  # Default estimate for speed
                }
                
                preview_data['repositories'].append(repo_info)
                
                # Update access summary
                valid_statuses = ['public', 'private_accessible', 'private_no_access', 'not_found']
                if accessibility_status in valid_statuses:
                    preview_data['access_summary'][accessibility_status] += 1
                else:
                    preview_data['access_summary']['not_found'] += 1
                preview_data['access_summary']['total'] += 1
        
        print(f"✅ Fast processing completed: {len(preview_data['repositories'])} repositories")
        return preview_data

    def _process_preview_data(
        self, 
        accepted_assignments: List[Dict[str, Any]], 
        preview_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process preview data from accepted assignments (with full accessibility checks)
        
        Args:
            accepted_assignments: List of accepted assignments
            preview_data: Preview data to update
            
        Returns:
            Updated preview data
        """
        print(f"🔍 Full processing {len(accepted_assignments)} repositories...")
        
        for assignment in accepted_assignments:
            repository = assignment.get('repository', {})
            repo_full_name = repository.get('full_name')
            
            if repo_full_name:
                accessibility = self._check_repository_accessibility(repo_full_name)
                accessibility_status = accessibility.get('status', 'unknown')
                
                repo_info = {
                    'name': repo_full_name,
                    'full_name': repo_full_name,
                    'html_url': repository.get('html_url'),
                    'students': [s.get('login') for s in assignment.get('students', [])],
                    'accessibility': accessibility,
                    'private': repository.get('private', False),
                    'estimated_files': 10  # Default estimate
                }
                
                preview_data['repositories'].append(repo_info)
                
                # Update access summary
                valid_statuses = ['public', 'private_accessible', 'private_no_access', 'not_found']
                if accessibility_status in valid_statuses:
                    preview_data['access_summary'][accessibility_status] += 1
                else:
                    # For unknown statuses, count as 'not_found'
                    preview_data['access_summary']['not_found'] += 1
                preview_data['access_summary']['total'] += 1
        
        return preview_data
