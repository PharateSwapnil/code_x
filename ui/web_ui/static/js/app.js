
// DOM Elements
const repoPathInput = document.getElementById('repoPath');
const processRepoBtn = document.getElementById('processRepoBtn');
const modelSelect = document.getElementById('modelSelect');
const maxTokensSlider = document.getElementById('maxTokens');
const tokenValueDisplay = document.getElementById('tokenValue');
const directorySelect = document.getElementById('directorySelect');
const fileTree = document.getElementById('fileTree');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const messageContainer = document.getElementById('messageContainer');
const fileArea = document.getElementById('fileArea');
const chatArea = document.getElementById('chatArea');
const fileName = document.getElementById('fileName');
const fileContent = document.getElementById('fileContent').querySelector('code');
const backToChat = document.getElementById('backToChat');
const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
const loadingMessage = document.getElementById('loadingMessage');
const loadingProgress = document.getElementById('loadingProgress');

// State
let directoryStructure = null;
let currentRepository = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Update token value display when slider changes
    maxTokensSlider.addEventListener('input', function() {
        tokenValueDisplay.textContent = this.value;
    });
    
    // Process repository button
    processRepoBtn.addEventListener('click', processRepository);
    
    // Send message button
    sendBtn.addEventListener('click', sendMessage);
    
    // Enter key to send message
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Back to chat button
    backToChat.addEventListener('click', function() {
        fileArea.classList.add('d-none');
        chatArea.classList.remove('d-none');
    });
    
    // Directory select change
    directorySelect.addEventListener('change', function() {
        renderFileTree(this.value);
    });
    
    // Load available models
    loadModels();
});

// Load models from API
function loadModels() {
    fetch('/api/models')
        .then(response => response.json())
        .then(data => {
            modelSelect.innerHTML = '';
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                modelSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading models:', error);
        });
}

// Process repository
function processRepository() {
    const repoPath = repoPathInput.value.trim();
    if (!repoPath) {
        alert('Please enter a repository path');
        return;
    }
    
    // Show loading modal
    loadingMessage.textContent = 'Processing repository...';
    loadingProgress.style.width = '0%';
    loadingModal.show();
    
    // Simulate progress (since we can't get real-time updates easily)
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += 5;
        if (progress > 95) {
            clearInterval(progressInterval);
        }
        loadingProgress.style.width = `${progress}%`;
    }, 500);
    
    // Call API to process repository
    fetch('/api/process_repo', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ repo_path: repoPath })
    })
    .then(response => response.json())
    .then(data => {
        clearInterval(progressInterval);
        loadingProgress.style.width = '100%';
        
        if (data.error) {
            alert(`Error: ${data.error}`);
            loadingModal.hide();
            return;
        }
        
        // Store the repository structure
        directoryStructure = data.structure;
        currentRepository = repoPath;
        
        // Populate directory dropdown
        populateDirectoryDropdown();
        
        // Enable chat input
        chatInput.disabled = false;
        sendBtn.disabled = false;
        
        // Add system message
        addMessage('assistant', `Repository processed successfully. You can now ask questions about the code.`);
        
        // Hide loading modal
        setTimeout(() => {
            loadingModal.hide();
        }, 500);
    })
    .catch(error => {
        clearInterval(progressInterval);
        console.error('Error processing repository:', error);
        alert('Error processing repository. Please try again.');
        loadingModal.hide();
    });
}

// Populate directory dropdown
function populateDirectoryDropdown() {
    directorySelect.innerHTML = '';
    const directories = getAllDirectoriesFromStructure(directoryStructure);
    
    // Add the root directory
    const rootOption = document.createElement('option');
    rootOption.value = '';
    rootOption.textContent = '/ (root)';
    directorySelect.appendChild(rootOption);
    
    // Add all subdirectories
    directories.forEach(dir => {
        const option = document.createElement('option');
        option.value = dir;
        option.textContent = dir;
        directorySelect.appendChild(option);
    });
    
    // Render the file tree for the root
    renderFileTree('');
}

// Get all directories from structure
function getAllDirectoriesFromStructure(structure, prefix = '') {
    let dirs = [];
    for (const key in structure) {
        if (typeof structure[key] === 'object') {
            const path = prefix ? `${prefix}/${key}` : key;
            dirs.push(path);
            dirs = dirs.concat(getAllDirectoriesFromStructure(structure[key], path));
        }
    }
    return dirs;
}

// Render file tree for a specific directory
function renderFileTree(dirPath) {
    fileTree.innerHTML = '';
    
    // Get the structure for the selected directory
    let currentStructure = directoryStructure;
    if (dirPath) {
        const parts = dirPath.split('/');
        for (const part of parts) {
            currentStructure = currentStructure[part];
        }
    }
    
    // Render the structure
    renderStructureNode(currentStructure, dirPath, fileTree);
}

// Render a node in the structure
function renderStructureNode(node, path, parentElement) {
    // Sort entries - directories first, then files
    const entries = Object.entries(node);
    const sortedEntries = entries.sort((a, b) => {
        const aIsDir = typeof a[1] === 'object';
        const bIsDir = typeof b[1] === 'object';
        
        if (aIsDir && !bIsDir) return -1;
        if (!aIsDir && bIsDir) return 1;
        return a[0].localeCompare(b[0]);
    });
    
    sortedEntries.forEach(([key, value]) => {
        const itemPath = path ? `${path}/${key}` : key;
        const isDirectory = typeof value === 'object';
        
        const item = document.createElement('div');
        item.textContent = isDirectory ? `📂 ${key}` : `📄 ${key}`;
        item.className = isDirectory ? 'folder-item' : 'file-item';
        
        if (isDirectory) {
            // Directory - add click handler to expand/collapse
            const contentsDiv = document.createElement('div');
            contentsDiv.className = 'folder-contents d-none';
            
            item.addEventListener('click', function(event) {
                event.stopPropagation();
                contentsDiv.classList.toggle('d-none');
                if (contentsDiv.children.length === 0) {
                    // Lazy load contents
                    renderStructureNode(value, itemPath, contentsDiv);
                }
            });
            
            parentElement.appendChild(item);
            parentElement.appendChild(contentsDiv);
        } else {
            // File - add click handler to view file
            item.addEventListener('click', function() {
                loadFile(`${currentRepository}/${itemPath}`);
            });
            
            parentElement.appendChild(item);
        }
    });
}

// Load file content
function loadFile(filePath) {
    fetch('/api/get_file', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file_path: filePath })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }
        
        // Display the file
        fileName.textContent = data.file_name;
        fileContent.textContent = data.content;
        
        // Apply syntax highlighting
        hljs.highlightElement(fileContent);
        
        // Show file area, hide chat area
        chatArea.classList.add('d-none');
        fileArea.classList.remove('d-none');
    })
    .catch(error => {
        console.error('Error loading file:', error);
        alert('Error loading file. Please try again.');
    });
}

// Send message
function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addMessage('user', message);
    
    // Clear input
    chatInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send to API
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: message,
            model: modelSelect.value,
            max_tokens: parseInt(maxTokensSlider.value)
        })
    })
    .then(response => response.json())
    .then(data => {
        // Remove typing indicator
        removeTypingIndicator();
        
        if (data.error) {
            addMessage('assistant', `Error: ${data.error}`);
            return;
        }
        
        // Add response to chat
        addMessage('assistant', data.response);
    })
    .catch(error => {
        console.error('Error sending message:', error);
        removeTypingIndicator();
        addMessage('assistant', 'Sorry, there was an error processing your request.');
    });
}

// Add message to chat
function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = role === 'user' ? 'user-message' : 'assistant-message';
    
    const contentP = document.createElement('p');
    contentP.textContent = content;
    messageDiv.appendChild(contentP);
    
    const timestampP = document.createElement('p');
    timestampP.className = 'message-timestamp';
    const now = new Date();
    timestampP.textContent = now.toLocaleTimeString();
    messageDiv.appendChild(timestampP);
    
    messageContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    messageContainer.scrollTop = messageContainer.scrollHeight;
}

// Show typing indicator
function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'assistant-message typing-indicator';
    typingDiv.id = 'typingIndicator';
    
    const typingContent = document.createElement('p');
    typingContent.textContent = 'Thinking...';
    
    typingDiv.appendChild(typingContent);
    messageContainer.appendChild(typingDiv);
    
    // Scroll to bottom
    messageContainer.scrollTop = messageContainer.scrollHeight;
}

// Remove typing indicator
function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}
