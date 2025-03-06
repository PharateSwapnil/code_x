from pathlib import Path
import os
from typing import Dict, List, Optional, Any, Callable

class UnifiedFileExplorer:
    """Unified file explorer component to handle repository files"""

    def __init__(self):
        self.current_repo_path = None
        self.directory_structure = {}
        self.current_file_path = None
        self.file_contents = {}

    def set_repository(self, repo_path: str, directory_structure: Dict):
        """Set the current repository and its directory structure"""
        self.current_repo_path = repo_path
        self.directory_structure = directory_structure
        self.current_file_path = None

    def get_directory_structure(self) -> Dict:
        """Get the current directory structure"""
        return self.directory_structure

    def get_file_content(self, file_path: str) -> Optional[str]:
        """Get the content of a file"""
        if file_path in self.file_contents:
            return self.file_contents[file_path]

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.file_contents[file_path] = content
                return content
        except Exception as e:
            print(f"Error reading file {file_path}: {str(e)}")
            return None

    def set_current_file(self, file_path: str):
        """Set the current file being viewed"""
        self.current_file_path = file_path

    def get_current_file(self) -> Optional[str]:
        """Get the current file path"""
        return self.current_file_path

    def get_repository_path(self) -> Optional[str]:
        """Get the current repository path"""
        return self.current_repo_path

    def get_file_paths(self, extensions: Optional[List[str]] = None) -> List[str]:
        """Get all file paths in the repository with optional extension filtering"""
        if not self.current_repo_path or not os.path.exists(self.current_repo_path):
            return []

        file_paths = []
        for root, _, files in os.walk(self.current_repo_path):
            # Skip hidden directories
            if any(part.startswith('.') for part in Path(root).parts):
                continue

            # Skip node_modules, __pycache__, etc.
            if any(excluded in root for excluded in ['node_modules', '__pycache__']):
                continue

            for file in files:
                # Skip hidden files
                if file.startswith('.'):
                    continue

                # Apply extension filter if provided
                if extensions and not any(file.endswith(ext) for ext in extensions):
                    continue

                file_paths.append(os.path.join(root, file))

        return file_paths

    def get_file_extension(self, file_path: str) -> str:
        """Get the file extension"""
        return os.path.splitext(file_path)[1].lower()

    def clear(self):
        """Clear the current state"""
        self.current_repo_path = None
        self.directory_structure = {}
        self.current_file_path = None
        self.file_contents = {}