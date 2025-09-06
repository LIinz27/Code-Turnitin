"""
File Management Utilities
Handles file operations, cleanup, and content retrieval
"""
import os
import shutil
from typing import Dict, Any, Optional, Tuple
from flask import current_app


class FileManager:
    """Handles file operations for the application"""
    
    @staticmethod
    def clear_student_files() -> int:
        """
        Clear all student files from the upload folder
        
        Returns:
            Number of items deleted
        """
        folder_path = current_app.config['UPLOAD_FOLDER_MAHASISWA']
        print(f"Membersihkan folder: {folder_path}")
        
        count = 0
        try:
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                try:
                    if os.path.isfile(item_path) and not item_path.endswith('.gitkeep'):
                        os.unlink(item_path)
                        count += 1
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        count += 1
                except Exception as e:
                    print(f"Error deleting item {item_path}: {e}")
                    
            print(f"Berhasil menghapus {count} item mahasiswa.")
        except FileNotFoundError:
            print(f"Folder {folder_path} tidak ditemukan.")
        except Exception as e:
            print(f"Error clearing student files: {e}")
            
        return count
    
    @staticmethod
    def clear_github_files() -> int:
        """
        Clear all GitHub files from the upload folder
        
        Returns:
            Number of items deleted
        """
        folder_path = current_app.config['UPLOAD_FOLDER_GITHUB']
        print(f"Membersihkan folder: {folder_path}")
        
        count = 0
        try:
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                try:
                    if os.path.isfile(item_path) and not item_path.endswith('.gitkeep'):
                        os.unlink(item_path)
                        count += 1
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        count += 1
                except Exception as e:
                    print(f"Error deleting item {item_path}: {e}")
                    
            print(f"Berhasil menghapus {count} item GitHub.")
        except FileNotFoundError:
            print(f"Folder {folder_path} tidak ditemukan.")
        except Exception as e:
            print(f"Error clearing GitHub files: {e}")
            
        return count
    
    @staticmethod
    def get_file_content(filename: str, file_type: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get content of a file
        
        Args:
            filename: Name of the file (dapat berupa path lengkap seperti 'repo/file.js')
            file_type: Type of file ('mahasiswa' or 'github')
            
        Returns:
            Tuple of (content, error_message)
        """
        if not filename or not file_type:
            return None, "Filename and file_type are required."
        
        # Determine base directory
        try:
            if file_type == 'mahasiswa':
                base_dir = current_app.config['UPLOAD_FOLDER_MAHASISWA']
            elif file_type == 'github':
                base_dir = current_app.config['UPLOAD_FOLDER_GITHUB']
            else:
                return None, "Invalid file_type."
        except KeyError as e:
            return None, f"Configuration error: {e}"
        
        # Handle both full path and just filename
        # If filename contains path separator, treat as full path
        file_path = os.path.join(base_dir, filename)
        
        if not os.path.exists(file_path):
            # Try to find file recursively if direct path doesn't work
            found_path = FileManager._find_file_recursive(base_dir, os.path.basename(filename))
            if found_path:
                file_path = found_path
            else:
                return None, f"File '{filename}' not found in {file_type} directory."
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content, None
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    content = file.read()
                return content, None
            except Exception as e:
                return None, f"Error reading file with fallback encoding: {e}"
        except Exception as e:
            return None, f"Error reading file: {e}"
    
    @staticmethod
    def _find_file_recursive(base_dir: str, filename: str) -> Optional[str]:
        """
        Find file recursively in directory
        
        Args:
            base_dir: Base directory to search
            filename: Name of file to find
            
        Returns:
            Full path to file or None if not found
        """
        if not os.path.exists(base_dir):
            return None
            
        for root, dirs, files in os.walk(base_dir):
            if filename in files:
                return os.path.join(root, filename)
        
        return None
    
    @staticmethod
    def get_directory_info(directory_path: str) -> Dict[str, Any]:
        """
        Get information about a directory
        
        Args:
            directory_path: Path to directory
            
        Returns:
            Dictionary with directory information
        """
        info = {
            'exists': False,
            'file_count': 0,
            'total_size': 0,
            'subdirectories': 0,
            'files': []
        }
        
        if not os.path.exists(directory_path):
            return info
        
        info['exists'] = True
        
        try:
            for root, dirs, files in os.walk(directory_path):
                info['subdirectories'] += len(dirs)
                
                for file in files:
                    if not file.endswith('.gitkeep'):
                        file_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(file_path)
                            info['total_size'] += file_size
                            info['file_count'] += 1
                            
                            # Store relative path for frontend
                            rel_path = os.path.relpath(file_path, directory_path)
                            info['files'].append({
                                'name': file,
                                'path': rel_path,
                                'size': file_size
                            })
                        except (OSError, IOError):
                            continue
                            
        except Exception as e:
            print(f"Error getting directory info for {directory_path}: {e}")
        
        return info
    
    @staticmethod
    def safe_filename(filename: str) -> str:
        """
        Create a safe filename by removing/replacing invalid characters
        
        Args:
            filename: Original filename
            
        Returns:
            Safe filename
        """
        from werkzeug.utils import secure_filename
        return secure_filename(filename)
    
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> bool:
        """
        Ensure directory exists, create if it doesn't
        
        Args:
            directory_path: Path to directory
            
        Returns:
            True if directory exists or was created successfully
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {directory_path}: {e}")
            return False
