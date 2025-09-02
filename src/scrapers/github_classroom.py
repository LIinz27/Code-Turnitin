import os
import requests
import json
from urllib.parse import urlparse, quote_plus
from .github_scraper import scrape_repo_files

class GitHubClassroom:
    def __init__(self, github_token=None):
        # Load environment variables first
        if not github_token:
            # Try multiple methods to get token
            github_token = os.getenv('GITHUB_TOKEN')
            
            if not github_token:
                # Try loading from config/.env manually
                try:
                    from dotenv import load_dotenv
                    config_env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
                    load_dotenv(dotenv_path=config_env_path)
                    github_token = os.getenv('GITHUB_TOKEN')
                except ImportError:
                    pass
        
        self.github_token = github_token
        
        if not self.github_token:
            print("WARNING: No GitHub token found. Please set GITHUB_TOKEN environment variable.")
        
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
        Ekstrak classroom ID dari URL classroom.
        URL format: https://classroom.github.com/classrooms/138271361-if20241e-pemprograman-web-lanjut
        Tapi ID sebenarnya berbeda dari angka di URL. Perlu lookup dari API.
        """
        if not classroom_url:
            return None
            
        # Jika sudah berupa angka, return langsung (mungkin sudah ID yang benar)
        if classroom_url.isdigit():
            return int(classroom_url)
        
        # Untuk URL classroom, kita perlu lookup ID sebenarnya dari API
        # karena angka di URL adalah organization ID, bukan classroom ID
        try:
            classrooms = self.get_classrooms()
            for classroom in classrooms:
                if classroom.get('url') == classroom_url:
                    return classroom.get('id')
        except Exception as e:
            print(f"Error during classroom lookup: {e}")
        
        # Fallback: extract angka pertama dari URL (mungkin ada format lain)
        parsed = urlparse(classroom_url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if len(path_parts) >= 2 and path_parts[0] == 'classrooms':
            classroom_id_part = path_parts[1]
            # Ambil angka di awal string saja (sebelum tanda '-')
            if '-' in classroom_id_part:
                first_part = classroom_id_part.split('-')[0]
                if first_part.isdigit():
                    return int(first_part)
            # Jika tidak ada tanda '-', ambil semua angka
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
        Karena GitHub Classroom API tidak mengembalikan assignments,
        kita akan menggunakan organization repositories sebagai proxy.
        """
        print(f"Mengambil daftar assignment untuk classroom {classroom_id}...")
        
        # Pertama coba API langsung
        assignments = self._make_request(f'classrooms/{classroom_id}/assignments')
        
        if assignments and len(assignments) > 0:
            print(f"Found {len(assignments)} assignments via API")
            return assignments if isinstance(assignments, list) else [assignments]
        
        # Jika API tidak mengembalikan assignments, coba ambil dari organization repos
        print("API tidak mengembalikan assignments, mencoba dari organization repositories...")
        
        # Ambil detail classroom untuk mendapatkan organization
        classroom_details = self.get_classroom_details(classroom_id)
        if not classroom_details:
            print("Tidak bisa mendapatkan detail classroom")
            return []
        
        organization = classroom_details.get('organization', {})
        org_login = organization.get('login')
        
        if not org_login:
            print("Tidak bisa mendapatkan organization login")
            return []
        
        print(f"Mencari assignments di organization: {org_login}")
        
        # Ambil repositories dari organization
        org_repos = self._make_request(f'orgs/{org_login}/repos', params={'per_page': 100})
        
        if not org_repos:
            print("Tidak bisa mendapatkan organization repositories")
            return []
        
        # Filter repositories yang kemungkinan adalah assignments
        assignments = []
        assignment_keywords = ['tugas', 'assignment', 'project', 'lab', 'final', 'ujian', 'uts', 'uas']
        
        # Special patterns for GitHub Classroom generated repos
        classroom_patterns = ['created by GitHub Classroom', 'github classroom']
        
        for repo in org_repos:
            repo_name = repo.get('name', '').lower()
            repo_desc = (repo.get('description') or '').lower()
            
            # Check if repo name or description contains assignment keywords
            is_assignment = any(keyword in repo_name or keyword in repo_desc for keyword in assignment_keywords)
            
            # Check for GitHub Classroom generated repositories
            is_classroom_repo = any(pattern in repo_desc for pattern in classroom_patterns)
            
            # Additional check: look for repos that seem to be assignment templates or student submissions
            is_template = 'template' in repo_name or 'starter' in repo_name
            has_multiple_forks = repo.get('forks_count', 0) > 5  # Likely an assignment if many students forked it
            
            # Priority scoring for better sorting
            priority_score = 0
            if 'final' in repo_name: priority_score += 100
            if 'tugas' in repo_name: priority_score += 80
            if is_classroom_repo: priority_score += 60
            if 'lab' in repo_name: priority_score += 40
            if 'assignment' in repo_name: priority_score += 50
            if 'project' in repo_name: priority_score += 30
            if has_multiple_forks: priority_score += repo.get('forks_count', 0) * 5
            
            if is_assignment or is_template or has_multiple_forks or is_classroom_repo:
                # Create an assignment-like object from repository data
                assignment = {
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
                    'accepted': repo.get('forks_count', 0),  # Use forks as proxy for accepted assignments
                    'deadline': None,  # Repository doesn't have deadline info
                    'priority_score': priority_score,  # For sorting
                    'repository': {
                        'id': repo.get('id'),
                        'name': repo.get('name'),
                        'full_name': repo.get('full_name'),
                        'html_url': repo.get('html_url'),
                        'clone_url': repo.get('clone_url'),
                        'ssh_url': repo.get('ssh_url')
                    }
                }
                assignments.append(assignment)
        
        print(f"Found {len(assignments)} potential assignments from organization repositories")
        
        # Sort by priority score first, then by update date (most recent first)
        assignments.sort(key=lambda x: (x.get('priority_score', 0), x.get('updated_at', '')), reverse=True)
        
        return assignments
    
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
        
        # Jika assignment_id adalah repository ID (dari organization repos), gunakan pendekatan berbeda
        if isinstance(assignment_id, int) or str(assignment_id).isdigit():
            return self._download_from_repository_id(assignment_id, save_dir, allowed_extensions)
        
        # Ambil daftar accepted assignments (untuk GitHub Classroom API tradisional)
        print(f"🔍 Mencari accepted assignments untuk assignment ID: {assignment_id}")
        accepted_assignments = self.get_accepted_assignments(assignment_id)
        
        if not accepted_assignments:
            print("❌ Tidak ada student repository yang ditemukan via API.")
            print("🔍 Mencoba fallback ke pencarian manual...")
            return self._download_from_repository_id(assignment_id, save_dir, allowed_extensions)
        
        downloaded_files = []
        total_repos = len(accepted_assignments)
        
        print(f"✅ Ditemukan {total_repos} student repository. Mulai download...")
        
        for i, assignment in enumerate(accepted_assignments, 1):
            repository = assignment.get('repository', {})
            repo_url = repository.get('html_url')
            repo_full_name = repository.get('full_name')
            students = assignment.get('students', [])
            
            if not repo_url:
                print(f"  [{i}/{total_repos}] ⚠️ Skipping - No repository URL found")
                continue
            
            # Ambil info student untuk nama file
            student_names = [student.get('login', 'unknown') for student in students]
            student_info = '_'.join(student_names) if student_names else 'unknown'
            
            print(f"  [{i}/{total_repos}] 📥 Downloading from {repo_full_name} (Student: {student_info})")
            
            # Check accessibility terlebih dahulu
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
                # Download files dari repository ini
                repo_files = self._download_repo_files(repo_url, save_dir, student_info, allowed_extensions)
                downloaded_files.extend(repo_files)
                print(f"    -> ✅ Downloaded {len(repo_files)} files")
            except Exception as e:
                print(f"    -> ❌ Error downloading from {repo_url}: {e}")
                continue
        
        print(f"\n📊 Download selesai. Total file downloaded: {len(downloaded_files)}")
        return downloaded_files
    
    def _download_from_repository_id(self, repo_id, save_dir, allowed_extensions):
        """
        Download files dari repository berdasarkan ID (untuk repository-based assignments)
        """
        print(f"Downloading from repository ID: {repo_id}")
        
        # Cari repository info dari daftar assignments
        assignments = self.get_classroom_assignments(self.current_classroom_id if hasattr(self, 'current_classroom_id') else None)
        target_repo = None
        
        for assignment in assignments:
            if assignment.get('id') == int(repo_id):
                target_repo = assignment
                break
        
        if not target_repo:
            print(f"Repository with ID {repo_id} not found")
            return []

        # Jika assignment tidak punya repository info, cari manual berdasarkan classroom
        repo_url = target_repo.get('html_url')
        repo_full_name = target_repo.get('repository', {}).get('full_name') if target_repo.get('repository') else None
        
        if not repo_url and not repo_full_name:
            print(f"❌ Assignment '{target_repo.get('title')}' tidak memiliki repository information")
            print("🔍 Mencoba mencari repository assignment secara manual...")
            
            # Cari repository berdasarkan nama assignment dan classroom
            return self._search_assignment_repositories(target_repo, save_dir, allowed_extensions)
        
        print(f"Found repository: {target_repo.get('title', 'Unknown')}")
        print(f"Repository URL: {repo_url}")
        
        # Check if repository is accessible
        if repo_full_name:
            accessibility = self._check_repository_accessibility(repo_full_name)
            if accessibility['status'] == 'private_no_access':
                print(f"❌ Repository is private and cannot be accessed with current token")
                print(f"   Repository: {repo_full_name}")
                print(f"   Suggestion: Repository owner needs to grant access to your GitHub account")
                return []
            elif accessibility['status'] == 'not_found':
                print(f"❌ Repository not found: {repo_full_name}")
                return []
        
        # Untuk repository yang diasumsikan sebagai template assignment,
        # kita perlu mencari repository mahasiswa yang di-fork dari ini
        return self._download_forked_repositories(target_repo, save_dir, allowed_extensions)
    
    def _search_assignment_repositories(self, assignment, save_dir, allowed_extensions):
        """
        Mencari repository assignment secara manual jika tidak ada info repository
        """
        assignment_title = assignment.get('title', '').lower()
        assignment_slug = assignment.get('slug', '').lower()
        classroom_id = getattr(self, 'current_classroom_id', None)
        
        print(f"🔍 Searching repositories for assignment: {assignment.get('title')}")
        
        # Ambil detail classroom untuk mendapatkan organization
        if classroom_id:
            classroom_details = self.get_classroom_details(classroom_id)
            if classroom_details:
                organization = classroom_details.get('organization', {})
                org_login = organization.get('login')
                
                if org_login:
                    print(f"🔍 Searching in organization: {org_login}")
                    return self._search_in_organization(org_login, assignment_title, assignment_slug, save_dir, allowed_extensions)
        
        print("❌ Could not determine organization for assignment search")
        return []
    
    def _search_in_organization(self, org_login, assignment_title, assignment_slug, save_dir, allowed_extensions):
        """
        Mencari repository di organization berdasarkan nama assignment
        """
        print(f"🔍 Searching organization {org_login} for assignment repositories...")
        
        # Ambil semua repositories di organization
        org_repos = self._make_request(f'orgs/{org_login}/repos', params={'per_page': 100})
        
        if not org_repos:
            print("❌ Could not fetch organization repositories")
            return []
        
        downloaded_files = []
        found_repos = []
        
        # Cari repository yang cocok dengan assignment
        for repo in org_repos:
            repo_name = repo.get('name', '').lower()
            repo_desc = (repo.get('description') or '').lower()
            
            # Check if repository name matches assignment
            name_match = any([
                assignment_title in repo_name,
                assignment_slug in repo_name,
                'final' in repo_name and 'tugas' in assignment_title,
                'tugas' in repo_name and 'final' in assignment_title,
                repo_name in assignment_title,
                repo_name in assignment_slug
            ])
            
            # Check description match
            desc_match = any([
                assignment_title in repo_desc,
                assignment_slug in repo_desc
            ]) if repo_desc else False
            
            if name_match or desc_match:
                found_repos.append(repo)
                print(f"✅ Found potential assignment repo: {repo.get('full_name')}")
        
        if not found_repos:
            print(f"❌ No repositories found matching assignment '{assignment_title}'")
            return []
        
        # Download dari semua repository yang ditemukan
        for repo in found_repos[:5]:  # Limit to first 5 matches
            repo_url = repo.get('html_url')
            repo_full_name = repo.get('full_name')
            
            print(f"📥 Attempting to download from: {repo_full_name}")
            
            # Check accessibility
            accessibility = self._check_repository_accessibility(repo_full_name)
            if accessibility['status'] in ['private_no_access', 'not_found']:
                print(f"⚠️ Cannot access {repo_full_name}: {accessibility['message']}")
                continue
            
            try:
                # Try direct download first
                repo_files = self._download_repo_files(repo_url, save_dir, f"assignment_{repo.get('name')}", allowed_extensions)
                downloaded_files.extend(repo_files)
                print(f"✅ Downloaded {len(repo_files)} files from {repo_full_name}")
                
                # If this looks like a template (has forks), download from forks too
                if repo.get('forks_count', 0) > 0:
                    print(f"🔍 Repository has {repo.get('forks_count')} forks, downloading student submissions...")
                    fork_files = self._download_forked_repositories({'repository': repo, 'html_url': repo_url}, save_dir, allowed_extensions)
                    downloaded_files.extend(fork_files)
                    print(f"✅ Downloaded {len(fork_files)} files from forks")
                
            except Exception as e:
                print(f"❌ Error downloading from {repo_full_name}: {e}")
                continue
        
        print(f"📊 Total files downloaded: {len(downloaded_files)}")
        return downloaded_files
    
    def _download_repo_files(self, repo_url, save_dir, student_info, allowed_extensions):
        """
        Download files dari repository menggunakan github_scraper
        """
        try:
            print(f"    🔄 Starting download from {repo_url}")
            
            # Import scraper function
            from .github_scraper import scrape_repo_files
            
            # Download menggunakan scraper yang sudah ada
            downloaded_files = scrape_repo_files(repo_url, save_dir)
            
            # Filter hanya file dengan ekstensi yang diinginkan
            filtered_files = []
            for file_info in downloaded_files:
                file_path = file_info.get('file_path', '')
                if any(file_path.lower().endswith(ext) for ext in allowed_extensions):
                    filtered_files.append(file_path)
            
            print(f"    ✅ Downloaded {len(filtered_files)} code files (total: {len(downloaded_files)})")
            return filtered_files
            
        except Exception as e:
            print(f"    ❌ Error in _download_repo_files: {e}")
            return []
    
    def _check_repository_accessibility(self, repo_full_name):
        """
        Check apakah repository bisa diakses dengan token saat ini
        """
        try:
            repo_url = f'repos/{repo_full_name}'
            response = self._make_request(repo_url)
            
            if response is None:
                return {'status': 'not_found', 'message': 'Repository not found or no access'}
            
            is_private = response.get('private', False)
            if is_private:
                # Test apakah kita bisa akses contents
                contents_response = self._make_request(f'repos/{repo_full_name}/contents')
                if contents_response is None:
                    return {'status': 'private_no_access', 'message': 'Private repository - no access'}
                else:
                    return {'status': 'private_accessible', 'message': 'Private repository - accessible'}
            else:
                return {'status': 'public', 'message': 'Public repository'}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _download_forked_repositories(self, target_repo, save_dir, allowed_extensions):
        """
        Download files dari repository yang di-fork mahasiswa (untuk assignment)
        """
        repo_full_name = target_repo.get('repository', {}).get('full_name')
        if not repo_full_name:
            print("No repository full name available")
            return []
        
        print(f"Looking for forks of {repo_full_name}...")
        
        # Ambil daftar forks
        forks = self._make_request(f'repos/{repo_full_name}/forks', params={'per_page': 100})
        
        if not forks:
            print("No forks found. Trying to download from main repository...")
            # Fallback: download dari repository utama
            return self._download_repo_files(target_repo.get('html_url'), save_dir, 'main_repo', allowed_extensions)
        
        print(f"Found {len(forks)} forks")
        downloaded_files = []
        
        for i, fork in enumerate(forks[:20], 1):  # Limit to first 20 forks
            fork_owner = fork.get('owner', {}).get('login', 'unknown')
            fork_url = fork.get('html_url')
            
            print(f"  [{i}/{min(len(forks), 20)}] Downloading from fork: {fork_owner}")
            
            try:
                # Check accessibility of fork
                accessibility = self._check_repository_accessibility(fork.get('full_name'))
                if accessibility['status'] in ['private_no_access', 'not_found']:
                    print(f"    -> ⚠️  Fork is private/inaccessible: {fork_owner}")
                    continue
                
                # Download files dari fork ini
                fork_files = self._download_repo_files(fork_url, save_dir, fork_owner, allowed_extensions)
                downloaded_files.extend(fork_files)
                print(f"    -> ✅ Downloaded {len(fork_files)} files from {fork_owner}")
                
            except Exception as e:
                print(f"    -> ❌ Error downloading from {fork_owner}: {e}")
                continue
        
        print(f"\nFork download completed. Total files: {len(downloaded_files)}")
        return downloaded_files
    
    def check_token_permissions(self):
        """
        Mengecek permission token GitHub saat ini
        """
        try:
            response = requests.get(f"{self.api_base}/user", headers=self.base_headers, timeout=15)
            
            if response.status_code != 200:
                return {
                    'status': 'error',
                    'message': 'Cannot verify token permissions'
                }
            
            user_data = response.json()
            scopes = response.headers.get('X-OAuth-Scopes', '').split(', ') if response.headers.get('X-OAuth-Scopes') else []
            
            return {
                'status': 'success',
                'user': user_data.get('login'),
                'scopes': scopes,
                'can_access_private': 'repo' in scopes or 'admin:org' in scopes,
                'recommendations': self._get_token_recommendations(scopes)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _get_token_recommendations(self, scopes):
        """
        Memberikan rekomendasi berdasarkan scopes token
        """
        recommendations = []
        
        if 'repo' not in scopes:
            recommendations.append({
                'issue': 'Missing repo scope',
                'description': 'Token cannot access private repositories',
                'solution': 'Create new token with "repo" scope for full repository access'
            })
        
        if 'admin:org' not in scopes and 'read:org' not in scopes:
            recommendations.append({
                'issue': 'Missing organization scope',
                'description': 'Token may have limited access to organization repositories',
                'solution': 'Add "read:org" scope for better organization access'
            })
        
        if len(recommendations) == 0:
            recommendations.append({
                'issue': 'Good token permissions',
                'description': 'Token has sufficient permissions for most operations',
                'solution': 'No action needed'
            })
        
        return recommendations
    
    def get_private_repo_access_guide(self, repo_full_name):
        """
        Memberikan panduan untuk mengakses repository private
        """
        return {
            'repository': repo_full_name,
            'access_methods': [
                {
                    'method': 'GitHub Token with repo scope',
                    'description': 'Create personal access token with "repo" scope',
                    'steps': [
                        'Go to GitHub Settings > Developer settings > Personal access tokens',
                        'Generate new token with "repo" scope',
                        'Replace current token in config/.env file'
                    ]
                },
                {
                    'method': 'Repository owner grants access',
                    'description': 'Ask repository owner to add you as collaborator',
                    'steps': [
                        'Contact repository owner',
                        'Request collaborator access to the repository',
                        'Accept the invitation when received'
                    ]
                },
                {
                    'method': 'Organization membership',
                    'description': 'Join the organization that owns the repository',
                    'steps': [
                        'Request membership to the organization',
                        'Wait for organization admin to approve',
                        'Repository may become accessible automatically'
                    ]
                }
            ],
            'troubleshooting': [
                'Verify token is correctly set in config/.env',
                'Check if repository URL is correct',
                'Ensure you have been granted access by repository owner',
                'Try refreshing GitHub token if it expired'
            ]
        }
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
