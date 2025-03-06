# Repository Chat Assistant

An AI-powered chat interface for interacting with code repositories through natural language.

## Features
- Chat interface for repository interactions
- Support for GitHub repositories and local folders
- Vector store-based semantic search
- AI-powered responses using Groq models

## Local Development Setup

### Step 1: Clone and Setup
1. Clone the repository
2. Create virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

### Step 2: Environment Configuration
1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and add your GROQ API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

### Step 3: Install Dependencies
Install required packages:
```bash
pip install streamlit faiss-cpu gitpython langchain-core langchain-groq nbformat openai numpy
```

### Step 4: Run the Application
```bash
streamlit run app.py
```
The app will be available at http://localhost:8501

## Project Structure
```
├── components/         # UI components
├── models/            # AI and embedding models
├── utils/             # Utility functions
├── styles/            # CSS styles
└── app.py            # Main application
```

## Troubleshooting

### Common Issues:
1. **ModuleNotFoundError**: Make sure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. **GROQ API Key Error**: Ensure your `.env` file exists and contains the correct API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. **Port Already in Use**: Change the port using:
   ```bash
   streamlit run app.py --server.port <different-port>
   ```

### Replit vs Local Files
- **Files you need**: All `.py` files, `.env`, and the folder structure
- **Files to ignore** (Replit-specific):
  - `.replit`
  - `.upm/`
  - `.pythonlibs/`
  - `uv.lock`
  - These files are for Replit's environment and won't affect local development

## Usage
1. Enter a repository URL or local path
2. Select an AI model from the sidebar
3. Adjust max tokens if needed
4. Start chatting about the repository

## Notes
- The application will use a simple fallback embedding method if sentence-transformers is not available
- Make sure to keep your GROQ API key secure