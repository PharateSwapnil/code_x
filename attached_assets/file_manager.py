import streamlit as st

# Initialize session state to manage expanded folders
if 'expanded_folders' not in st.session_state:
    st.session_state.expanded_folders = {}

def list_directory(dir_path, level=0):
    """Recursively list the directory and display it in a tree-like structure with toggle functionality."""
    indent = "&nbsp;" * (level * 8)  # HTML non-breaking spaces for indentation
    
    # Create a toggle button for the current directory
    folder_key = str(dir_path)  # Use the directory path as a unique key
    is_expanded = st.session_state.expanded_folders.get(folder_key, False)

    # Display the folder name without a box, using markdown
    if st.button(f"{indent}📂 {dir_path.name}", key=folder_key, help="Click to expand/collapse"):
        # Toggle the expanded state
        st.session_state.expanded_folders[folder_key] = not is_expanded
        is_expanded = st.session_state.expanded_folders[folder_key]

    # If the folder is expanded, list its contents
    if is_expanded:
        # Separate directories and files into two lists
        directories = []
        files = []
        
        for path in dir_path.iterdir():
            if path.is_dir():
                directories.append(path)
            else:
                files.append(path)

        # Sort directories and files
        directories.sort(key=lambda x: x.name)
        files.sort(key=lambda x: x.name)

        # Display directories first
        for path in directories:
            list_directory(path, level + 1)  # Recursively list subdirectories

        # Then display files
        for path in files:
            st.markdown(f"{indent}&nbsp;&nbsp;📄 {path.name}", unsafe_allow_html=True)
