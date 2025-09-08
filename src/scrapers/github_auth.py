"""
GitHub Authentication and Base API Handler
Handles GitHub token management and base API requests
"""
import os
import requests
from typing import Optional, Dict, Any


class GitHubAuth:
    """Handles GitHub authentication and base API operations"""
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub authentication
        
        Args:
            github_token: GitHub personal access token
        """
        self.github_token = self._load_token(github_token)
        self.api_base = 'https://api.github.com'
        self.base_headers = self._build_headers()
        
        if not self.github_token:
            print("WARNING: No GitHub token found. Please set GITHUB_TOKEN environment variable.")
    
    def _load_token(self, provided_token: Optional[str]) -> Optional[str]:
        """
        Load GitHub token from various sources
        
        Args:
            provided_token: Token provided directly
            
        Returns:
            GitHub token or None
        """
        if provided_token:
            return provided_token
            
        # Try environment variable
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            return github_token
            
        # Try loading from config/.env
        try:
            from dotenv import load_dotenv
            config_env_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'config', '.env'
            )
            load_dotenv(dotenv_path=config_env_path)
            return os.getenv('GITHUB_TOKEN')
        except ImportError:
            pass
            
        return None
    
    def _build_headers(self) -> Dict[str, str]:
        """
        Build headers for GitHub API requests
        
        Returns:
            Request headers dictionary
        """
        headers = {
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
            
        return headers
    
    def make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Make authenticated request to GitHub API
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            JSON response or None if error
        """
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.get(
                url, 
                headers=self.base_headers, 
                params=params, 
                timeout=15
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                print(f"🔍 Resource tidak ditemukan: {endpoint}")
                print(f"   URL: {url}")
                print(f"   Kemungkinan: endpoint tidak valid, resource dihapus, atau tidak ada akses")
            elif response.status_code == 403:
                print(f"🚫 Akses ditolak: {endpoint}")
                print(f"   URL: {url}")
                print(f"   Kemungkinan: rate limit exceeded atau insufficient permissions")
            elif response.status_code == 401:
                print(f"🔐 Tidak terautentikasi: {endpoint}")
                print(f"   URL: {url}")
                print(f"   Kemungkinan: token tidak valid atau expired")
            else:
                print(f"❌ HTTP Error {response.status_code}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Error making request to {url}: {e}")
            return None
    
    def is_authenticated(self) -> bool:
        """
        Check if authentication is valid
        
        Returns:
            True if authenticated, False otherwise
        """
        if not self.github_token:
            return False
            
        # Test authentication with a simple API call
        response = self.make_request('user')
        return response is not None
