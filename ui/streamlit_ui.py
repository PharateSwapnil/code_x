
import streamlit as st
from components.chat import ChatInterface
from components.sidebar import Sidebar
from components.file_explorer import FileExplorer
from models.ai_models import AIModels
from utils.repo_handler import RepositoryHandler

class StreamlitUI:
    """Streamlit UI implementation"""
    def __init__(self):
        self.chat_interface = ChatInterface()
        self.file_explorer = FileExplorer()
        self.ai_models = AIModels()
        self.sidebar = Sidebar(self.ai_models, self.file_explorer)
        
    def render(self):
        """Render the Streamlit UI"""
        # Render sidebar
        repo_path, selected_model, max_tokens = self.sidebar.render()
        
        # Main content area
        if st.session_state.get('selected_file_content'):
            self._display_file_content(st.session_state.selected_file_content)
        else:
            # Display chat interface
            self.chat_interface.display_chat()
            
            # Handle user input
            user_input = self.chat_interface.get_user_input()
            if user_input:
                self._process_user_input(user_input, selected_model, max_tokens)
        
    def _display_file_content(self, file_path):
        """Display file content in the main area"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Display file info
            st.subheader(f"File: {os.path.basename(file_path)}")
            st.text(f"Path: {file_path}")
            
            # Add button to return to chat
            if st.button("← Back to Chat"):
                st.session_state.selected_file_content = None
                st.rerun()
                
            # Display code with syntax highlighting
            file_extension = os.path.splitext(file_path)[1].lower()
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.java': 'java',
                '.html': 'html',
                '.css': 'css',
                '.md': 'markdown',
                '.json': 'json',
                '.cpp': 'cpp',
                '.c': 'c',
                '.h': 'c',
                '.ts': 'typescript'
            }
            language = language_map.get(file_extension, '')
            
            st.code(content, language=language)
            
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
            
    def _process_user_input(self, user_input, selected_model, max_tokens):
        """Process user input and generate response"""
        # Handle user input (same as in main app.py)
        # This is a placeholder - you would integrate with the existing chat logic
        self.chat_interface.add_message("user", user_input)
        
        # Mark as generating
        st.session_state.response_generating = True
        st.rerun()
