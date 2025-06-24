// Global variables
let network = null;
let memoryNetworkDiv = null;
let currentThreshold = 0.35;
let isMapMode = false;

// --- Render Memories List ---
async function renderMemories() {
    try {
        const response = await apiCall('/memories');
        const container = document.getElementById('memories-container');
        
        // Handle the response format: {memories: [...]}
        const memories = response?.memories || [];
        
        if (!memories || !Array.isArray(memories) || memories.length === 0) {
            container.innerHTML = '<p class="text-gray-400">No memories found.</p>';
            return;
        }

        container.innerHTML = memories.map(memory => `
            <div class="memory-card" data-memory-id="${memory.id}">
                <p>${memory.content}</p>
                <div class="flex justify-between items-center mt-3">
                    <span class="memory-score">Score: ${memory.score.toFixed(2)}</span>
                    <span class="text-gray-400 text-sm">${memory.created}</span>
                    <button class="delete-memory-btn" onclick="deleteMemory('${memory.id}')">Delete</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error rendering memories:', error);
        document.getElementById('memories-container').innerHTML = '<p class="text-red-400">Failed to load memories.</p>';
    }
}

// --- Delete Memory ---
async function deleteMemory(memoryId) {
    if (!confirm('Are you sure you want to delete this memory?')) return;
    
    try {
        const result = await apiCall(`/memories/${memoryId}`, { method: 'DELETE' });
        if (result && result.success) {
            await renderMemories(); // Refresh the list
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
        const results = await apiCall(`/search/${encodeURIComponent(query)}`);
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
    
    if (thresholdSlider && thresholdValue) {
        thresholdSlider.addEventListener('input', (e) => {
            currentThreshold = parseFloat(e.target.value);
            thresholdValue.textContent = currentThreshold.toFixed(2);
            
            // Re-render network if in map mode
            if (isMapMode && memoryNetworkDiv) {
                renderMemoryNetwork();
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

// --- API Call Helper ---
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin',
            ...options,
        });
        if (!response.ok) {
            throw new Error('API error: ' + response.status);
        }
        return await response.json();
    } catch (err) {
        console.error('API call failed:', err);
        return null;
    }
}

// --- Initialize App ---
document.addEventListener('DOMContentLoaded', () => {
    // Initialize memories list
    renderMemories();
    
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

            // Optionally, you can add tags or method here
            const data = { content };
            const result = await apiCall('/memories', {
                method: 'POST',
                body: JSON.stringify(data),
            });
            if (result && result.id) {
                memoryContent.value = '';
                // Re-render memories list instead of reloading page
                await renderMemories();
            } else {
                alert('Failed to add memory.');
            }
        });
    }
});