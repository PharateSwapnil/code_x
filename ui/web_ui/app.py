
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import os
import sys
import json
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from pathlib import Path

# Add parent directory to path for imports
current_dir = Path(__file__).parent
parent_dir = str(current_dir.parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from models.ai_models import AIModels
from models.embeddings import EmbeddingModel
from utils.vector_store import VectorStore
from utils.repo_handler import RepositoryHandler
from components.unified_file_explorer import UnifiedFileExplorer
from utils.parallel_processor import ParallelProcessor

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24).hex())
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # Session timeout in seconds (1 hour)

# Initialize components
ai_models = AIModels()
embedding_model = EmbeddingModel()
vector_store = VectorStore()
repo_handler = RepositoryHandler()
file_explorer = UnifiedFileExplorer()

# Mock users database (replace with a real database in production)
users = {
    "admin": {
        "password": generate_password_hash("admin123"),
        "name": "Administrator"
    },
    "user": {
        "password": generate_password_hash("user123"),
        "name": "Test User"
    }
}

# AI Agents configuration
AI_AGENTS = {
    "software_developer": {
        "name": "Senior Software Developer",
        "expertise": ["code analysis", "architecture", "refactoring", "best practices"],
        "system_prompt": "You are an expert senior software developer with deep knowledge across various programming languages and architectures. Your strength is analyzing code, suggesting improvements, and explaining software concepts clearly."
    },
    "data_engineer": {
        "name": "Senior Data Engineer",
        "expertise": ["data pipelines", "ETL", "databases", "data modeling"],
        "system_prompt": "You are a senior data engineer specializing in data infrastructure, pipelines, and processing. You excel at designing robust data solutions and optimizing data workflows."
    },
    "data_scientist": {
        "name": "Senior Data Scientist",
        "expertise": ["machine learning", "data analysis", "statistics", "visualization"],
        "system_prompt": "You are a senior data scientist with expertise in machine learning, statistical analysis, and data visualization. You help extract meaningful insights from data and implement AI solutions."
    },
    "fullstack_developer": {
        "name": "Senior Fullstack Developer",
        "expertise": ["frontend", "backend", "database", "UI/UX", "web technologies"],
        "system_prompt": "You are a senior fullstack developer with comprehensive knowledge of both frontend and backend technologies. You excel at building complete web applications and integrating different technology stacks."
    }
}

# =====================
# Authentication Routes
# =====================

@app.route('/')
def index():
    """Redirect to login page if not logged in, otherwise to repository chat"""
    if 'user_id' in session:
        return redirect(url_for('repository_chat'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and check_password_hash(users[username]['password'], password):
            session['user_id'] = username
            session['user_name'] = users[username]['name']
            return redirect(url_for('repository_chat'))
        else:
            flash('Invalid username or password', 'error')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        
        if username in users:
            flash('Username already exists', 'error')
        else:
            users[username] = {
                'password': generate_password_hash(password),
                'name': name
            }
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    return redirect(url_for('login'))

# ==================
# Main Application Routes
# ==================

@app.route('/repository_chat')
def repository_chat():
    """Main repository chat page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    providers = ai_models.get_provider_names()
    model_names = ai_models.get_model_names()
    return render_template('repository_chat.html', 
                          username=session.get('user_name'), 
                          providers=providers, 
                          models=model_names,
                          agents=AI_AGENTS)

@app.route('/database_chat')
def database_chat():
    """Database chat page (placeholder)"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('database_chat.html', username=session.get('user_name'))

@app.route('/documents_chat')
def documents_chat():
    """Documents chat page (placeholder)"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('documents_chat.html', username=session.get('user_name'))

# ==================
# API Routes
# ==================

@app.route('/api/models', methods=['GET'])
def get_models():
    """API endpoint to get available models"""
    return jsonify({
        'providers': ai_models.get_provider_names(),
        'models': ai_models.get_model_names()
    })

@app.route('/api/repository', methods=['POST'])
def process_repository():
    """API endpoint to process repository"""
    data = request.json
    repo_path = data.get('repo_path', '')
    
    if not repo_path:
        return jsonify({'success': False, 'error': 'Repository path is required'})
    
    try:
        # Process repository and get file structure
        repo_dir, directory_structure, file_contents = repo_handler.process_repository(repo_path)
        
        # Set repository in file explorer
        file_explorer.set_repository(repo_dir, directory_structure)
        
        # Store repository information in session
        session['repository'] = {
            'path': repo_dir,
            'structure': json.dumps(str(directory_structure)[:1000] + '...')  # Truncated for session storage
        }
        
        # Process repository files and create embeddings
        documents = []
        for file_path, content in file_contents:
            if content:
                # Create document chunks
                relative_path = os.path.relpath(file_path, repo_dir)
                documents.append({
                    "content": content,
                    "source": relative_path
                })
        
        # Generate embeddings and add to vector store
        if documents:
            embeddings = embedding_model.embed_documents([doc["content"] for doc in documents])
            vector_store.add_documents(documents, embeddings)
            
        # Store a session identifier for the vector store
        if 'vector_store_id' not in session:
            session['vector_store_id'] = str(uuid.uuid4())
            
        return jsonify({
            'success': True, 
            'repo_dir': repo_dir,
            'file_count': len(file_contents),
            'document_count': len(documents)
        })
        
    except Exception as e:
        print(f"Error processing repository: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/directory_structure', methods=['GET'])
def get_directory_structure():
    """API endpoint to get directory structure"""
    repo_path = file_explorer.get_repository_path()
    if not repo_path:
        return jsonify({'success': False, 'error': 'No repository loaded'})
        
    try:
        structure = repo_handler.get_directory_structure(repo_path)
        return jsonify({
            'success': True,
            'structure': structure
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/file_content', methods=['GET'])
def get_file_content():
    """API endpoint to get file content"""
    file_path = request.args.get('path')
    if not file_path:
        return jsonify({'success': False, 'error': 'File path is required'})
        
    try:
        content = file_explorer.get_file_content(file_path)
        if content is None:
            return jsonify({'success': False, 'error': 'Unable to read file'})
            
        return jsonify({
            'success': True,
            'content': content,
            'path': file_path,
            'extension': file_explorer.get_file_extension(file_path)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint for chat"""
    data = request.json
    query = data.get('query', '')
    model_key = data.get('model', 'groq/llama-3.1-8b-instant')
    max_tokens = int(data.get('max_tokens', 1000))
    
    if not query:
        return jsonify({'success': False, 'error': 'Query is required'})
    
    try:
        # Determine appropriate agent based on query
        agent = _determine_best_agent(query)
        system_prompt = AI_AGENTS[agent]["system_prompt"]
        
        # Get relevant documents from vector store
        query_embedding = embedding_model.embed_query(query)
        relevant_docs = vector_store.search(query_embedding, k=5)
        
        # Format context from documents
        context = ""
        for i, doc in enumerate(relevant_docs):
            context += f"\nDocument {i+1} - {doc['source']}:\n{doc['content']}\n"
        
        # Format the prompt with context
        prompt = f"""
        I have a question about a code repository. Here is my question:
        
        {query}
        
        Based on the following relevant files from the repository:
        
        {context}
        
        Please provide a detailed answer.
        """
        
        # Get the model and generate response
        model = ai_models.get_model(model_key)
        
        # Create messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # Get response from model
        response = model.invoke(messages)
        response_text = response.content
        
        return jsonify({
            'success': True,
            'response': response_text,
            'agent': AI_AGENTS[agent]["name"],
            'sources': [doc['source'] for doc in relevant_docs]
        })
        
    except Exception as e:
        print(f"Error in chat: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# ==================
# Helper Functions
# ==================

def _determine_best_agent(query):
    """Determine the best agent based on the query content"""
    query = query.lower()
    
    # Simple keyword matching - in a real app, use embeddings or ML classification
    if any(word in query for word in ["frontend", "ui", "interface", "css", "html", "react", "angular", "vue"]):
        return "fullstack_developer"
    elif any(word in query for word in ["data pipeline", "etl", "database schema", "sql", "nosql"]):
        return "data_engineer"
    elif any(word in query for word in ["machine learning", "model", "prediction", "statistics", "analysis"]):
        return "data_scientist"
    else:
        # Default to software developer
        return "software_developer"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)), debug=True)
