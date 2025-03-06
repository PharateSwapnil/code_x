
import streamlit as st
import os
from pathlib import Path

class FileExplorer:
    def __init__(self):
        # Initialize session state to manage expanded folders
        if 'expanded_folders' not in st.session_state:
            st.session_state.expanded_folders = {}
        if 'selected_file' not in st.session_state:
            st.session_state.selected_file = None
            
    def render(self, base_path, initial_path=None):
        """Render the file explorer in the sidebar"""
        with st.sidebar.expander("Repository Explorer", expanded=True):
            # Convert string path to Path object if needed
            if isinstance(base_path, str):
                base_path = Path(base_path)
                
            # If base path doesn't exist, show a message
            if not base_path.exists():
                st.warning("Repository path not found.")
                return None
                
            # Current directory dropdown
            directories = self._get_all_directories(base_path)
            selected_dir = st.selectbox(
                "Current Directory",
                options=directories,
                format_func=lambda x: os.path.relpath(x, base_path),
                index=0
            )
            
            # Display file tree
            st.write("### Files")
            self._list_directory(Path(selected_dir), base_path)
            
            return st.session_state.selected_file
            
    def _get_all_directories(self, base_path):
        """Get all directories in the repository"""
        dirs = [str(base_path)]  # Start with the base directory
        
        for root, directories, _ in os.walk(base_path):
            # Skip hidden directories and common excludes
            if any(excluded in root for excluded in ['.git', 'node_modules', '__pycache__', '.streamlit']):
                continue
                
            for directory in directories:
                # Skip hidden directories
                if directory.startswith('.'):
                    continue
                    
                full_path = os.path.join(root, directory)
                dirs.append(full_path)
                
        return dirs
        
    def _list_directory(self, dir_path, base_path, level=0):
        """Recursively list the directory and display it with toggle functionality"""
        # Create collections for directories and files
        directories = []
        files = []
        
        # Get all items in the directory
        try:
            for path in dir_path.iterdir():
                # Skip hidden files and directories
                if path.name.startswith('.'):
                    continue
                    
                # Skip common exclude directories
                if path.is_dir() and path.name in ['node_modules', '__pycache__', '.streamlit']:
                    continue
                    
                if path.is_dir():
                    directories.append(path)
                else:
                    files.append(path)
        except (PermissionError, FileNotFoundError):
            st.error(f"Cannot access {dir_path}")
            return
            
        # Sort directories and files
        directories.sort(key=lambda x: x.name.lower())
        files.sort(key=lambda x: x.name.lower())
        
        # Display directories first
        for path in directories:
            folder_key = str(path)
            is_expanded = st.session_state.expanded_folders.get(folder_key, False)
            
            # Display folder with toggle
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                if st.button(f"📂 {path.name}", key=f"dir_{folder_key}"):
                    # Toggle expanded state
                    st.session_state.expanded_folders[folder_key] = not is_expanded
                    st.rerun()
                    
            # If expanded, show contents
            if is_expanded:
                self._list_directory(path, base_path, level + 1)
                
        # Then display files
        for path in files:
            file_key = str(path)
            is_selected = st.session_state.selected_file == file_key
            
            # Display file with selection
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                if st.button(f"📄 {path.name}", key=f"file_{file_key}", 
                           help=f"View {os.path.relpath(path, base_path)}",
                           type="primary" if is_selected else "secondary"):
                    st.session_state.selected_file = file_key
                    st.rerun()
