
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import os
import sys
import json
import uuid
import time
import string
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
# Initialize parallel processor
parallel_processor = ParallelProcessor()

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
    max_workers = int(data.get('max_workers', 4))
    
    if not repo_path:
        return jsonify({'success': False, 'error': 'Repository path is required'})
    
    try:
        # Show progress message
        app.logger.info(f"Processing repository: {repo_path}")
        
        # Validate repository path or URL
        if repo_path.startswith(('http://', 'https://')) and ('github.com' in repo_path):
            # For GitHub URLs, ensure format is correct
            if '/blob/' in repo_path:
                # User is likely pointing to a specific file, extract the repository URL
                repo_parts = repo_path.split('/blob/')
                repo_path = repo_parts[0]
                app.logger.info(f"Modified GitHub URL to repository root: {repo_path}")
        
        # Process repository and get file structure
        try:
            repo_dir, directory_structure, file_contents = repo_handler.process_repository(repo_path)
        except Exception as repo_error:
            app.logger.error(f"Repository processing error: {str(repo_error)}", exc_info=True)
            return jsonify({
                'success': False, 
                'error': f"Failed to process repository: {str(repo_error)}",
                'details': "Please check that the repository URL or path is correct and accessible."
            })
        
        # Set repository in file explorer
        file_explorer.set_repository(repo_dir, directory_structure)
        
        # Store repository information in session
        session['repository'] = {
            'path': repo_dir,
            'structure': json.dumps(str(directory_structure)[:1000] + '...')  # Truncated for session storage
        }
        
        # Process repository files and create embeddings using parallel processing
        def process_file(file_tuple):
            file_path, content = file_tuple
            if not content:
                return None
                
            try:
                relative_path = os.path.relpath(file_path, repo_dir)
                return {
                    "content": content,
                    "source": relative_path
                }
            except Exception as e:
                app.logger.warning(f"Error processing file {file_path}: {str(e)}")
                return None
        
        # Use parallel processing to process files
        app.logger.info(f"Processing {len(file_contents)} files with {max_workers} workers")
        documents = parallel_processor.process_items(
            items=file_contents,
            process_func=process_file,
            max_workers=max_workers
        )
        
        # Filter out None values (already handled in process_items)
        documents = [doc for doc in documents if doc]
        
        # Generate embeddings and add to vector store
        if documents:
            app.logger.info(f"Generating embeddings for {len(documents)} documents")
            
            # Process in batches to avoid memory issues
            batch_size = 20
            processed_batches = 0
            total_batches = (len(documents) + batch_size - 1) // batch_size
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                batch_contents = [doc["content"] for doc in batch]
                
                try:
                    embeddings = embedding_model.embed_documents(batch_contents)
                    vector_store.add_documents(batch, embeddings)
                    processed_batches += 1
                    app.logger.info(f"Processed batch {processed_batches}/{total_batches}")
                except Exception as e:
                    app.logger.error(f"Error processing batch {i//batch_size + 1}: {str(e)}")
                    # Continue with next batch instead of failing completely
            
        # Store a session identifier for the vector store
        if 'vector_store_id' not in session:
            session['vector_store_id'] = str(uuid.uuid4())
            
        return jsonify({
            'success': True, 
            'repo_dir': repo_dir,
            'file_count': len(file_contents),
            'document_count': len(documents),
            'directory': directory_structure
        })
        
    except Exception as e:
        app.logger.error(f"Error processing repository: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': f"Error processing repository: {str(e)}"})

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
    
    # Check if repository is loaded
    if 'repository' not in session:
        return jsonify({'success': False, 'error': 'No repository loaded. Please load a repository first.'})
    
    repo_path = session.get('repository', {}).get('path')
    if not repo_path:
        return jsonify({'success': False, 'error': 'Repository path not found in session'})
        
    try:
        # For security, ensure the requested file is within the repository directory
        # Normalize paths to handle different path formats
        full_path = os.path.normpath(os.path.join(repo_path, file_path))
        normalized_repo_path = os.path.normpath(repo_path)
        
        if not os.path.commonpath([normalized_repo_path, full_path]).startswith(normalized_repo_path):
            return jsonify({'success': False, 'error': 'Access denied: File is outside repository directory'})
            
        # Check if file exists
        if not os.path.exists(full_path):
            return jsonify({'success': False, 'error': f'File not found: {file_path}'})
            
        # Check if it's a directory
        if os.path.isdir(full_path):
            # Handle directory listing
            items = os.listdir(full_path)
            return jsonify({
                'success': True,
                'is_directory': True,
                'path': file_path,
                'items': items
            })
        
        # Get file extension for choosing appropriate reader
        _, extension = os.path.splitext(full_path)
        extension = extension.lower()
        
        # Check file size before reading
        file_size = os.path.getsize(full_path)
        if file_size > 5000000:  # 5MB limit
            return jsonify({
                'success': True,
                'content': f"[File too large to display: {file_size / 1000000:.2f} MB]",
                'path': file_path,
                'extension': extension,
                'size': file_size,
                'last_modified': os.path.getmtime(full_path),
                'is_binary': True,
                'truncated': True
            })
            
        # Import file reader utility
        from utils.file_readers import get_file_reader
        
        # Get appropriate reader based on file extension
        reader = get_file_reader(full_path)
        
        try:
            # Try to read the file
            content = reader(full_path)
        except UnicodeDecodeError:
            # Handle binary files
            return jsonify({
                'success': True,
                'content': "[Binary file content not displayed]",
                'path': file_path,
                'extension': extension,
                'size': file_size,
                'last_modified': os.path.getmtime(full_path),
                'is_binary': True
            })
        except Exception as read_error:
            app.logger.error(f"Error reading file {file_path}: {str(read_error)}", exc_info=True)
            return jsonify({
                'success': False, 
                'error': f"Error reading file: {str(read_error)}"
            })
            
        # Get file metadata
        last_modified = os.path.getmtime(full_path)
        
        # Determine if content should be truncated (for very large text files)
        truncated = False
        if len(content) > 500000:  # If content is more than 500KB
            content = content[:500000] + "\n\n[Content truncated due to size...]"
            truncated = True
        
        return jsonify({
            'success': True,
            'content': content,
            'path': file_path,
            'extension': extension,
            'size': file_size,
            'last_modified': last_modified,
            'is_binary': False,
            'truncated': truncated
        })
    except FileNotFoundError:
        return jsonify({'success': False, 'error': f'File not found: {file_path}'})
    except PermissionError:
        return jsonify({'success': False, 'error': f'Permission denied: {file_path}'})
    except Exception as e:
        app.logger.error(f"Error reading file {file_path}: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': f"Error processing file: {str(e)}"})

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint for chat"""
    data = request.json
    query = data.get('query', '').strip()
    model_key = data.get('model', 'groq/llama-3.1-8b-instant')
    max_tokens = int(data.get('max_tokens', 1000))
    temperature = float(data.get('temperature', 0.7))
    num_context_docs = int(data.get('num_context_docs', 5))
    
    if not query:
        return jsonify({'success': False, 'error': 'Query is required'})
    
    # Check if repository is loaded
    if not vector_store.has_documents():
        return jsonify({
            'success': False, 
            'error': 'No repository data available. Please load a repository first.'
        })
    
    try:
        # Start timing for performance monitoring
        start_time = time.time()
        
        # Determine appropriate agent based on query
        agent = _determine_best_agent(query)
        system_prompt = AI_AGENTS[agent]["system_prompt"]
        
        app.logger.info(f"Processing query with {agent} agent: {query[:50]}...")
        
        # Get relevant documents from vector store with error handling
        try:
            query_embedding = embedding_model.embed_query(query)
            relevant_docs = vector_store.search(query_embedding, k=num_context_docs)
        except Exception as embed_error:
            app.logger.error(f"Error generating embeddings: {str(embed_error)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f"Error finding relevant code: {str(embed_error)}"
            })
        
        if not relevant_docs:
            app.logger.warning("No relevant documents found in vector store")
            return jsonify({
                'success': True,
                'response': "I couldn't find any relevant information in the repository to answer your question. Could you please rephrase or ask about a different topic?",
                'agent': AI_AGENTS[agent]["name"],
                'sources': []
            })
        
        # Format context from documents with better organization and file type handling
        context_parts = []
        source_files = []
        
        for i, doc in enumerate(relevant_docs):
            # Clean file path for presentation
            source = doc['source'].replace('\\', '/')
            source_files.append(source)
            
            # Get file extension to format context appropriately
            _, file_ext = os.path.splitext(source)
            file_ext = file_ext.lower()
            
            # Format content based on file type
            content = doc['content']
            
            # Add document to context with better formatting
            context_parts.append(f"FILE {i+1}: {source}\n\n```{file_ext[1:] if file_ext else ''}\n{content}\n```\n")
        
        context = "\n".join(context_parts)
        
        # Format the prompt with context and improved instructions
        prompt = f"""
I have a question about a code repository. Here is my question:

{query}

I'll provide context from relevant files in the repository:

{context}

Based on ONLY the information provided in these files:
1. Answer the question directly and concisely
2. If the answer can't be determined from the provided files, clearly state that
3. Reference specific code and files when explaining your reasoning
4. If showing code examples, ensure they are accurate and relevant
5. Use markdown formatting in your response to improve readability
"""
        
        # Get the model and generate response with error handling
        try:
            app.logger.info(f"Using model: {model_key}")
            model = ai_models.get_model(model_key)
            
            # Create messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            # Get response from model with additional parameters
            response = model.invoke(
                messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            response_text = response.content
            
        except ValueError as model_error:
            app.logger.error(f"Model error: {str(model_error)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f"Error with AI model: {str(model_error)}"
            })
        except Exception as model_error:
            app.logger.error(f"Unexpected model error: {str(model_error)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f"An error occurred while processing your request: {str(model_error)}"
            })
        
        # Calculate processing time
        processing_time = time.time() - start_time
        app.logger.info(f"Query processed in {processing_time:.2f} seconds")
        
        # Ensure the response isn't empty
        if not response_text or response_text.strip() == "":
            return jsonify({
                'success': False,
                'error': "The AI model returned an empty response. Please try again or adjust your query."
            })
        
        return jsonify({
            'success': True,
            'response': response_text,
            'agent': AI_AGENTS[agent]["name"],
            'sources': source_files,
            'processing_time': f"{processing_time:.2f}s"
        })
        
    except ValueError as e:
        app.logger.warning(f"Value error in chat: {str(e)}")
        return jsonify({'success': False, 'error': f"Value error: {str(e)}"})
    except Exception as e:
        app.logger.error(f"Error in chat: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': f"An error occurred: {str(e)}"})

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

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)), debug=True)
