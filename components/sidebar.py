
import streamlit as st
import os

class Sidebar:
    def __init__(self, ai_models, file_explorer=None):
        self.ai_models = ai_models
        self.file_explorer = file_explorer

    def render(self):
        with st.sidebar:
            st.title("Repository Chat")

            # Repository input with default value
            repo_path = st.text_input(
                "Repository Path",
                value=st.session_state.get('repo_path', ''),
                placeholder="Enter GitHub URL or local path"
            )
            
            # Add file explorer if repository is processed
            if st.session_state.get('repo_processed', False) and self.file_explorer:
                selected_file = self.file_explorer.render(st.session_state.get('repo_dir', repo_path))
                if selected_file:
                    st.success(f"Selected: {os.path.basename(selected_file)}")
                    # Show file content in the main area
                    st.session_state.selected_file_content = selected_file

            # API Keys expander
            with st.expander("Configure API Keys", expanded=False):
                # Show current API status
                providers = {
                    "groq": "GROQ_API_KEY",
                    "openai": "OPENAI_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY",
                    "google": "GOOGLE_API_KEY",
                    "ollama": "Local models (no API key needed)"
                }
                
                for provider, env_var in providers.items():
                    if provider == "ollama":
                        st.success(f"✅ {provider.capitalize()}: {env_var}")
                        continue
                        
                    api_key = os.getenv(env_var, "")
                    if api_key:
                        st.success(f"✅ {provider.capitalize()}: Configured")
                    else:
                        st.error(f"❌ {provider.capitalize()}: Not configured")

                st.caption("To add API keys, create a .env file based on .env.example")

            # Model provider selection
            provider_options = [p for p in self.ai_models.get_provider_names() 
                               if p == "ollama" or self.ai_models.is_provider_configured(p)]
            
            if not provider_options:
                st.warning("No model providers configured. Please add API keys.")
                return repo_path, None, 2000

            selected_provider = st.selectbox(
                "Select Model Provider",
                options=provider_options,
                index=0
            )
            
            # Model selection based on provider
            model_options = self.ai_models.get_provider_models(selected_provider)
            if not model_options:
                st.warning(f"No models available for {selected_provider}.")
                return repo_path, None, 2000
                
            selected_model = st.selectbox(
                "Select AI Model",
                options=model_options,
                index=0
            )

            # Token limit
            model_info = self.ai_models.get_model_info(selected_model)
            max_tokens_default = min(2000, model_info.get("tokens", 4000) // 2)
            max_tokens = st.slider(
                "Max Tokens",
                min_value=100,
                max_value=model_info.get("tokens", 4000),
                value=max_tokens_default,
                step=100
            )
            
            # Processing options
            with st.expander("Advanced Settings", expanded=False):
                chunk_size = st.slider(
                    "Text Chunk Size",
                    min_value=200,
                    max_value=2000,
                    value=500,
                    step=100,
                    help="Size of text chunks for processing. Smaller chunks may improve accuracy but increase processing time."
                )
                
                max_parallel = st.slider(
                    "Max Parallel Processes",
                    min_value=1,
                    max_value=8,
                    value=4,
                    step=1,
                    help="Maximum number of parallel processes for repository analysis. Higher values may improve speed but increase resource usage."
                )
                
                st.session_state.chunk_size = chunk_size
                st.session_state.max_parallel = max_parallel

            # Repository structure
            if st.session_state.get('repo_structure'):
                with st.expander("Repository Structure", expanded=False):
                    st.text_area(
                        "",
                        st.session_state.repo_structure,
                        height=300,
                        disabled=True
                    )

        return repo_path, selected_model, max_tokens
