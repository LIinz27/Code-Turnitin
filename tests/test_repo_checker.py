#!/usr/bin/env python3
"""
Test script untuk mengecek isi repository GitHub
Mendukung public dan private repositories dengan GitHub token
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class GitHubRepoChecker:
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub repository checker
        
        Args:
            token: GitHub Personal Access Token (optional untuk public repos)
        """
        self.token = token
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Code-Turnitin-Repo-Checker'
        }
        
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
    
    def get_organization_repos(self, org_name: str) -> List[Dict]:
        """
        Mendapatkan semua repository dari sebuah organisasi
        
        Args:
            org_name: Nama organisasi GitHub
            
        Returns:
            List repository dengan informasi lengkap
        """
        print(f"🔍 Mengecek organisasi: {org_name}")
        
        url = f"https://api.github.com/orgs/{org_name}/repos"
        params = {
            'per_page': 100,  # Max per page
            'sort': 'updated',
            'direction': 'desc'
        }
        
        all_repos = []
        page = 1
        
        while True:
            params['page'] = page
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                repos = response.json()
                if not repos:  # No more repos
                    break
                    
                all_repos.extend(repos)
                page += 1
                print(f"   📄 Page {page-1}: {len(repos)} repositories")
                
            elif response.status_code == 404:
                print(f"❌ Organisasi '{org_name}' tidak ditemukan")
                return []
            elif response.status_code == 403:
                print(f"🔒 Access denied. Mungkin perlu GitHub token untuk private repos")
                return []
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                return []
        
        print(f"✅ Total ditemukan: {len(all_repos)} repositories")
        return all_repos
    
    def get_repo_details(self, owner: str, repo_name: str) -> Optional[Dict]:
        """
        Mendapatkan detail lengkap sebuah repository
        
        Args:
            owner: Owner repository (user atau organization)
            repo_name: Nama repository
            
        Returns:
            Dictionary dengan detail repository
        """
        url = f"https://api.github.com/repos/{owner}/{repo_name}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error getting repo {owner}/{repo_name}: {response.status_code}")
            return None
    
    def get_repo_contents(self, owner: str, repo_name: str, path: str = "") -> List[Dict]:
        """
        Mendapatkan isi/contents dari repository
        
        Args:
            owner: Owner repository
            repo_name: Nama repository  
            path: Path dalam repository (default: root)
            
        Returns:
            List file dan folder dalam repository
        """
        url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error getting contents {owner}/{repo_name}/{path}: {response.status_code}")
            return []
    
    def analyze_repository(self, owner: str, repo_name: str) -> Dict:
        """
        Analisis lengkap sebuah repository
        
        Args:
            owner: Owner repository
            repo_name: Nama repository
            
        Returns:
            Dictionary dengan hasil analisis
        """
        print(f"\n🔍 Menganalisis repository: {owner}/{repo_name}")
        
        # Get basic repo info
        repo_info = self.get_repo_details(owner, repo_name)
        if not repo_info:
            return {}
        
        # Get repository contents
        contents = self.get_repo_contents(owner, repo_name)
        
        # Analyze file types
        file_types = {}
        total_files = 0
        
        def count_files_recursive(items, current_path=""):
            nonlocal total_files
            for item in items:
                if item['type'] == 'file':
                    total_files += 1
                    # Get file extension
                    ext = os.path.splitext(item['name'])[1].lower()
                    if ext:
                        file_types[ext] = file_types.get(ext, 0) + 1
                    else:
                        file_types['no_extension'] = file_types.get('no_extension', 0) + 1
                
                elif item['type'] == 'dir':
                    # Recursively get subdirectory contents (limit depth untuk avoid rate limit)
                    if current_path.count('/') < 2:  # Max depth 2
                        sub_contents = self.get_repo_contents(owner, repo_name, item['path'])
                        if sub_contents:
                            count_files_recursive(sub_contents, item['path'])
        
        count_files_recursive(contents)
        
        analysis = {
            'name': repo_info['name'],
            'full_name': repo_info['full_name'],
            'private': repo_info['private'],
            'description': repo_info.get('description', 'No description'),
            'language': repo_info.get('language', 'Unknown'),
            'size': repo_info['size'],  # in KB
            'stars': repo_info['stargazers_count'],
            'forks': repo_info['forks_count'],
            'issues': repo_info['open_issues_count'],
            'created_at': repo_info['created_at'],
            'updated_at': repo_info['updated_at'],
            'clone_url': repo_info['clone_url'],
            'ssh_url': repo_info['ssh_url'],
            'total_files': total_files,
            'file_types': file_types,
            'top_files': [item['name'] for item in contents if item['type'] == 'file'][:10]
        }
        
        return analysis
    
    def print_repo_summary(self, repos: List[Dict]):
        """
        Print summary dari list repositories
        """
        if not repos:
            print("❌ Tidak ada repository ditemukan")
            return
        
        print(f"\n📊 SUMMARY - {len(repos)} Repositories:")
        print("=" * 80)
        
        # Group by language
        languages = {}
        total_stars = 0
        total_forks = 0
        private_count = 0
        
        for repo in repos:
            lang = repo.get('language') or 'Unknown'
            languages[lang] = languages.get(lang, 0) + 1
            total_stars += repo.get('stargazers_count', 0)
            total_forks += repo.get('forks_count', 0)
            if repo.get('private', False):
                private_count += 1
        
        print(f"📈 Total Stars: {total_stars}")
        print(f"🍴 Total Forks: {total_forks}")
        print(f"🔒 Private Repos: {private_count}")
        print(f"🌍 Public Repos: {len(repos) - private_count}")
        
        print(f"\n💻 Languages Used:")
        for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
            print(f"   {lang}: {count} repos")
        
        print(f"\n📋 Repository List:")
        for i, repo in enumerate(repos, 1):
            visibility = "🔒" if repo.get('private', False) else "🌍"
            stars = repo.get('stargazers_count', 0)
            lang = repo.get('language', 'Unknown')
            updated = repo.get('updated_at', '')[:10]  # YYYY-MM-DD
            
            print(f"{i:2d}. {visibility} {repo['name']}")
            print(f"     Lang: {lang} | Stars: {stars} | Updated: {updated}")
            if repo.get('description'):
                desc = repo['description'][:60] + "..." if len(repo['description']) > 60 else repo['description']
                print(f"     Desc: {desc}")
            print()

def main():
    """
    Main function untuk testing
    """
    print("🚀 GitHub Repository Checker")
    print("=" * 50)
    
    # Option untuk input GitHub token
    token = input("GitHub Token (optional, tekan Enter jika skip): ").strip()
    if not token:
        token = None
        print("⚠️  Running without token - only public repos accessible")
    else:
        print("✅ Token provided - can access private repos")
    
    checker = GitHubRepoChecker(token)
    
    while True:
        print("\n" + "=" * 50)
        print("Pilih opsi:")
        print("1. Cek organisasi (misal: Lab-IF)")
        print("2. Analisis repository spesifik")
        print("3. Exit")
        
        choice = input("Pilihan (1-3): ").strip()
        
        if choice == "1":
            org_name = input("Nama organisasi: ").strip()
            if org_name:
                repos = checker.get_organization_repos(org_name)
                checker.print_repo_summary(repos)
                
                # Save to file
                if repos:
                    filename = f"repo_analysis_{org_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(repos, f, indent=2, ensure_ascii=False)
                    print(f"💾 Data saved to: {filename}")
        
        elif choice == "2":
            owner = input("Owner/Organization: ").strip()
            repo_name = input("Repository name: ").strip()
            
            if owner and repo_name:
                analysis = checker.analyze_repository(owner, repo_name)
                if analysis:
                    print(f"\n📊 ANALYSIS RESULT:")
                    print("=" * 50)
                    for key, value in analysis.items():
                        if key == 'file_types':
                            print(f"📁 File Types:")
                            for ext, count in sorted(value.items(), key=lambda x: x[1], reverse=True):
                                print(f"     {ext}: {count} files")
                        elif key == 'top_files':
                            print(f"📄 Top Files: {', '.join(value[:5])}")
                        else:
                            print(f"{key}: {value}")
        
        elif choice == "3":
            print("👋 Bye!")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
