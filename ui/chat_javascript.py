#!/usr/bin/env python3

# Chat JavaScript Component with all functionality
CHAT_JAVASCRIPT = '''
<script>
let currentThreadId = null;
let isTyping = false;
let sendingMessage = false;

// Auto-resize textarea
const textarea = document.getElementById('chat-input');
textarea.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 150) + 'px';
});

// Handle Enter key (Send on Enter, new line on Shift+Enter)
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        console.log('🔥 ENTER KEY PRESSED - calling sendMessage()');
        event.preventDefault();
        event.stopPropagation();
        sendMessage();
        return false;
    }
}

// Toggle memory search (always enabled now)
function toggleMemorySearch() {
    const toggleBtn = document.getElementById('memory-toggle');
    const toggleText = document.getElementById('memory-toggle-text');
    toggleBtn.classList.add('active');
    toggleText.textContent = '✅ Memory Search ALWAYS ON';
}

// Show/hide searching memories indicator
function showSearchingMemories() {
    document.getElementById('searching-memories-indicator').classList.add('show');
}
function hideSearchingMemories() {
    document.getElementById('searching-memories-indicator').classList.remove('show');
}

// Send message function
async function sendMessage() {
    console.log('🔥 === SENDMESSAGE FUNCTION CALLED ===');
    
    const input = document.getElementById('chat-input');
    const sendButton = document.querySelector('.send-button');
    const message = input.value.trim();
    
    if (!message || isTyping || sendingMessage) {
        return;
    }
    
    // Set flags and disable UI
    isTyping = true;
    sendingMessage = true;
    input.disabled = true;
    sendButton.disabled = true;
    sendButton.style.opacity = '0.5';
    
    // Generate unique request ID
    const requestId = 'req_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    
    // Clear input and add user message
    input.value = '';
    input.style.height = 'auto';
    addMessage(message, 'user');
    
    // Show indicators
    showTypingIndicator();
    showSearchingMemories();
    
    try {
        const response = await fetch('/send_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                thread_id: currentThreadId,
                use_memory_search: true,
                request_id: requestId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentThreadId = data.thread_id;
            updateThreadTitle();
            
            if (data.memory_context && data.memory_context.length > 0) {
                addMessageWithMemoriesInjected(data.response, 'assistant', data.memory_context);
                
                // Trigger memory animation
                const activatedMemoryIds = data.memory_context.map(ctx => ctx.memory.id);
                setTimeout(() => {
                    if (memoryNetwork && networkData.nodes.length > 0) {
                        animateMemoryActivation(activatedMemoryIds);
                    }
                }, 200);
            } else {
                addMessage(data.response, 'assistant');
            }
        } else if (response.status !== 409) {
            addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
        }
    } catch (error) {
        addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
    } finally {
        hideTypingIndicator();
        hideSearchingMemories();
        
        // Re-enable UI
        input.disabled = false;
        sendButton.disabled = false;
        sendButton.style.opacity = '1';
        sendButton.style.cursor = 'pointer';
        
        // Reset flags
        isTyping = false;
        sendingMessage = false;
    }
}

// Add message to chat
function addMessage(content, sender) {
    const messagesContainer = document.getElementById('chat-messages');
    const emptyState = messagesContainer.querySelector('.empty-state');
    
    if (emptyState) {
        emptyState.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    
    messageDiv.innerHTML = `
        <p class="message-content">${content}</p>
        <div class="message-time">${timeString}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Add message with memories injected info
function addMessageWithMemoriesInjected(content, sender, memoryContext) {
    const messagesContainer = document.getElementById('chat-messages');
    const emptyState = messagesContainer.querySelector('.empty-state');
    
    if (emptyState) {
        emptyState.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    
    // Build memories injected HTML
    let memoriesHtml = '<div class="memories-injected-box">';
    memoriesHtml += '<h4>🧠 Memories Injected:</h4>';
    if (memoryContext && memoryContext.length > 0) {
        memoryContext.forEach(memory => {
            memoriesHtml += `<div class="memories-injected-item">${memory.memory.content}<span class="memories-injected-score">(Score: ${memory.relevance_score.toFixed(2)})</span></div>`;
        });
    } else {
        memoriesHtml += '<div class="memories-injected-item">No relevant memories were injected for this prompt.</div>';
    }
    memoriesHtml += '</div>';
    
    messageDiv.innerHTML = `
        <p class="message-content">${content}</p>
        ${memoriesHtml}
        <div class="message-time">${timeString}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Show/hide typing indicator
function showTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    indicator.classList.add('show');
    indicator.scrollIntoView({ behavior: 'smooth' });
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    indicator.classList.remove('show');
}

// Thread management functions
async function newThread() {
    if (currentThreadId) {
        const messagesContainer = document.getElementById('chat-messages');
        const messages = messagesContainer.querySelectorAll('.message');
        
        if (messages.length > 2) {
            const extractMemories = confirm('Extract memories from current conversation before starting new thread?');
            if (extractMemories) {
                await endThread();
                return;
            }
        }
    }
    
    currentThreadId = null;
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML = '<div class="empty-state">Start a new conversation by typing a message below...</div>';
    updateThreadTitle();
}

function clearThread() {
    if (confirm('Are you sure you want to clear this conversation?')) {
        newThread();
    }
}

async function endThread() {
    if (!currentThreadId) {
        alert('No active conversation to end.');
        return;
    }

    if (!confirm('End this conversation and extract memories for future chats?')) {
        return;
    }
    
    try {
        showTypingIndicator();
        
        const response = await fetch('/end_thread', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ thread_id: currentThreadId })
        });

        const data = await response.json();

        if (data.success) {
            const oldThreadId = currentThreadId;
            currentThreadId = null;
            
            if (data.extracted_memories && data.extracted_memories.length > 0) {
                const memoriesText = data.extracted_memories.join('\\n• ');
                addMessage(`🧠 ${data.message}\\n\\n• ${memoriesText}\\n\\nThese will inform future conversations.`, 'assistant');
            } else {
                addMessage('🧠 Conversation ended! No new memories were extracted from this conversation.', 'assistant');
            }
            
            // Refresh memory network
            setTimeout(() => loadMemoryNetwork(), 1000);
            
            // Start new conversation
            setTimeout(() => {
                const messagesContainer = document.getElementById('chat-messages');
                messagesContainer.innerHTML = '<div class="empty-state">Start a new conversation by typing a message below...</div>';
                updateThreadTitle();
            }, 2500);
        } else {
            addMessage(`❌ ${data.error || 'Failed to end conversation and extract memories.'}`, 'assistant');
        }
    } catch (error) {
        addMessage('❌ Error ending conversation. Please try again.', 'assistant');
    } finally {
        hideTypingIndicator();
    }
}

function updateThreadTitle() {
    const titleElement = document.getElementById('thread-title');
    if (currentThreadId) {
        titleElement.textContent = `Conversation ${currentThreadId.substring(0, 8)}...`;
    } else {
        titleElement.textContent = 'New Conversation';
    }
}

// Initialize
updateThreadTitle();

// Check memory system availability
fetch('/check_memory_availability')
    .then(response => response.json())
    .then(data => {
        if (!data.available) {
            const toggleBtn = document.getElementById('memory-toggle');
            toggleBtn.classList.add('disabled');
            toggleBtn.disabled = true;
            document.getElementById('memory-toggle-text').textContent = '❌ Memory System Unavailable';
        }
    });
</script>
''' 