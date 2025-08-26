import os
import requests
import json
from urllib.parse import urlparse, quote_plus
from .github_scraper import scrape_repo_files

class GitHubClassroom:
    def __init__(self, github_token=None):
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.base_headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        self.api_base = 'https://api.github.com'
    
    def _make_request(self, endpoint, params=None):
        """Helper method untuk membuat request ke GitHub API"""
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        try:
            response = requests.get(url, headers=self.base_headers, params=params, timeout=15)
            
            # Log rate limit info
            print(f"DEBUG: Rate Limit - Remaining: {response.headers.get('X-RateLimit-Remaining')}")
            print(f"DEBUG: Rate Limit - Reset: {response.headers.get('X-RateLimit-Reset')}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return None
    
    def get_classrooms(self):
        """
        Mengambil daftar classroom yang dapat diakses oleh user
        """
        print("Mengambil daftar classroom...")
        classrooms = self._make_request('classrooms')
        
        if classrooms is None:
            return []
        
        # Jika response adalah list
        if isinstance(classrooms, list):
            return classrooms
        
        # Jika response adalah single object, wrap dalam list
        return [classrooms] if classrooms else []
    
    def extract_classroom_id(self, classroom_url):
        """
        Ekstrak classroom ID dari URL classroom
        Contoh: https://classroom.github.com/classrooms/12345-programming -> 12345
        """
        if not classroom_url:
            return None
            
        # Jika sudah berupa angka, return langsung
        if classroom_url.isdigit():
            return int(classroom_url)
        
        # Parse dari URL
        parsed = urlparse(classroom_url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if len(path_parts) >= 2 and path_parts[0] == 'classrooms':
            classroom_id_part = path_parts[1]
            # Ambil angka di awal string (format: "12345-nama-classroom")
            classroom_id = ''.join(c for c in classroom_id_part if c.isdigit())
            return int(classroom_id) if classroom_id else None
        
        return None
    
    def get_classroom_details(self, classroom_id):
        """
        Mengambil detail classroom berdasarkan ID
        """
        print(f"Mengambil detail classroom {classroom_id}...")
        return self._make_request(f'classrooms/{classroom_id}')
    
    def get_classroom_assignments(self, classroom_id):
        """
        Mengambil daftar assignment dalam classroom
        """
        print(f"Mengambil daftar assignment untuk classroom {classroom_id}...")
        assignments = self._make_request(f'classrooms/{classroom_id}/assignments')
        
        if assignments is None:
            return []
        
        # Jika response adalah list
        if isinstance(assignments, list):
            return assignments
        
        # Jika response adalah single object, wrap dalam list
        return [assignments] if assignments else []
    
    def get_assignment_details(self, assignment_id):
        """
        Mengambil detail assignment berdasarkan ID
        """
        print(f"Mengambil detail assignment {assignment_id}...")
        return self._make_request(f'assignments/{assignment_id}')
    
    def get_accepted_assignments(self, assignment_id, page=1, per_page=100):
        """
        Mengambil daftar student repositories yang sudah accept assignment
        """
        print(f"Mengambil student repositories untuk assignment {assignment_id}...")
        params = {'page': page, 'per_page': per_page}
        
        accepted = self._make_request(f'assignments/{assignment_id}/accepted_assignments', params)
        
        if accepted is None:
            return []
        
        # Jika response adalah list
        if isinstance(accepted, list):
            return accepted
        
        # Jika response adalah single object, wrap dalam list
        return [accepted] if accepted else []
    
    def get_assignment_grades(self, assignment_id):
        """
        Mengambil grades untuk assignment (opsional, untuk informasi tambahan)
        """
        print(f"Mengambil grades untuk assignment {assignment_id}...")
        return self._make_request(f'assignments/{assignment_id}/grades')
    
    def download_classroom_assignment_repos(self, assignment_id, save_dir, allowed_extensions=('.js', '.py', '.java', '.c', '.cpp', '.h')):
        """
        Download semua repository mahasiswa untuk assignment tertentu
        """
        print(f"Memulai download repository untuk assignment {assignment_id}...")
        
        # Buat direktori jika belum ada
        os.makedirs(save_dir, exist_ok=True)
        
        # Ambil daftar accepted assignments
        accepted_assignments = self.get_accepted_assignments(assignment_id)
        
        if not accepted_assignments:
            print("Tidak ada student repository yang ditemukan.")
            return []
        
        downloaded_files = []
        total_repos = len(accepted_assignments)
        
        print(f"Ditemukan {total_repos} student repository. Mulai download...")
        
        for i, assignment in enumerate(accepted_assignments, 1):
            repository = assignment.get('repository', {})
            repo_url = repository.get('html_url')
            students = assignment.get('students', [])
            
            if not repo_url:
                print(f"  [{i}/{total_repos}] Skipping - No repository URL found")
                continue
            
            # Ambil info student untuk nama file
            student_names = [student.get('login', 'unknown') for student in students]
            student_info = '_'.join(student_names) if student_names else 'unknown'
            
            print(f"  [{i}/{total_repos}] Downloading: {repository.get('full_name', repo_url)} (Student: {student_info})")
            
            # Download menggunakan fungsi yang sudah ada
            try:
                repo_files = scrape_repo_files(repo_url, save_dir, allowed_extensions)
                downloaded_files.extend(repo_files)
                print(f"    ✓ Berhasil download {len(repo_files)} file")
            except Exception as e:
                print(f"    ✗ Error downloading {repo_url}: {e}")
        
        print(f"\nSelesai! Total {len(downloaded_files)} file berhasil didownload dari {total_repos} repository.")
        return downloaded_files
    
    def get_classroom_summary(self, classroom_id):
        """
        Mendapatkan ringkasan lengkap classroom beserta assignments
        """
        print(f"Mengambil ringkasan classroom {classroom_id}...")
        
        # Ambil detail classroom
        classroom_details = self.get_classroom_details(classroom_id)
        if not classroom_details:
            return None
        
        # Ambil daftar assignments
        assignments = self.get_classroom_assignments(classroom_id)
        
        # Tambahkan info assignment ke summary
        for assignment in assignments:
            assignment_id = assignment.get('id')
            if assignment_id:
                # Ambil jumlah accepted assignments
                accepted = self.get_accepted_assignments(assignment_id, per_page=1)
                assignment['total_students'] = len(accepted) if accepted else 0
        
        return {
            'classroom': classroom_details,
            'assignments': assignments,
            'total_assignments': len(assignments)
        }

# Helper functions untuk kemudahan penggunaan
def get_classroom_instance():
    """Helper untuk membuat instance GitHubClassroom dengan token dari environment"""
    return GitHubClassroom()

def quick_download_assignment(assignment_id, save_dir='data/classroom'):
    """Quick function untuk download assignment dengan default settings"""
    classroom = get_classroom_instance()
    return classroom.download_classroom_assignment_repos(assignment_id, save_dir)

# Test function jika file dijalankan langsung
if __name__ == "__main__":
    print("Testing GitHub Classroom integration...")
    
    classroom = get_classroom_instance()
    
    # Test: Ambil daftar classroom
    classrooms = classroom.get_classrooms()
    print(f"Found {len(classrooms)} accessible classrooms:")
    
    for classroom_info in classrooms:
        print(f"  - {classroom_info.get('name', 'Unknown')} (ID: {classroom_info.get('id', 'Unknown')})")
        
        # Test: Ambil assignments untuk classroom pertama
        if classroom_info.get('id'):
            assignments = classroom.get_classroom_assignments(classroom_info['id'])
            print(f"    Assignments: {len(assignments)}")
            
            for assignment in assignments[:3]:  # Maksimal 3 untuk testing
                print(f"      - {assignment.get('title', 'Unknown')} (ID: {assignment.get('id', 'Unknown')})")
