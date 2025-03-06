
import streamlit as st
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

class FileManager:
    """A component for managing and displaying files with directory navigation dropdown"""
    
    def __init__(self):
        """Initialize the file manager"""
        if 'selected_directory' not in st.session_state:
            st.session_state.selected_directory = None
        if 'expanded_folders' not in st.session_state:
            st.session_state.expanded_folders = {}
        if 'selected_file' not in st.session_state:
            st.session_state.selected_file = None
        
    def render(self, base_path: str) -> Optional[str]:
        """
        Render the file manager with dropdown navigation
        
        Args:
            base_path: Base repository path
            
        Returns:
            Selected file path or None if no file is selected
        """
        with st.sidebar.expander("Repository Explorer", expanded=True):
            # Convert to Path object if needed
            if isinstance(base_path, str):
                base_path = Path(base_path)
                
            if not base_path.exists():
                st.warning("Repository path not found.")
                return None
            
            # Get all directories for dropdown
            all_dirs = self._get_directories(base_path)
            
            # Create the dropdown for directory selection
            dir_options = [str(d) for d in all_dirs]
            dir_labels = [os.path.relpath(d, base_path) for d in all_dirs]
            
            # Create a dictionary for mapping display names to actual paths
            dir_map = {label: path for label, path in zip(dir_labels, dir_options)}
            
            # Add "Root Directory" option
            dir_map["Root Directory"] = str(base_path)
            
            # Directory dropdown
            selected_dir_label = st.selectbox(
                "Current Directory",
                options=["Root Directory"] + sorted(dir_labels),
                index=0
            )
            
            # Get the actual directory path
            selected_dir = dir_map[selected_dir_label]
            
            # Store in session state
            st.session_state.selected_directory = selected_dir
            
            # Display files for the selected directory
            st.write("### Files")
            selected_file = self._display_directory_files(Path(selected_dir), base_path)
            
            return selected_file
    
    def _get_directories(self, base_path: Path) -> List[Path]:
        """Get all directories in the repository (excluding hidden dirs)"""
        directories = []
        
        for root, dirs, _ in os.walk(base_path):
            # Filter out hidden and excluded directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and 
                      d not in ['node_modules', '__pycache__', '.streamlit']]
            
            for dir_name in dirs:
                dir_path = Path(os.path.join(root, dir_name))
                directories.append(dir_path)
        
        return directories
    
    def _display_directory_files(self, dir_path: Path, base_path: Path) -> Optional[str]:
        """Display files in the selected directory"""
        try:
            # Get files and directories
            items = list(dir_path.iterdir())
            
            # Separate directories and files
            directories = [item for item in items if item.is_dir() and not item.name.startswith('.')]
            files = [item for item in items if item.is_file() and not item.name.startswith('.')]
            
            # Sort alphabetically
            directories.sort(key=lambda x: x.name.lower())
            files.sort(key=lambda x: x.name.lower())
            
            # Display directories first
            for directory in directories:
                col1, col2 = st.columns([0.9, 0.1])
                with col1:
                    if st.button(f"📂 {directory.name}", key=f"dir_{directory}"):
                        # Update selected directory
                        st.session_state.selected_directory = str(directory)
                        st.rerun()
            
            # Then display files
            for file in files:
                col1, col2 = st.columns([0.9, 0.1])
                with col1:
                    is_selected = st.session_state.selected_file == str(file)
                    button_type = "primary" if is_selected else "secondary"
                    
                    # Get file extension for icon
                    ext = file.suffix.lower()
                    if ext in ['.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.cs']:
                        icon = "📄 "  # Code file
                    elif ext in ['.md', '.txt']:
                        icon = "📝 "  # Text file
                    elif ext in ['.jpg', '.png', '.gif', '.svg']:
                        icon = "🖼️ "  # Image file
                    elif ext in ['.json', '.yaml', '.yml', '.xml']:
                        icon = "🔧 "  # Config file
                    else:
                        icon = "📄 "  # Generic file
                    
                    if st.button(f"{icon} {file.name}", 
                               key=f"file_{file}",
                               help=f"View {os.path.relpath(file, base_path)}",
                               type=button_type):
                        st.session_state.selected_file = str(file)
                        return str(file)
            
            return st.session_state.selected_file
            
        except Exception as e:
            st.error(f"Error accessing directory: {str(e)}")
            return None
