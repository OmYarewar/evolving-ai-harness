// Initialize Icons
lucide.createIcons();

// State
let currentSessionId = 'session_' + Date.now();
let isGenerating = false;

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const btnNewChat = document.getElementById('btn-new-chat');

// Throttled scroll to bottom
let scrollTicking = false;
function scrollToBottom() {
    if (!scrollTicking) {
        window.requestAnimationFrame(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
            scrollTicking = false;
        });
        scrollTicking = true;
    }
}

// Settings Elements
const settingsModal = document.getElementById('settings-modal');
const btnSettings = document.getElementById('btn-settings');
const btnCloseSettings = document.getElementById('btn-close-settings');
const btnSaveSettings = document.getElementById('btn-save-settings');

const inputBaseUrl = document.getElementById('config-base-url');
const inputApiKey = document.getElementById('config-api-key');
const inputModel = document.getElementById('config-model');
const inputSystemPrompt = document.getElementById('config-system-prompt');

// Auto-resize textarea
chatInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

// Chat form submission
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (isGenerating) return;

    const message = chatInput.value.trim();
    if (!message) return;

    // Reset input
    chatInput.value = '';
    chatInput.style.height = 'auto';
    
    // Add User message UI
    appendMessage('user', message);
    
    // Create assistant message container
    const assistantMsgId = 'msg_' + Date.now();
    appendMessage('assistant', '', assistantMsgId);
    
    isGenerating = true;
    chatInput.disabled = true;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                message: message
            })
        });

        if (!response.ok) throw new Error('Network response was not ok');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        let assistantContent = "";
        let msgEl = document.getElementById(assistantMsgId + '-content');

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const dataStr = line.slice(6);
                    if (!dataStr) continue;
                    try {
                        const data = JSON.parse(dataStr);
                        
                        if (data.role === 'assistant') {
                            if (data.content) {
                                assistantContent = data.content; // Use exact latest content rather than appending chunks
                                msgEl.innerHTML = marked.parse(assistantContent);
                            }
                            if (data.tool_calls) {
                                let toolHTML = '<div class="mt-2 space-y-1">';
                                data.tool_calls.forEach(tc => {
                                    toolHTML += `<div class="text-xs bg-slate-800 text-slate-300 p-2 rounded border border-slate-700 font-mono">
                                        <span class="text-indigo-400">Executing:</span> ${tc.function.name}
                                    </div>`;
                                });
                                toolHTML += '</div>';
                                if(!msgEl.innerHTML.includes('Executing:')) {
                                    msgEl.innerHTML += toolHTML;
                                }
                            }
                        } else if (data.role === 'tool') {
                            const toolContent = document.createElement('div');
                            toolContent.className = 'mt-2 text-xs bg-slate-900 text-slate-400 p-2 rounded border border-slate-800 overflow-x-auto font-mono max-h-48 overflow-y-auto';
                            toolContent.textContent = data.content;
                            msgEl.appendChild(toolContent);
                        }

                        scrollToBottom();

                    } catch(e) {
                        console.error('Error parsing JSON from stream:', e, dataStr);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Chat error:', error);
        appendMessage('assistant', 'Error: ' + error.message);
    } finally {
        isGenerating = false;
        chatInput.disabled = false;
        chatInput.focus();
    }
});

function appendMessage(role, content, id = null) {
    if (chatMessages.querySelector('.opacity-50')) {
        chatMessages.innerHTML = ''; // Clear empty state
    }

    const wrapper = document.createElement('div');
    wrapper.className = `flex gap-4 ${role === 'user' ? 'justify-end' : 'justify-start'} max-w-4xl mx-auto w-full`;
    
    const innerId = id ? `id="${id}-content"` : '';
    
    let avatar = '';
    let msgClass = '';

    if (role === 'user') {
        msgClass = 'bg-indigo-600 text-white rounded-2xl rounded-tr-sm';
        wrapper.innerHTML = `
            <div class="flex-1"></div>
            <div class="max-w-[80%] ${msgClass} p-4 shadow-sm">
                <div class="prose prose-invert max-w-none text-sm">${marked.parse(content || ' ')}</div>
            </div>
            <div class="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center shrink-0">
                <i data-lucide="user" class="w-4 h-4 text-white"></i>
            </div>
        `;
    } else {
        msgClass = 'bg-dark-panel border border-dark-border text-slate-200 rounded-2xl rounded-tl-sm';
        wrapper.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center shrink-0 border border-slate-600">
                <i data-lucide="bot" class="w-4 h-4 text-slate-300"></i>
            </div>
            <div class="max-w-[80%] ${msgClass} p-4 shadow-sm w-full">
                <div ${innerId} class="prose prose-invert max-w-none text-sm">${content ? marked.parse(content) : '<span class="animate-pulse flex items-center h-4"><span class="w-2 h-2 bg-slate-500 rounded-full mr-1"></span><span class="w-2 h-2 bg-slate-500 rounded-full mr-1"></span><span class="w-2 h-2 bg-slate-500 rounded-full"></span></span>'}</div>
            </div>
            <div class="flex-1"></div>
        `;
    }
    
    chatMessages.appendChild(wrapper);
    lucide.createIcons();
    scrollToBottom();
}

btnNewChat.addEventListener('click', () => {
    currentSessionId = 'session_' + Date.now();
    chatMessages.innerHTML = `
        <div class="flex justify-center items-center h-full text-slate-500">
            <div class="text-center">
                <i data-lucide="bot" class="w-12 h-12 mx-auto mb-2 opacity-50"></i>
                <p>New Session Started.</p>
            </div>
        </div>
    `;
    lucide.createIcons();
});

// Settings Logic
btnSettings.addEventListener('click', async () => {
    // Fetch current config
    const res = await fetch('/api/config');
    const config = await res.json();
    
    inputBaseUrl.value = config.base_url;
    inputApiKey.value = config.api_key;
    inputModel.value = config.model;
    inputSystemPrompt.value = config.system_prompt;
    
    settingsModal.classList.remove('hidden');
    settingsModal.classList.add('flex');
});

btnCloseSettings.addEventListener('click', () => {
    settingsModal.classList.add('hidden');
    settingsModal.classList.remove('flex');
});

btnSaveSettings.addEventListener('click', async () => {
    btnSaveSettings.textContent = 'Saving...';
    await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            base_url: inputBaseUrl.value,
            api_key: inputApiKey.value,
            model: inputModel.value,
            system_prompt: inputSystemPrompt.value
        })
    });
    btnSaveSettings.textContent = 'Saved!';
    setTimeout(() => {
        btnSaveSettings.textContent = 'Save Configurations';
        btnCloseSettings.click();
    }, 1000);
});
