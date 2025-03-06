import streamlit as st

class ChatInterface:
    def __init__(self):
        if "messages" not in st.session_state:
            st.session_state.messages = []

    def display_chat(self):
        """Display chat messages"""
        # Display system message if repository not processed yet
        if not st.session_state.get('repo_processed', False):
            if st.session_state.get('repo_processing', False):
                st.info("Processing repository... This may take a moment.")
            else:
                st.info("Enter a repository URL or path in the sidebar to begin.")
        
        # Display existing messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Display typing indicator if generating response
        if st.session_state.get('response_generating', False):
            with st.chat_message("assistant"):
                st.write("Thinking...")

    def add_message(self, role: str, content: str):
        """Add a message to the chat history"""
        st.session_state.messages.append({"role": role, "content": content})

    def get_user_input(self):
        """Get user input from chat input box"""
        # Disable input if repository is not processed
        if not st.session_state.get('repo_processed', False):
            placeholder = "Processing repository..." if st.session_state.get('repo_processing', False) else "Enter repository details first..."
            return st.chat_input(placeholder, disabled=True)
        
        # Disable during response generation
        elif st.session_state.get('response_generating', False):
            return st.chat_input("Generating response...", disabled=True)
        
        # Normal functioning
        else:
            return st.chat_input("Ask about the repository...")

    def display_thinking(self):
        """Display thinking animation"""
        with st.chat_message("assistant"):
            st.write("Thinking...")
