// Global variables
let network = null;
let memoryNetworkDiv = null;
let currentThreshold = 0.35;
let isMapMode = false;

// Session memory store for real-time updates
let sessionMemories = [];
let sessionMemoryIds = new Set();
let newMemoryPollingInterval = null;
let savedNodePositions = {};

let suppressMemoryNotifications = false;

// --- Render Memories List ---
async function renderMemories() {
    try {
        console.log('🔍 Loading memories...');
        const container = document.getElementById('memories-container');
        
        // Direct fetch approach that works
        const response = await fetch('http://localhost:5001/memories');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const memories = await response.json();
        console.log(`📊 Loaded ${memories.length} memories`);
        
        if (!memories || memories.length === 0) {
            container.innerHTML = '<p class="text-gray-400">No memories found.</p>';
            return;
        }

        // Use the working approach from test.html but with proper styling
        container.innerHTML = memories.map((memory, index) => `
            <div class="memory-card" data-memory-id="${memory.id}">
                <p><strong>${index + 1}.</strong> ${memory.content}</p>
                <div class="flex justify-between items-center mt-3">
                    <span class="memory-score">Score: ${memory.score.toFixed(2)}</span>
                    <span class="text-gray-400 text-sm">${new Date(memory.timestamp).toLocaleDateString()}</span>
                    <button class="delete-memory-btn" onclick="deleteMemory('${memory.id}')">Delete</button>
                </div>
            </div>
        `).join('');
        
        console.log('✅ Memories rendered successfully');
    } catch (error) {
        console.error('Error loading memories:', error);
        const container = document.getElementById('memories-container');
        container.innerHTML = `<p class="text-red-400">Failed to load memories: ${error.message}</p>`;
    }
}

// --- Delete Memory ---
async function deleteMemory(memoryId) {
    if (!confirm('Are you sure you want to delete this memory?')) return;
    
    try {
        const result = await apiCall(`/memories/${memoryId}`, { method: 'DELETE' });
        if (result && result.message) {
            await renderMemories(); // Refresh the list
            console.log('Memory deleted successfully');
        } else {
            alert('Failed to delete memory.');
        }
    } catch (error) {
        console.error('Error deleting memory:', error);
        alert('Failed to delete memory.');
    }
}

// --- Map Mode Toggle ---
function toggleMapMode() {
    isMapMode = !isMapMode;
    const listView = document.getElementById('list-mode-view');
    const mapView = document.getElementById('map-mode-view');
    const toggle = document.getElementById('map-mode-toggle');
    const toggleSlider = toggle.nextElementSibling.firstElementChild;

    if (isMapMode) {
        listView.style.display = 'none';
        mapView.style.display = 'block';
        toggle.checked = true;
        toggleSlider.style.transform = 'translateX(100%)';
        
        // Render the network when entering map mode
        if (!memoryNetworkDiv) {
            memoryNetworkDiv = document.getElementById('memory-network');
        }
        renderMemoryNetwork();
    } else {
        listView.style.display = 'block';
        mapView.style.display = 'none';
        toggle.checked = false;
        toggleSlider.style.transform = 'translateX(0%)';
        
        // Destroy network when leaving map mode to free memory
        if (network) {
            network.destroy();
            network = null;
        }
    }
}

// --- Search Functionality ---
function setupSearch() {
    const searchInput = document.getElementById('search-input');
    let searchTimeout;

    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(async () => {
            const query = e.target.value.trim();
            if (query) {
                await searchMemories(query);
            } else {
                await renderMemories(); // Show all memories if search is empty
            }
        }, 300); // Debounce search
    });
}

// --- Search Memories ---
async function searchMemories(query) {
    try {
        const results = await apiCall(`/search?q=${encodeURIComponent(query)}`);
        const container = document.getElementById('memories-container');
        
        if (!results || !Array.isArray(results) || results.length === 0) {
            container.innerHTML = '<p class="text-gray-400">No memories found for your search.</p>';
            return;
        }

        container.innerHTML = results.map(result => {
            // Search results have a different format: {memory: {...}, relevance_score: ...}
            const memory = result.memory || result;
            return `
                <div class="memory-card search-result" data-memory-id="${memory.id}">
                    <p>${memory.content}</p>
                    <div class="flex justify-between items-center mt-3">
                        <span class="memory-score">Score: ${memory.score.toFixed(2)}</span>
                        ${result.relevance_score ? `<span class="relevance-score">Relevance: ${result.relevance_score.toFixed(2)}</span>` : ''}
                        <span class="text-gray-400 text-sm">${memory.created}</span>
                        <button class="delete-memory-btn" onclick="deleteMemory('${memory.id}')">Delete</button>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Error searching memories:', error);
        document.getElementById('memories-container').innerHTML = '<p class="text-red-400">Search failed.</p>';
    }
}

// --- Settings Handlers ---
function setupSettings() {
    // Threshold slider
    const thresholdSlider = document.getElementById('threshold-slider');
    const thresholdValue = document.getElementById('threshold-value');
    let thresholdDebounce;
    if (thresholdSlider && thresholdValue) {
        thresholdSlider.addEventListener('input', (e) => {
            // Snap to nearest 0.05
            let snapped = Math.round(parseFloat(e.target.value) / 0.05) * 0.05;
            snapped = Math.max(0, Math.min(1, snapped));
            thresholdSlider.value = snapped;
            currentThreshold = snapped;
            thresholdValue.textContent = currentThreshold.toFixed(2);
            // Debounce re-render
            if (isMapMode && memoryNetworkDiv) {
                suppressMemoryNotifications = true;
                clearTimeout(thresholdDebounce);
                thresholdDebounce = setTimeout(() => {
                    renderMemoryNetwork().then(() => {
                        suppressMemoryNotifications = false;
                    });
                }, 100);
            }
        });
    }

    // Model toggle (placeholder for future implementation)
    const modelToggle = document.getElementById('model-toggle');
    if (modelToggle) {
        modelToggle.addEventListener('change', async (e) => {
            const useTransformer = e.target.checked;
            // TODO: Implement model switching API call
            console.log('Model toggle:', useTransformer ? 'transformer' : 'tfidf');
        });
    }
}

// --- Show Memory Modal (placeholder) ---
function showMemoryModal(node) {
    // Simple alert for now - you can enhance this with a proper modal
    alert(`Memory: ${node.title}\nScore: ${node.score}`);
}

// --- Show Error Message ---
function showErrorMessage(message) {
    console.error(message);
    // You can enhance this with a toast notification system
}

async function renderMemoryNetwork() {
    try {
        const data = await apiCall(`/memory-network?threshold=${currentThreshold}`);
        if (!data || !data.nodes || !data.edges) {
            console.error('Invalid network data received');
            return;
        }

        // Clear previous network
        if (network) {
            network.destroy();
        }

        // Create nodes with better styling
        const nodes = new vis.DataSet(data.nodes.map(node => {
            const baseSize = 60; // Larger base size
            const scoreMultiplier = Math.max(1, node.score * 20); // Better scaling
            const nodeSize = Math.min(baseSize + scoreMultiplier, 150); // Cap maximum size
            
            return {
                id: node.id,
                label: node.label.length > 40 ? node.label.substring(0, 40) + '...' : node.label,
                title: `${node.label}\n\nScore: ${node.score.toFixed(2)}`, // Enhanced tooltip
                size: nodeSize,
                color: {
                    background: '#8b5cf6', // Slightly darker purple
                    border: '#a855f7',
                    borderWidth: 3,
                    highlight: { 
                        background: '#a78bfa', 
                        border: '#c084fc',
                        borderWidth: 4
                    },
                    hover: {
                        background: '#a78bfa',
                        border: '#c084fc',
                        borderWidth: 4
                    }
                },
                font: { 
                    color: '#ffffff', 
                    size: Math.max(14, Math.min(18, 12 + node.score * 2)), // Dynamic font size
                    face: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
                    strokeWidth: 2,
                    strokeColor: '#000000',
                    multi: 'md',
                    bold: true
                },
                shadow: {
                    enabled: true,
                    color: 'rgba(139, 92, 246, 0.3)',
                    size: 15,
                    x: 0,
                    y: 0
                },
                score: node.score,
                margin: 10,
                widthConstraint: { minimum: 100, maximum: 200 }
            };
        }));

        // Enhanced edges with better visibility
        const edges = new vis.DataSet(data.edges.map((edge, index) => {
            const edgeWidth = Math.max(2, edge.value * 8); // Better edge scaling
            const opacity = Math.max(0.4, edge.value); // Dynamic opacity
            
            return {
                id: `edge_${index}`, // Add unique ID for edges
                from: edge.from,
                to: edge.to,
                value: edge.value,
                color: {
                    color: `rgba(168, 85, 247, ${opacity})`,
                    highlight: `rgba(192, 132, 252, ${Math.min(1, opacity + 0.3)})`,
                    hover: `rgba(192, 132, 252, ${Math.min(1, opacity + 0.3)})`
                },
                width: edgeWidth,
                smooth: { 
                    type: 'continuous',
                    roundness: 0.2
                },
                shadow: {
                    enabled: true,
                    color: 'rgba(168, 85, 247, 0.2)',
                    size: 8
                },
                physics: true,
                length: 200 + (1 - edge.value) * 300 // Stronger connections = shorter length
            };
        }));

        // Enhanced network configuration
        const options = {
            nodes: {
                shape: 'dot',
                borderWidth: 3,
                scaling: { 
                    min: 60, 
                    max: 150,
                    label: { 
                        enabled: true, 
                        min: 14, 
                        max: 20,
                        maxVisible: 20,
                        drawThreshold: 8
                    }
                },
                shadow: {
                    enabled: true,
                    color: 'rgba(139, 92, 246, 0.3)',
                    size: 15,
                    x: 0,
                    y: 0
                },
                margin: {
                    top: 15,
                    right: 15,
                    bottom: 15,
                    left: 15
                }
            },
            edges: {
                shadow: {
                    enabled: true,
                    color: 'rgba(168, 85, 247, 0.2)',
                    size: 8
                },
                smooth: { 
                    type: 'continuous',
                    roundness: 0.2
                },
                scaling: {
                    min: 2,
                    max: 12
                }
            },
            physics: {
                enabled: true,
                solver: 'forceAtlas2Based',
                forceAtlas2Based: {
                    gravitationalConstant: -120,
                    centralGravity: 0.01,
                    springLength: 350,
                    springConstant: 0.12,
                    damping: 0.6,
                    avoidOverlap: 2.0
                },
                stabilization: {
                    enabled: true,
                    iterations: 3000,
                    updateInterval: 25,
                    onlyDynamicEdges: false,
                    fit: true
                },
                timestep: 0.25,
                adaptiveTimestep: true,
                maxVelocity: 30,
                minVelocity: 0.75
            },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                zoomView: true,
                dragView: true,
                dragNodes: true,
                selectConnectedEdges: false,
                hoverConnectedEdges: false,
                keyboard: {
                    enabled: true,
                    speed: { x: 10, y: 10, zoom: 0.02 },
                    bindToWindow: false
                },
                multiselect: false,
                navigationButtons: false,
                zoomSpeed: 0.8
            },
            layout: {
                improvedLayout: true,
                clusterThreshold: 150,
                hierarchical: false
            }
        };

        // Create network with enhanced styling
        network = new vis.Network(memoryNetworkDiv, { nodes, edges }, options);

        // Enhanced click interactions
        network.on('click', function(params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const node = nodes.get(nodeId);
                if (node) {
                    showMemoryModal(node);
                }
            }
        });

        // Simple but elegant hover effects
        network.on('hoverNode', function(params) {
            const hoveredNodeId = params.node;
            const connectedNodes = network.getConnectedNodes(hoveredNodeId);
            const connectedEdges = network.getConnectedEdges(hoveredNodeId);
            
            // Update nodes with elegant highlighting
            const nodeUpdates = [];
            
            data.nodes.forEach(nodeData => {
                const node = nodes.get(nodeData.id);
                if (!node) return;
                
                if (nodeData.id === hoveredNodeId) {
                    // Main hovered node - golden highlight
                    nodeUpdates.push({
                        id: nodeData.id,
                        color: {
                            background: '#fbbf24',
                            border: '#f59e0b',
                            borderWidth: 5
                        },
                        shadow: {
                            enabled: true,
                            color: 'rgba(251, 191, 36, 0.8)',
                            size: 25,
                            x: 0,
                            y: 0
                        },
                        size: node.size * 1.3
                    });
                } else if (connectedNodes.includes(nodeData.id)) {
                    // Connected nodes - purple highlight
                    nodeUpdates.push({
                        id: nodeData.id,
                        color: {
                            background: '#c084fc',
                            border: '#e879f9',
                            borderWidth: 4
                        },
                        shadow: {
                            enabled: true,
                            color: 'rgba(192, 132, 252, 0.6)',
                            size: 18,
                            x: 0,
                            y: 0
                        },
                        size: node.size * 1.1
                    });
                } else {
                    // Non-connected nodes - fade out
                    nodeUpdates.push({
                        id: nodeData.id,
                        color: {
                            background: 'rgba(139, 92, 246, 0.3)',
                            border: 'rgba(168, 85, 247, 0.4)',
                            borderWidth: 2
                        },
                        shadow: {
                            enabled: false
                        },
                        size: node.size * 0.8
                    });
                }
            });
            
            nodes.update(nodeUpdates);
        });

        network.on('blurNode', function() {
            // Restore original node appearances
            const nodeRestoreUpdates = [];
            
            data.nodes.forEach(nodeData => {
                const originalNode = nodes.get(nodeData.id);
                if (!originalNode) return;
                
                nodeRestoreUpdates.push({
                    id: nodeData.id,
                    color: {
                        background: '#8b5cf6',
                        border: '#a855f7',
                        borderWidth: 3,
                        highlight: { 
                            background: '#a78bfa', 
                            border: '#c084fc',
                            borderWidth: 4
                        }
                    },
                    shadow: {
                        enabled: true,
                        color: 'rgba(139, 92, 246, 0.3)',
                        size: 15,
                        x: 0,
                        y: 0
                    },
                    size: Math.min(60 + Math.max(1, nodeData.score * 20), 150) // Reset to original size calculation
                });
            });
            
            nodes.update(nodeRestoreUpdates);
        });

        // Fit network to container after stabilization
        network.once('stabilizationIterationsDone', function() {
            network.fit({
                animation: {
                    duration: 1000,
                    easingFunction: 'easeInOutQuad'
                }
            });
        });

        // Add zoom controls
        network.on('zoom', function(params) {
            const scale = network.getScale();
            // Adjust node sizes based on zoom level for better visibility
            if (scale < 0.5) {
                // When zoomed out, make nodes slightly larger
                const updateArray = [];
                nodes.forEach(node => {
                    updateArray.push({
                        id: node.id,
                        font: { ...node.font, size: Math.max(16, node.font.size * 1.2) }
                    });
                });
                nodes.update(updateArray);
            }
        });

    } catch (error) {
        console.error('Error rendering memory network:', error);
        showErrorMessage('Failed to load memory network.');
    }
}

// --- Session-based memory management for real-time updates ---
async function addMemoryToSession(memoryData) {
    console.log('✨ Adding new memory to session:', memoryData.content.substring(0, 50) + '...');
    
    // Avoid duplicates
    if (sessionMemoryIds.has(memoryData.id)) {
        console.log('Memory already in session, skipping');
        return;
    }
    
    // Add to session store
    sessionMemories.push(memoryData);
    sessionMemoryIds.add(memoryData.id);
    
    // If we're in map mode, add to network
    if (isMapMode && network) {
        addMemoryToNetworkRealtime(memoryData);
    } else {
        // If we're in list mode, refresh the memories list
        await renderMemories();
    }
}

function addMemoryToNetworkRealtime(memoryData) {
    if (!network) {
        console.warn('Network not initialized, cannot add memory');
        return;
    }
    
    console.log('🚀 Adding memory to network in real-time:', memoryData.content.substring(0, 30) + '...');
    
    const nodes = network.body.data.nodes;
    const edges = network.body.data.edges;
    
    // Create new node
    const baseSize = 60;
    const scoreMultiplier = Math.max(1, memoryData.score * 20);
    const nodeSize = Math.min(baseSize + scoreMultiplier, 150);
    
    const newNode = {
        id: memoryData.id,
        label: memoryData.content.length > 40 ? memoryData.content.substring(0, 40) + '...' : memoryData.content,
        title: `${memoryData.content}\\n\\nScore: ${memoryData.score.toFixed(2)}`,
        size: nodeSize,
        color: {
            background: '#8b5cf6',
            border: '#a855f7',
            highlight: {
                background: '#a78bfa',
                border: '#c084fc'
            }
        },
        font: {
            color: 'white',
            size: 14,
            face: 'Inter, sans-serif'
        },
        shadow: {
            enabled: true,
            color: 'rgba(139, 92, 246, 0.3)',
            size: 15,
            x: 0,
            y: 0
        },
        score: memoryData.score
    };
    
    // Add the new node
    nodes.add(newNode);
    
    // Calculate similarities with existing nodes for edges
    const existingNodes = nodes.get();
    const newEdges = [];
    const threshold = currentThreshold;
    
    existingNodes.forEach(existingNode => {
        if (existingNode.id !== memoryData.id) {
            const similarity = calculateSimpleSimilarity(memoryData.content, existingNode.title.split('\\n')[0]);
            if (similarity > threshold) {
                newEdges.push({
                    id: `${memoryData.id}-${existingNode.id}`,
                    from: memoryData.id,
                    to: existingNode.id,
                    value: similarity,
                    width: 2 + 12 * similarity,
                    color: {
                        color: `rgba(168,85,247,${Math.max(0.2, similarity * 0.8)})`,
                        highlight: 'rgba(255,215,0,1)',
                        hover: 'rgba(255,215,0,0.8)'
                    },
                    title: `Similarity: ${similarity.toFixed(3)}`
                });
            }
        }
    });
    
    // Add new edges
    if (newEdges.length > 0) {
        edges.add(newEdges);
    }
    
    console.log(`🎯 Added memory with ${newEdges.length} connections`);
    
    // Show notification
    if (!suppressMemoryNotifications) {
        showNewMemoryNotification(memoryData.content);
    }
}

// Simple similarity calculation
function calculateSimpleSimilarity(text1, text2) {
    const words1 = text1.toLowerCase().split(/\\s+/);
    const words2 = text2.toLowerCase().split(/\\s+/);
    
    const freq1 = {};
    const freq2 = {};
    
    words1.forEach(word => freq1[word] = (freq1[word] || 0) + 1);
    words2.forEach(word => freq2[word] = (freq2[word] || 0) + 1);
    
    let dotProduct = 0;
    let magnitude1 = 0;
    let magnitude2 = 0;
    
    const allWords = new Set([...words1, ...words2]);
    
    allWords.forEach(word => {
        const f1 = freq1[word] || 0;
        const f2 = freq2[word] || 0;
        
        dotProduct += f1 * f2;
        magnitude1 += f1 * f1;
        magnitude2 += f2 * f2;
    });
    
    if (magnitude1 === 0 || magnitude2 === 0) return 0;
    return dotProduct / (Math.sqrt(magnitude1) * Math.sqrt(magnitude2));
}

// Show notification for new memory
function showNewMemoryNotification(memoryText) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(139, 92, 246, 0.9);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        z-index: 1000;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
        backdrop-filter: blur(10px);
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    notification.textContent = `New memory: ${memoryText.substring(0, 50)}${memoryText.length > 50 ? '...' : ''}`;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Animate out and remove
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Polling system for new memories
function startNewMemoryPolling() {
    if (newMemoryPollingInterval) {
        clearInterval(newMemoryPollingInterval);
    }
    
    newMemoryPollingInterval = setInterval(checkForNewMemories, 2000);
    console.log('📡 Started polling for new memories');
}

function stopNewMemoryPolling() {
    if (newMemoryPollingInterval) {
        clearInterval(newMemoryPollingInterval);
        newMemoryPollingInterval = null;
        console.log('⏸️ Stopped polling for new memories');
    }
}

async function checkForNewMemories() {
    try {
        const data = await apiCall('/new-memories');
        
        if (data && data.memories && data.memories.length > 0) {
            console.log(`🔔 Found ${data.memories.length} new memories!`);
            
            // Add each new memory to the session
            for (const memoryData of data.memories) {
                await addMemoryToSession(memoryData);
            }
        }
    } catch (error) {
        // Silently handle errors to avoid spamming console
        if (error.message && !error.message.includes('fetch')) {
            console.warn('Error checking for new memories:', error);
        }
    }
}

// --- API Call Helper ---
const API_BASE_URL = 'http://localhost:5001';

async function apiCall(url, options = {}) {
    const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
    const response = await fetch(fullUrl, {
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
        ...options,
    });
    
    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }
    
    return await response.json();
}

// --- Initialize App ---
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 MemoryOS App initializing...');
    
    // Initialize memories list with the working approach
    renderMemories();
    
    // Setup other features
    setupSearch();
    setupSettings();
    
    // Setup search functionality
    setupSearch();
    
    // Setup settings
    setupSettings();
    
    // Setup map mode toggle
    const mapModeToggle = document.getElementById('map-mode-toggle');
    if (mapModeToggle) {
        mapModeToggle.addEventListener('change', toggleMapMode);
    }
    
    // Setup exit map mode button
    const exitMapModeBtn = document.getElementById('exit-map-mode');
    if (exitMapModeBtn) {
        exitMapModeBtn.addEventListener('click', () => {
            if (isMapMode) {
                toggleMapMode();
            }
        });
    }

    // Setup add memory form
    const addMemoryForm = document.getElementById('add-memory-form');
    const memoryContent = document.getElementById('memory-content');

    if (addMemoryForm) {
        addMemoryForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const content = memoryContent.value.trim();
            if (!content) return;

            try {
                // Direct fetch approach that works
                const response = await fetch('http://localhost:5001/memories', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ content }),
                });
                
                if (response.ok) {
                    const result = await response.json();
                    console.log('✅ Memory added:', result);
                    memoryContent.value = '';
                    // Re-render memories list
                    await renderMemories();
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            } catch (error) {
                console.error('Error adding memory:', error);
                alert(`Failed to add memory: ${error.message}`);
            }
        });
    }
});