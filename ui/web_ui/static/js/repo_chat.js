
document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI elements
    const repoPathInput = document.getElementById('repo-path');
    const processRepoBtn = document.getElementById('process-repo-btn');
    const modelSelector = document.getElementById('model-selector');
    const maxTokensSlider = document.getElementById('max-tokens');
    const tokenValueDisplay = document.getElementById('token-value');
    const directorySelector = document.getElementById('directory-selector');
    const fileTree = document.getElementById('file-tree');
    const fileViewer = document.getElementById('file-viewer');
    const fileName = document.getElementById('file-name');
    const fileContent = document.getElementById('file-content');
    const closeFileBtn = document.getElementById('close-file-btn');
    const chatInterface = document.getElementById('chat-interface');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendMessageBtn = document.getElementById('send-message-btn');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingMessage = document.getElementById('loading-message');
    const themeSwitch = document.getElementById('theme-switch');
    
    // Theme toggle functionality
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.body.classList.add('dark-theme');
        themeSwitch.checked = true;
    }
    
    themeSwitch.addEventListener('change', function() {
        if (this.checked) {
            document.body.classList.add('dark-theme');
            localStorage.setItem('theme', 'dark');
        } else {
            document.body.classList.remove('dark-theme');
            localStorage.setItem('theme', 'light');
        }
    });
    
    // Update token value display when slider moves
    maxTokensSlider.addEventListener('input', function() {
        tokenValueDisplay.textContent = this.value;
    });
    
    // Process repository button click
    processRepoBtn.addEventListener('click', function() {
        const repoPath = repoPathInput.value.trim();
        
        if (!repoPath) {
            alert('Please enter a repository URL or path');
            return;
        }
        
        // Show loading overlay
        loadingOverlay.classList.remove('hidden');
        loadingMessage.textContent = 'Processing repository...';
        
        // Process repository
        fetch('/process_repository', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `repo_path=${encodeURIComponent(repoPath)}`
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading overlay
            loadingOverlay.classList.add('hidden');
            
            if (data.success) {
                // Enable chat input
                sendMessageBtn.disabled = false;
                
                // Update UI with success message
                addSystemMessage(`Repository processed successfully. You can now ask questions about the code.`);
                
                // Update file tree
                updateFileTree(data.directory);
                
                // Update directory selector
                updateDirectorySelector(data.directory);
            } else {
                // Show error message
                alert(`Error: ${data.message}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            loadingOverlay.classList.add('hidden');
            alert('An error occurred while processing the repository.');
        });
    });
    
    // Close file button click
    closeFileBtn.addEventListener('click', function() {
        fileViewer.classList.add('hidden');
        chatInterface.classList.remove('hidden');
    });
    
    // Send message button click
    sendMessageBtn.addEventListener('click', function() {
        sendMessage();
    });
    
    // Allow Enter key to send message (Shift+Enter for new line)
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Function to send a message
    function sendMessage() {
        const message = chatInput.value.trim();
        
        if (!message) {
            return;
        }
        
        // Add user message to chat
        addUserMessage(message);
        
        // Clear input
        chatInput.value = '';
        
        // Disable send button while waiting for response
        sendMessageBtn.disabled = true;
        
        // Show thinking message
        addThinkingMessage();
        
        // Get selected model and max tokens
        const selectedModel = modelSelector.value;
        const maxTokens = maxTokensSlider.value;
        
        // Send message to server
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `message=${encodeURIComponent(message)}&model=${encodeURIComponent(selectedModel)}&max_tokens=${encodeURIComponent(maxTokens)}`
        })
        .then(response => response.json())
        .then(data => {
            // Remove thinking message
            removeThinkingMessage();
            
            if (data.success) {
                // Add AI response to chat
                addAssistantMessage(data.response);
            } else {
                // Show error message
                addSystemMessage(`Error: ${data.message}`);
            }
            
            // Re-enable send button
            sendMessageBtn.disabled = false;
        })
        .catch(error => {
            console.error('Error:', error);
            removeThinkingMessage();
            addSystemMessage('An error occurred while processing your message.');
            sendMessageBtn.disabled = false;
        });
    }
    
    // Add a user message to the chat
    function addUserMessage(content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message user-message';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-user"></i>
            </div>
            <div class="message-content">
                <p>${formatMessageContent(content)}</p>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }
    
    // Add an assistant message to the chat
    function addAssistantMessage(content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message assistant-message';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <p>${formatMessageContent(content)}</p>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }
    
    // Add a system message to the chat
    function addSystemMessage(content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message system-message';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-info-circle"></i>
            </div>
            <div class="message-content">
                <p>${content}</p>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }
    
    // Add a thinking message
    function addThinkingMessage() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message assistant-message thinking-message';
        messageDiv.id = 'thinking-message';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <p>Thinking...</p>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }
    
    // Remove the thinking message
    function removeThinkingMessage() {
        const thinkingMessage = document.getElementById('thinking-message');
        if (thinkingMessage) {
            thinkingMessage.remove();
        }
    }
    
    // Format message content with code blocks
    function formatMessageContent(content) {
        // Basic markdown-like formatting
        // Replace code blocks
        content = content.replace(/```([\s\S]*?)```/g, '<pre>$1</pre>');
        
        // Replace line breaks with <br>
        content = content.replace(/\n/g, '<br>');
        
        return content;
    }
    
    // Update the file tree with the directory structure
    function updateFileTree(directory) {
        // Clear existing content
        fileTree.innerHTML = '';
        
        // Create tree nodes
        const tree = document.createElement('div');
        tree.className = 'file-tree-content';
        
        // Build tree recursively
        buildFileTree(tree, directory, '');
        
        fileTree.appendChild(tree);
    }
    
    // Build the file tree nodes recursively
    function buildFileTree(parentElement, directory, currentPath) {
        for (const [name, value] of Object.entries(directory)) {
            const itemPath = currentPath ? `${currentPath}/${name}` : name;
            const itemDiv = document.createElement('div');
            
            if (value === null) {
                // It's a file
                itemDiv.className = 'file-item';
                itemDiv.innerHTML = `<i class="fas fa-file"></i> ${name}`;
                itemDiv.addEventListener('click', function() {
                    loadFileContent(itemPath);
                });
            } else {
                // It's a directory
                itemDiv.className = 'folder-item';
                
                const folderHeader = document.createElement('div');
                folderHeader.className = 'file-item folder-header';
                folderHeader.innerHTML = `<i class="fas fa-folder"></i> ${name}`;
                
                const folderContent = document.createElement('div');
                folderContent.className = 'folder-content';
                folderContent.style.paddingLeft = '15px';
                folderContent.style.display = 'none';
                
                folderHeader.addEventListener('click', function(e) {
                    e.stopPropagation();
                    
                    // Toggle folder icon
                    const icon = this.querySelector('i');
                    if (icon.classList.contains('fa-folder')) {
                        icon.classList.remove('fa-folder');
                        icon.classList.add('fa-folder-open');
                    } else {
                        icon.classList.remove('fa-folder-open');
                        icon.classList.add('fa-folder');
                    }
                    
                    // Toggle folder content visibility
                    folderContent.style.display = folderContent.style.display === 'none' ? 'block' : 'none';
                });
                
                itemDiv.appendChild(folderHeader);
                itemDiv.appendChild(folderContent);
                
                // Recursively build the tree for this directory
                buildFileTree(folderContent, value, itemPath);
            }
            
            parentElement.appendChild(itemDiv);
        }
    }
    
    // Update directory selector
    function updateDirectorySelector(directory) {
        // Clear existing options
        directorySelector.innerHTML = '';
        
        // Add root option
        const rootOption = document.createElement('option');
        rootOption.value = '';
        rootOption.textContent = 'Root directory';
        directorySelector.appendChild(rootOption);
        
        // Add options for each directory
        function addDirectoryOptions(directory, path, depth) {
            for (const [name, value] of Object.entries(directory)) {
                if (value !== null) {  // It's a directory
                    const dirPath = path ? `${path}/${name}` : name;
                    const option = document.createElement('option');
                    option.value = dirPath;
                    option.textContent = '  '.repeat(depth) + name;
                    directorySelector.appendChild(option);
                    
                    // Recursively add subdirectories
                    addDirectoryOptions(value, dirPath, depth + 1);
                }
            }
        }
        
        addDirectoryOptions(directory, '', 0);
        
        // Add change event to update file tree view
        directorySelector.addEventListener('change', function() {
            const selectedPath = this.value;
            
            // TODO: Update file tree to focus on selected directory
            // This would require keeping track of the full directory structure
        });
    }
    
    // Load file content
    function loadFileContent(filePath) {
        // Show loading overlay
        loadingOverlay.classList.remove('hidden');
        loadingMessage.textContent = 'Loading file...';
        
        fetch('/get_file_content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `file_path=${encodeURIComponent(filePath)}`
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading overlay
            loadingOverlay.classList.add('hidden');
            
            if (data.success) {
                // Update file viewer
                fileName.textContent = data.file_name;
                fileContent.textContent = data.content;
                
                // Show file viewer, hide chat interface
                fileViewer.classList.remove('hidden');
                chatInterface.classList.add('hidden');
            } else {
                alert(`Error: ${data.message}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            loadingOverlay.classList.add('hidden');
            alert('An error occurred while loading the file.');
        });
    }
    
    // Scroll chat to bottom
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
