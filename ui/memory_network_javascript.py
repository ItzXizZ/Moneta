MEMORY_NETWORK_JAVASCRIPT = '''
    <script>
    // Memory Network Variables
    let memoryNetwork = null;
    let networkData = { nodes: [], edges: [] };
    let activeMemories = new Set();
    let currentThreshold = 0.35;

    // Position persistence and incremental updates
    let savedNodePositions = {};
    let lastNetworkHash = '';
    let isInitialLoad = true;

    // Advanced Signal Trail System for Neural-like Visualization
    let signalTrails = [];
    let sparkleSystem = [];
    let trailAnimationActive = false;
    let nodeGlowLevels = {}; // Track accumulating glow for each node
    let activeSignals = 0;

    // Auto-refresh control
    let autoRefreshEnabled = false;
    let autoRefreshInterval = null;

    // Session memory store for real-time updates
    let sessionMemories = [];
    let sessionMemoryIds = new Set();
    let newMemoryPollingInterval = null;
    
    // Live score update system
    let scoreUpdateInterval = null;
    let lastScoreUpdateTime = 0;
    let scoreUpdateEnabled = false;
    let nodeScoreAnimations = new Map(); // Track ongoing score animations

    // Proportional Node Sizing System
    function calculateProportionalNodeSize(score, allScores) {
        // Safety check - if no scores or invalid score, return default size
        if (!allScores || allScores.length === 0 || score === undefined || score === null) {
            return 35; // Safe default size
        }
        
        // Ensure all scores are valid numbers
        const validScores = allScores.filter(s => typeof s === 'number' && !isNaN(s) && s >= 0);
        if (validScores.length === 0) {
            return 35; // Safe default size
        }
        
        // Find min/max scores in the dataset
        const minScore = Math.min(...validScores);
        const maxScore = Math.max(...validScores);
        
        // If all scores are the same, return a reasonable default size
        if (minScore === maxScore) {
            return 35;
        }
        
        // Apply logarithmic scaling to handle infinite growth
        const logMin = Math.log(minScore + 1);
        const logMax = Math.log(maxScore + 1);
        const logScore = Math.log(score + 1);
        
        // Calculate relative position (0-1)
        const relativePosition = (logScore - logMin) / (logMax - logMin);
        
        // Apply sigmoid function for smooth distribution
        const sigmoid = 1 / (1 + Math.exp(-10 * (relativePosition - 0.5)));
        
        // Map to size range with minimum visibility guarantee
        const minSize = 25;  // Minimum visible size
        const maxSize = 80;  // Maximum size cap
        const sizeRange = maxSize - minSize;
        
        const calculatedSize = minSize + (sigmoid * sizeRange);
        
        // Ensure the size is within bounds and return
        const finalSize = Math.max(minSize, Math.min(maxSize, calculatedSize));
        
        // Debug logging for size calculations
        if (score > 50) { // Only log for higher scores to avoid spam
            console.log(`📏 Proportional sizing: score=${score}, min=${minScore}, max=${maxScore}, size=${finalSize.toFixed(1)}`);
        }
        
        return finalSize;
    }

    // Function to recalculate all node sizes based on current score distribution
    function recalculateAllNodeSizes() {
        if (!networkData || !networkData.nodes || networkData.nodes.length === 0) {
            return;
        }
        
        // Extract all current scores
        const allScores = networkData.nodes.map(n => n.score || 0);
        
        // Recalculate sizes for all nodes
        networkData.nodes.forEach(node => {
            const newSize = calculateProportionalNodeSize(node.score || 0, allScores);
            node.size = newSize;
            
            // Update font size proportionally
            node.font = {
                ...node.font,
                size: Math.max(10, Math.min(14, 8 + newSize * 0.08))
            };
        });
        
        // Update the network with new sizes
        if (memoryNetwork) {
            memoryNetwork.setData(networkData);
        }
        
        console.log('🔄 Recalculated node sizes for proportional distribution');
    }

    // Live Score Update Functions
    function startLiveScoreUpdates() {
        if (scoreUpdateInterval) {
            clearInterval(scoreUpdateInterval);
        }
        
        scoreUpdateInterval = setInterval(checkForScoreUpdates, 3000); // Check every 3 seconds
        scoreUpdateEnabled = true;
        console.log('📊 Live score updates enabled - checking every 3 seconds');
    }

    function stopLiveScoreUpdates() {
        if (scoreUpdateInterval) {
            clearInterval(scoreUpdateInterval);
            scoreUpdateInterval = null;
        }
        scoreUpdateEnabled = false;
        console.log('⏸️ Live score updates disabled');
    }

    async function checkForScoreUpdates() {
        try {
            const response = await fetch('/score-updates');
            const data = await response.json();
            
            if (data.success && data.updates) {
                // Check if we have new updates
                if (data.timestamp > lastScoreUpdateTime) {
                    lastScoreUpdateTime = data.timestamp;
                    await updateNodeScores(data.updates);
                }
            }
        } catch (error) {
            console.error('❌ Error checking for score updates:', error);
        }
    }

    async function updateNodeScores(scoreUpdates) {
        if (!networkData || !networkData.nodes || !memoryNetwork) {
            return;
        }

        // Extract all current scores for proportional sizing
        const allScores = networkData.nodes.map(n => n.score || 0);
        let hasChanges = false;

        // Update scores and trigger animations
        scoreUpdates.forEach(update => {
            const node = networkData.nodes.find(n => n.id === update.id);
            if (node) {
                const oldScore = node.score || 0;
                const newScore = update.score;
                
                if (Math.abs(newScore - oldScore) > 0.01) { // Only update if significant change
                    node.score = newScore;
                    hasChanges = true;
                    
                    // Start score animation
                    animateNodeScoreChange(node.id, oldScore, newScore);
                    
                    console.log(`📈 Score update: ${update.content} ${oldScore.toFixed(2)} → ${newScore.toFixed(2)}`);
                }
            }
        });

        if (hasChanges) {
            // Recalculate all node sizes with new score distribution
            recalculateAllNodeSizes();
            
            // Update the network
            memoryNetwork.setData(networkData);
            
            console.log('🎯 Applied live score updates to network');
        }
    }

    function animateNodeScoreChange(nodeId, oldScore, newScore) {
        // Cancel any existing animation for this node
        if (nodeScoreAnimations.has(nodeId)) {
            clearInterval(nodeScoreAnimations.get(nodeId));
        }

        const node = networkData.nodes.find(n => n.id === nodeId);
        if (!node) return;

        const scoreDiff = newScore - oldScore;
        const animationDuration = 1000; // 1 second
        const steps = 20;
        const stepSize = scoreDiff / steps;
        const stepDuration = animationDuration / steps;
        
        let currentStep = 0;
        
        const animation = setInterval(() => {
            currentStep++;
            const currentScore = oldScore + (stepSize * currentStep);
            
            // Update node score during animation
            node.score = currentScore;
            
            // Update node color intensity based on score
            const intensity = Math.max(0.7, Math.min(1, currentScore / 100));
            node.color = {
                background: `rgba(35,4,55,${intensity})`,
                border: `rgba(255,255,255,${Math.min(0.4, intensity * 0.5)})`,
                highlight: {
                    background: `rgba(70,9,107,${intensity})`,
                    border: 'rgba(255,255,255,0.8)'
                },
                hover: {
                    background: `rgba(50,6,80,${intensity})`,
                    border: 'rgba(255,255,255,0.6)'
                }
            };
            
            // Update the specific node in the network
            if (memoryNetwork) {
                memoryNetwork.body.data.nodes.update(node);
            }
            
            if (currentStep >= steps) {
                // Animation complete
                clearInterval(animation);
                nodeScoreAnimations.delete(nodeId);
                
                // Ensure final score is exact
                node.score = newScore;
                if (memoryNetwork) {
                    memoryNetwork.body.data.nodes.update(node);
                }
            }
        }, stepDuration);
        
        nodeScoreAnimations.set(nodeId, animation);
    }

    function toggleLiveScoreUpdates() {
        if (scoreUpdateEnabled) {
            stopLiveScoreUpdates();
        } else {
            startLiveScoreUpdates();
        }
        
        // Update UI button if it exists
        const button = document.getElementById('toggle-score-updates');
        if (button) {
            button.textContent = scoreUpdateEnabled ? '⏸️ Pause Score Updates' : '📊 Enable Live Scores';
            button.className = scoreUpdateEnabled ? 'btn btn-warning' : 'btn btn-success';
        }
        
        // Show status message
        if (scoreUpdateEnabled) {
            console.log('📊 Live score updates enabled - scores will update every 3 seconds');
            console.log('💡 Node sizes and colors will animate smoothly as scores change');
        } else {
            console.log('⏸️ Live score updates disabled');
        }
    }

    async function saveScoresToJSON() {
        try {
            const button = document.getElementById('save-scores-btn');
            if (button) {
                button.textContent = '💾 Saving...';
                button.disabled = true;
            }
            
            const response = await fetch('/save-scores', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log('✅ ' + data.message);
                alert('✅ Scores saved to memories.json!');
            } else {
                console.error('❌ Failed to save scores:', data.error);
                alert('❌ Failed to save scores: ' + data.error);
            }
        } catch (error) {
            console.error('❌ Error saving scores:', error);
            alert('❌ Error saving scores: ' + error.message);
        } finally {
            const button = document.getElementById('save-scores-btn');
            if (button) {
                button.textContent = '💾 Save Scores';
                button.disabled = false;
            }
        }
    }

    // Memory Network Functions
    function initializeMemoryNetwork() {
        const container = document.getElementById('memory-network');
        
        // Clear any loading text first
        container.innerHTML = '<div class="memory-activity-indicator" id="activity-indicator">🔥 Memory Activity</div>';
        
        const options = {
            nodes: {
                shape: 'dot',
                scaling: { min: 20, max: 85 }, // Updated to accommodate larger proportional sizes
                font: {
                    size: 11,
                    color: '#ffffff',
                    face: '-apple-system, SF Pro Display, SF Pro Text, Helvetica Neue, Helvetica, Arial, sans-serif',
                    strokeWidth: 0,
                    strokeColor: 'transparent',
                    align: 'center',
                    vadjust: 0,
                    multi: false,
                    bold: {
                        face: '-apple-system, SF Pro Display, SF Pro Text, Helvetica Neue, Helvetica, Arial, sans-serif',
                        size: 11,
                        color: '#ffffff'
                    }
                },
                borderWidth: 1,
                borderWidthSelected: 2,
                shadow: {
                    enabled: true,
                    color: 'rgba(17,24,39,0.6)',
                    size: 12,
                    x: 0,
                    y: 3
                },
                margin: { top: 12, right: 12, bottom: 12, left: 12 },
                chosen: {
                    node: function(values, id, selected, hovering) {
                        if (hovering) {
                            values.shadowSize = 12;
                            values.shadowColor = 'rgba(168,85,247,0.6)';
                            values.borderWidth = 2;
                        }
                    }
                }
            },
            edges: {
                width: 1.5,
                color: { 
                    color: 'rgba(168,85,247,0.15)',
                    highlight: 'rgba(255,215,0,0.9)',
                    hover: 'rgba(255,215,0,0.7)'
                },
                smooth: {
                    type: 'curvedCW',
                    roundness: 0.2,
                    forceDirection: 'none'
                },
                shadow: {
                    enabled: true,
                    color: 'rgba(17,24,39,0.3)',
                    size: 6,
                    x: 0,
                    y: 2
                },
                length: 200,
                scaling: { min: 1, max: 6 },
                selectionWidth: 2,
                hoverWidth: 2
            },
            physics: {
                enabled: true,
                barnesHut: {
                    gravitationalConstant: -1200,
                    centralGravity: 0.15,
                    springLength: 150,
                    springConstant: 0.02,
                    damping: 0.12,
                    avoidOverlap: 0.2
                },
                maxVelocity: 100,
                minVelocity: 0.1,
                solver: 'barnesHut',
                stabilization: {
                    enabled: true,
                    iterations: 1500,
                    updateInterval: 35,
                    fit: true
                },
                adaptiveTimestep: false,
                timestep: 0.3
            },
            interaction: {
                hover: true,
                tooltipDelay: 150,
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
                zoomSpeed: 1.0
            },
            layout: {
                improvedLayout: true,
                clusterThreshold: 150,
                hierarchical: false,
                randomSeed: 2
            },
            configure: {
                enabled: false
            }
        };
        
        memoryNetwork = new vis.Network(container, networkData, options);
        
        // Keep default positioning - nodes should be visible
        console.log('🧠 Memory network will auto-fit to viewport');
        
        // Add click interaction
        memoryNetwork.on('click', function(params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const node = networkData.nodes.find(n => n.id === nodeId);
                if (node) {
                    alert(`Memory: ${node.content}\\nScore: ${node.score}`);
                }
            }
        });

        // Save positions when nodes are dragged or stabilized
        memoryNetwork.on('dragEnd', function(params) {
            saveNodePositions();
            setTimeout(() => {
                memoryNetwork.setOptions({
                    physics: {
                        barnesHut: {
                            springConstant: 0.02,
                            damping: 0.12,
                            centralGravity: 0.15
                        },
                        maxVelocity: 100
                    }
                });
            }, 100);
        });

        memoryNetwork.on('stabilizationIterationsDone', function() {
            saveNodePositions();
            console.log('🎯 Network stabilized, positions saved');
        });

        // Improve dragging responsiveness
        memoryNetwork.on('dragStart', function(params) {
            memoryNetwork.setOptions({
                physics: {
                    barnesHut: {
                        springConstant: 0.04,
                        damping: 0.2,
                        centralGravity: 0.1
                    },
                    maxVelocity: 150
                }
            });
        });

        let dragUpdateThrottle = null;
        
        memoryNetwork.on('dragging', function(params) {
            if (params.nodes.length > 0 && !dragUpdateThrottle) {
                dragUpdateThrottle = requestAnimationFrame(() => {
                    const nodeId = params.nodes[0];
                    if (nodeGlowLevels[nodeId] > 0.01) {
                        updateNodeGlow(nodeId);
                    }
                    dragUpdateThrottle = null;
                });
            }
        });

        let stabilizationThrottle = null;
        
        memoryNetwork.on('stabilizationProgress', () => {
            if (!stabilizationThrottle) {
                stabilizationThrottle = requestAnimationFrame(() => {
                    for (const nodeId in nodeGlowLevels) {
                        if (nodeGlowLevels[nodeId] > 0.01) {
                            updateNodeGlow(nodeId);
                        }
                    }
                    stabilizationThrottle = null;
                });
            }
        });
        
        console.log('🧠 Memory network initialized');
    }

    // Save current node positions to preserve layout
    function saveNodePositions() {
        if (!memoryNetwork) return;
        
        try {
            const positions = memoryNetwork.getPositions();
            savedNodePositions = { ...positions };
            console.log(`💾 Saved ${Object.keys(positions).length} node positions`);
        } catch (error) {
            console.warn('Could not save node positions:', error);
        }
    }

    // Restore saved node positions
    function restoreNodePositions(nodes) {
        const restoredNodes = nodes.map(node => {
            if (savedNodePositions[node.id]) {
                return {
                    ...node,
                    x: savedNodePositions[node.id].x,
                    y: savedNodePositions[node.id].y,
                    fixed: false // Allow physics to take over after positioning
                };
            }
            return node;
        });
        
        console.log(`🔄 Restored positions for ${restoredNodes.filter(n => n.x !== undefined).length} nodes`);
        return restoredNodes;
    }

    // Generate hash of network data to detect changes
    function generateNetworkHash(data) {
        const nodeStr = data.nodes.map(n => `${n.id}:${n.label}:${n.score}`).sort().join('|');
        const edgeStr = data.edges.map(e => `${e.from}-${e.to}:${e.value}`).sort().join('|');
        return btoa(nodeStr + '::' + edgeStr).substring(0, 20);
    }

    // Incremental network update instead of complete replacement
    async function updateMemoryNetworkIncremental(newData) {
        if (!memoryNetwork) return;
        
        const newHash = generateNetworkHash(newData);
        
        // If data hasn't changed, skip update
        if (newHash === lastNetworkHash && !isInitialLoad) {
            console.log('📊 Network data unchanged, skipping update');
            return;
        }
        
        console.log('🔄 Updating memory network incrementally...');
        
        // Save current positions before update
        saveNodePositions();
        
        // Create new nodes with elegant Apple-style design
        // Extract all scores for proportional sizing
        const allScores = newData.nodes.map(n => n.score || 0);
        
        const processedNodes = newData.nodes.map((node, index) => {
            const intensity = Math.max(0.7, Math.min(1, node.score / 100));
            // Use proportional sizing instead of linear sizing
            const size = calculateProportionalNodeSize(node.score || 0, allScores);
            
            return {
                id: node.id,
                label: node.label.length > 25 ? node.label.substring(0, 25) + '…' : node.label,
                title: node.label,
                size: size,
                color: {
                    background: `rgba(35,4,55,${intensity})`,
                    border: `rgba(255,255,255,${Math.min(0.4, intensity * 0.5)})`,
                    highlight: {
                        background: `rgba(70,9,107,${intensity})`,
                        border: 'rgba(255,255,255,0.8)'
                    },
                    hover: {
                        background: `rgba(50,6,80,${intensity})`,
                        border: 'rgba(255,255,255,0.6)'
                    }
                },
                font: {
                    size: Math.max(10, Math.min(12, 8 + size * 0.08)),
                    color: '#ffffff',
                    face: '-apple-system, SF Pro Display, SF Pro Text, Helvetica Neue, Helvetica, Arial, sans-serif',
                    strokeWidth: 0,
                    strokeColor: 'transparent'
                },
                score: node.score,
                tags: node.tags || [],
                content: node.label,
                created: node.created || ''
            };
        });
        
        // Restore positions for existing nodes and identify new nodes
        const existingNodeIds = new Set(networkData.nodes.map(n => n.id));
        const restoredNodes = restoreNodePositions(processedNodes);
        const newNodeIds = restoredNodes.filter(n => !existingNodeIds.has(n.id)).map(n => n.id);
        
        // Process edges
        const processedEdges = newData.edges.map(edge => ({
            from: edge.from,
            to: edge.to,
            value: edge.value,
            width: Math.max(1, edge.value * 6),
            color: {
                color: `rgba(168,85,247,${Math.max(0.2, edge.value * 0.8)})`,
                highlight: 'rgba(255,215,0,1)',
                hover: 'rgba(255,215,0,0.8)'
            },
            title: `Similarity: ${edge.value.toFixed(3)}`
        }));
        
        // Update network data
        networkData.nodes = restoredNodes;
        networkData.edges = processedEdges;
        
        // Initialize node glow levels for new nodes
        restoredNodes.forEach(node => {
            if (!nodeGlowLevels.hasOwnProperty(node.id)) {
                nodeGlowLevels[node.id] = 0;
            }
        });
        
        // Update the network
        if (isInitialLoad) {
            // First load - allow physics to position nodes naturally
            memoryNetwork.setData(networkData);
            isInitialLoad = false;
        } else {
            // Incremental update - preserve positions
            memoryNetwork.setData(networkData);
            
            // Animate new nodes if any
            if (newNodeIds.length > 0) {
                console.log(`✨ Animating ${newNodeIds.length} new memories`);
                setTimeout(() => animateNewNodes(newNodeIds), 100);
            }
        }
        
        // Update stats
        document.getElementById('memory-count').textContent = newData.nodes.length;
        document.getElementById('connection-count').textContent = newData.edges.length;
        document.getElementById('active-memories').textContent = activeMemories.size;
        
        // Populate session store with initial data
        if (isInitialLoad) {
            sessionMemories = newData.nodes.map(node => ({
                id: node.id,
                content: node.label,
                score: node.score,
                tags: node.tags || [],
                created: node.created || ''
            }));
            sessionMemoryIds = new Set(sessionMemories.map(m => m.id));
            console.log(`📝 Initialized session store with ${sessionMemories.length} memories`);
        }
        
        lastNetworkHash = newHash;
        console.log(`🧠 Updated network: ${newData.nodes.length} memories, ${newData.edges.length} connections`);
        
        // Recalculate all node sizes for proportional distribution
        setTimeout(() => {
            recalculateAllNodeSizes();
        }, 100);
        
        // Start glow decay system
        startGlowDecay();
    }

    // Animate new nodes with a smooth entrance effect
    function animateNewNodes(newNodeIds) {
        console.log('🔧 DEBUG: animateNewNodes called with:', newNodeIds);
        
        newNodeIds.forEach((nodeId, index) => {
            console.log(`🔧 DEBUG: Setting up animation for node ${index + 1}: ${nodeId}`);
            
            setTimeout(() => {
                console.log(`🔧 DEBUG: Starting animation for node: ${nodeId}`);
                
                // Add entrance animation effects
                console.log('🔧 DEBUG: Adding glow effect...');
                addNodeGlow(nodeId, 0.8);
                
                console.log('🔧 DEBUG: Adding pulse effect...');
                createNodePulse(nodeId, 0.6);
                
                // Show notification for new memory
                const node = networkData.nodes.find(n => n.id === nodeId);
                console.log('🔧 DEBUG: Found node for notification:', !!node);
                
                if (node) {
                    console.log('🔧 DEBUG: Showing notification for:', node.label.substring(0, 30) + '...');
                    showNewMemoryNotification(node.label);
                } else {
                    console.warn('🔧 DEBUG: Node not found in networkData for notification');
                }
            }, index * 200);
        });
    }

    // Show notification for new memory
    function showNewMemoryNotification(memoryText) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(168,85,247,0.9);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(168,85,247,0.3);
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
            setTimeout(() => notification.remove(), 3000);
        }, 3000);
    }

    async function loadMemoryNetwork() {
        try {
            const threshold = parseFloat(document.getElementById('threshold-slider')?.value || currentThreshold);
            const response = await fetch(`/memory-network?threshold=${threshold}`);
            const data = await response.json();
            
            // Use incremental update instead of complete replacement
            await updateMemoryNetworkIncremental(data);
            
        } catch (error) {
            console.error('Error loading memory network:', error);
        }
    }

    // Auto-refresh toggle functionality
    function toggleAutoRefresh() {
        autoRefreshEnabled = !autoRefreshEnabled;
        
        if (autoRefreshEnabled) {
            autoRefreshInterval = setInterval(loadMemoryNetwork, 30000);
            console.log('🔄 Auto-refresh enabled (30s interval)');
            
            // Update button text if it exists
            const button = document.getElementById('auto-refresh-toggle');
            if (button) button.textContent = 'Disable Auto-refresh';
        } else {
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
            }
            console.log('⏸️ Auto-refresh disabled');
            
            // Update button text if it exists
            const button = document.getElementById('auto-refresh-toggle');
            if (button) button.textContent = 'Enable Auto-refresh';
        }
    }

    // Toggle new memory polling
    function toggleNewMemoryPolling() {
        if (newMemoryPollingInterval) {
            stopNewMemoryPolling();
        } else {
            startNewMemoryPolling();
        }
    }

    // Session-based memory management for real-time updates
    function addMemoryToSession(memoryData) {
        console.log('🔧 DEBUG: addMemoryToSession called with:', memoryData);
        console.log('✨ Adding new memory to session:', memoryData.content.substring(0, 50) + '...');
        
        // Avoid duplicates
        if (sessionMemoryIds.has(memoryData.id)) {
            console.log('🔧 DEBUG: Memory already in session, skipping');
            return;
        }
        
        console.log('🔧 DEBUG: Adding to session store. Current session size:', sessionMemories.length);
        
        // Add to session store
        sessionMemories.push(memoryData);
        sessionMemoryIds.add(memoryData.id);
        
        console.log('🔧 DEBUG: Session store updated. New size:', sessionMemories.length);
        console.log('🔧 DEBUG: Network object available:', !!memoryNetwork);
        
        // Calculate similarity with existing memories and add to network
        addMemoryToNetworkRealtime(memoryData);
    }

    function addMemoryToNetworkRealtime(memoryData) {
        console.log('🔧 DEBUG: addMemoryToNetworkRealtime called with:', memoryData);
        
        if (!memoryNetwork) {
            console.warn('🔧 DEBUG: Network not initialized, cannot add memory');
            return;
        }
        
        console.log('🔧 DEBUG: Current network data nodes:', networkData.nodes.length);
        console.log('🚀 Adding memory to network in real-time:', memoryData.content.substring(0, 30) + '...');
        
        // Create new node
        const intensity = Math.max(0.7, Math.min(1, memoryData.score / 100));
        // Extract all scores including the new memory for proportional sizing
        const allScores = [...networkData.nodes.map(n => n.score || 0), memoryData.score || 0];
        const size = calculateProportionalNodeSize(memoryData.score || 0, allScores);
        
        console.log('🔧 DEBUG: Node properties - intensity:', intensity, 'size:', size);
        
        const newNode = {
            id: memoryData.id,
            label: memoryData.content.length > 25 ? memoryData.content.substring(0, 25) + '…' : memoryData.content,
            title: memoryData.content,
            size: size,
            color: {
                background: `rgba(35,4,55,${intensity})`,
                border: `rgba(255,255,255,${Math.min(0.4, intensity * 0.5)})`,
                highlight: {
                    background: `rgba(70,9,107,${intensity})`,
                    border: 'rgba(255,255,255,0.8)'
                },
                hover: {
                    background: `rgba(50,6,80,${intensity})`,
                    border: 'rgba(255,255,255,0.6)'
                }
            },
            font: {
                size: Math.max(10, Math.min(12, 8 + size * 0.08)),
                color: '#ffffff',
                face: '-apple-system, SF Pro Display, SF Pro Text, Helvetica Neue, Helvetica, Arial, sans-serif',
                strokeWidth: 0,
                strokeColor: 'transparent'
            },
            score: memoryData.score,
            tags: memoryData.tags || [],
            content: memoryData.content,
            created: memoryData.created || new Date().toISOString().split('T')[0]
        };
        
        console.log('🔧 DEBUG: Created new node:', newNode);
        
        // Calculate similarities with existing nodes for edges
        const newEdges = [];
        const threshold = currentThreshold;
        
        console.log('🔧 DEBUG: Calculating similarities. Threshold:', threshold);
        console.log('🔧 DEBUG: Existing nodes to check:', networkData.nodes.length);
        
        networkData.nodes.forEach((existingNode, index) => {
            const similarity = calculateSimpleSimilarity(memoryData.content, existingNode.content);
            console.log(`🔧 DEBUG: Similarity with node ${index} (${existingNode.content.substring(0, 20)}...): ${similarity.toFixed(3)}`);
            
            if (similarity > threshold) {
                const newEdge = {
                    from: memoryData.id,
                    to: existingNode.id,
                    value: similarity,
                    width: Math.max(1, similarity * 6),
                    color: {
                        color: `rgba(168,85,247,${Math.max(0.2, similarity * 0.8)})`,
                        highlight: 'rgba(255,215,0,1)',
                        hover: 'rgba(255,215,0,0.8)'
                    },
                    title: `Similarity: ${similarity.toFixed(3)}`
                };
                newEdges.push(newEdge);
                console.log('🔧 DEBUG: Added edge:', newEdge);
            }
        });
        
        console.log('🔧 DEBUG: Total new edges:', newEdges.length);
        
        // Add to network data
        networkData.nodes.push(newNode);
        networkData.edges.push(...newEdges);
        
        console.log('🔧 DEBUG: Network data updated. Nodes:', networkData.nodes.length, 'Edges:', networkData.edges.length);
        
        // Initialize glow level
        nodeGlowLevels[memoryData.id] = 0;
        
        // Update the network with new data
        console.log('🔧 DEBUG: Calling memoryNetwork.setData...');
        memoryNetwork.setData(networkData);
        console.log('🔧 DEBUG: memoryNetwork.setData completed');
        
        // Animate the new node
        setTimeout(() => {
            console.log('🔧 DEBUG: Starting animation for new node');
            animateNewNodes([memoryData.id]);
            console.log(`🎯 Added memory with ${newEdges.length} connections`);
            
            // Update stats
            const memoryCountEl = document.getElementById('memory-count');
            const connectionCountEl = document.getElementById('connection-count');
            
            if (memoryCountEl) {
                memoryCountEl.textContent = networkData.nodes.length;
                console.log('🔧 DEBUG: Updated memory count to:', networkData.nodes.length);
            }
            if (connectionCountEl) {
                connectionCountEl.textContent = networkData.edges.length;
                console.log('🔧 DEBUG: Updated connection count to:', networkData.edges.length);
            }
        }, 100);
    }

    // Simple similarity calculation for real-time use
    function calculateSimpleSimilarity(text1, text2) {
        // Convert to lowercase and split into words
        const words1 = text1.toLowerCase().split(/\s+/);
        const words2 = text2.toLowerCase().split(/\s+/);
        
        // Create word frequency maps
        const freq1 = {};
        const freq2 = {};
        
        words1.forEach(word => freq1[word] = (freq1[word] || 0) + 1);
        words2.forEach(word => freq2[word] = (freq2[word] || 0) + 1);
        
        // Calculate dot product and magnitudes
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
        
        // Cosine similarity
        if (magnitude1 === 0 || magnitude2 === 0) return 0;
        return dotProduct / (Math.sqrt(magnitude1) * Math.sqrt(magnitude2));
    }

    // Global functions to be called when new memories are created
    window.addNewMemoryToNetwork = function(memoryData) {
        addMemoryToSession(memoryData);
    };

    window.addMemoryToNetworkRealtime = addMemoryToNetworkRealtime;
    
    // Global function to manually recalculate node sizes
    window.recalculateNodeSizes = function() {
        recalculateAllNodeSizes();
    };

    // Simple notification function
    window.showNewMemoryNotification = function(message) {
        console.log('🔔 Memory notification:', message);
        
        // Create notification element
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, rgba(168, 85, 247, 0.9), rgba(147, 51, 234, 0.8));
            color: white;
            padding: 15px 20px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 500;
            z-index: 10000;
            box-shadow: 0 8px 32px rgba(168, 85, 247, 0.3);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transform: translateX(100%);
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            max-width: 300px;
        `;
        notification.textContent = `🧠 ${message}`;
        
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
    };

    // Polling system for new memories
    function startNewMemoryPolling() {
        console.log('🔧 DEBUG: startNewMemoryPolling called');
        
        if (newMemoryPollingInterval) {
            console.log('🔧 DEBUG: Clearing existing polling interval');
            clearInterval(newMemoryPollingInterval);
        }
        
        newMemoryPollingInterval = setInterval(checkForNewMemories, 2000); // Poll every 2 seconds
        console.log('📡 Started polling for new memories every 2 seconds');
        console.log('🔧 DEBUG: Polling interval ID:', newMemoryPollingInterval);
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
            console.log('🔧 DEBUG: ========== POLLING /new-memories ENDPOINT ==========');
            console.log('🔧 DEBUG: Making GET request to /new-memories (NOT /end_thread)');
            
            const response = await fetch('/new-memories');
            console.log('🔧 DEBUG: /new-memories response status:', response.status);
            console.log('🔧 DEBUG: /new-memories response headers:', [...response.headers.entries()]);
            
            const data = await response.json();
            console.log('🔧 DEBUG: /new-memories response data:', JSON.stringify(data, null, 2));
            console.log('🔧 DEBUG: Expected format: { "memories": [...], "count": N }');
            
            if (data.memories && data.memories.length > 0) {
                console.log(`🔔 ✅ Found ${data.memories.length} new memories in session queue!`);
                console.log('🔧 DEBUG: Memory details:', data.memories.map(m => ({ id: m.id, content: m.content.substring(0, 50) + '...' })));
                
                // Add each new memory to the network
                data.memories.forEach((memoryData, index) => {
                    console.log(`🔧 DEBUG: Processing session memory ${index + 1}:`, memoryData);
                    addMemoryToSession(memoryData);
                });
            } else {
                console.log('🔧 DEBUG: ⚠️ No new memories found in session queue');
                console.log('🔧 DEBUG: data.memories:', data.memories);
                console.log('🔧 DEBUG: data.count:', data.count);
            }
            
            console.log('🔧 DEBUG: ========== /new-memories POLLING COMPLETE ==========');
        } catch (error) {
            console.error('🔧 DEBUG: ❌ Error polling /new-memories endpoint:', error);
        }
    }

    function animateMemoryActivation(activatedMemoryIds) {
        if (!memoryNetwork || !activatedMemoryIds.length) {
            return;
        }
        
        // Verify these nodes exist in our network
        const existingNodeIds = networkData.nodes.map(node => node.id);
        const validMemoryIds = activatedMemoryIds.filter(id => existingNodeIds.includes(id));
        
        if (validMemoryIds.length === 0) {
            return;
        }
        
        // Show activity indicator
        const indicator = document.getElementById('activity-indicator');
        if (indicator) {
            indicator.classList.add('active');
            setTimeout(() => {
                if (indicator) {
                    indicator.classList.remove('active');
                }
            }, 4000);
        }
        
        // Update last search time
        const lastSearchElement = document.getElementById('last-search');
        if (lastSearchElement) {
            lastSearchElement.textContent = new Date().toLocaleTimeString();
        }
        
        // Start the signal animation
        setTimeout(() => {
            createNeuralPropagationEffect(validMemoryIds);
        }, 100);
        
        // Update active memories count
        activeMemories = new Set(validMemoryIds);
        const activeMemoriesElement = document.getElementById('active-memories');
        if (activeMemoriesElement) {
            activeMemoriesElement.textContent = activeMemories.size;
        }
        
        // Clear active memories after animation completes
        setTimeout(() => {
            activeMemories.clear();
            const activeMemoriesElement = document.getElementById('active-memories');
            if (activeMemoriesElement) {
                activeMemoriesElement.textContent = '0';
            }
        }, 5000);
    }

    function createNeuralPropagationEffect(activatedMemoryIds) {
        // Reset global visited nodes for new simulation
        globalVisitedNodes.clear();
        
        // Add immediate effects to activated nodes
        activatedMemoryIds.forEach((startNodeId, index) => {
            // Give initial activated nodes immediate glow, pulse, and vibration
            addNodeGlow(startNodeId, 1.0);
            createNodePulse(startNodeId, 1.0);
            createNodeVibration(startNodeId, 1.0);
        });
        
        // Start signal propagation from each activated node with slight delay
        activatedMemoryIds.forEach((startNodeId, index) => {
            setTimeout(() => {
                propagateSignalFromNode(startNodeId, 0, new Set(), 1.0);
            }, index * 150);
        });
    }

    // Global visited tracking to prevent infinite loops
    let globalVisitedNodes = new Set();

    async function propagateSignalFromNode(currentNodeId, hopCount, visitedNodes, signalStrength) {
        // Stop if we've reached max hops, signal is too weak, or node already visited globally
        if (hopCount >= 5 || signalStrength < 0.15 || globalVisitedNodes.has(currentNodeId)) {
            return;
        }
        
        // Add current node to both local and global visited sets
        const newVisited = new Set(visitedNodes);
        newVisited.add(currentNodeId);
        globalVisitedNodes.add(currentNodeId);
        
        // Add glow to current node
        addNodeGlow(currentNodeId, signalStrength);
        
        // Find all connected neighbors
        const neighbors = getConnectedNeighbors(currentNodeId);
        
        // Filter out already visited neighbors
        const unvisitedNeighbors = neighbors.filter(neighborId => !globalVisitedNodes.has(neighborId));
        
        if (unvisitedNeighbors.length === 0) {
            return;
        }
        
        // Propagate to each neighbor with staggered timing
        const propagationPromises = unvisitedNeighbors.map((neighborId, index) => {
            return new Promise(resolve => {
                setTimeout(async () => {
                    const newStrength = signalStrength * 0.85;
                    
                    // Animate signal to neighbor
                    await animateSignalToNeighbor(currentNodeId, neighborId, newStrength, `hop-${hopCount}-${index}`, hopCount);
                    
                    // Continue propagation from neighbor
                    setTimeout(() => {
                        propagateSignalFromNode(neighborId, hopCount + 1, newVisited, newStrength);
                        resolve();
                    }, 50);
                }, index * 75);
            });
        });
        
        await Promise.all(propagationPromises);
    }

    function getConnectedNeighbors(nodeId) {
        const neighbors = [];
        networkData.edges.forEach(edge => {
            if (edge.from === nodeId) {
                neighbors.push(edge.to);
            } else if (edge.to === nodeId) {
                neighbors.push(edge.from);
            }
        });
        return neighbors;
    }

    async function animateSignalToNeighbor(fromId, toId, strength, signalId, hopCount = 0) {
        return new Promise(resolve => {
            activeSignals++;
            
            // Calculate fading strength based on hop count
            const fadedStrength = strength * Math.pow(0.8, hopCount);
            
            const particle = createSignalParticle(fadedStrength, signalId);
            const container = document.getElementById('memory-network');
            const containerRect = container.getBoundingClientRect();
            
            const animationDuration = 100;
            const startTime = Date.now();
            const trail = [];
            
            const animate = () => {
                const elapsed = Date.now() - startTime;
                const progress = Math.min(elapsed / animationDuration, 1);
                
                const positions = memoryNetwork.getPositions([fromId, toId]);
                const fromPos = memoryNetwork.canvasToDOM(positions[fromId]);
                const toPos = memoryNetwork.canvasToDOM(positions[toId]);
                
                const eased = easeInOutCubic(progress);
                
                // Create curved path similar to vis.js edges
                const { currentX, currentY } = getCurvedPathPosition(fromPos, toPos, eased, fromId, toId);
                
                particle.style.left = (containerRect.left + currentX) + 'px';
                particle.style.top = (containerRect.top + currentY) + 'px';
                
                // Create continuous trail effect
                trail.push({ x: currentX, y: currentY, time: elapsed });
                
                // Keep trail length manageable
                if (trail.length > 15) {
                    trail.shift();
                }
                
                // Draw continuous trail with faded strength
                if (trail.length > 1) {
                    drawContinuousTrail(trail, fadedStrength, containerRect, signalId);
                }
                
                // Dynamic scaling and opacity using faded strength
                const scale = fadedStrength * (1 + Math.sin(progress * Math.PI * 2) * 0.2);
                particle.style.transform = `translate(-50%, -50%) scale(${scale})`;
                particle.style.opacity = Math.max(0.2, fadedStrength * (Math.sin(progress * Math.PI) * 0.7 + 0.3));
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    // Signal reaches destination with faded strength
                    addNodeGlow(toId, fadedStrength);
                    createNodePulse(toId, fadedStrength);
                    createNodeVibration(toId, fadedStrength);
                    
                    particle.style.transition = 'all 0.4s ease-out';
                    particle.style.opacity = '0';
                    particle.style.transform = 'translate(-50%, -50%) scale(0)';
                    
                    setTimeout(() => {
                        particle.remove();
                        // Clean up trail for this signal
                        const trailElement = document.querySelector(`.continuous-trail-${signalId}`);
                        if (trailElement) {
                            trailElement.style.transition = 'opacity 0.3s ease-out';
                            trailElement.style.opacity = '0';
                            setTimeout(() => trailElement.remove(), 300);
                        }
                        activeSignals--;
                        resolve();
                    }, 400);
                }
            };
            
            requestAnimationFrame(animate);
        });
    }

    function createSignalParticle(strength, signalId) {
        const particle = document.createElement('div');
        const size = Math.max(16, 32 * strength);
        const intensity = Math.max(0.7, strength);
        
        particle.className = `signal-particle-${signalId}`;
        particle.style.position = 'fixed';
        particle.style.width = size + 'px';
        particle.style.height = size + 'px';
        particle.style.borderRadius = '50%';
        particle.style.background = `radial-gradient(circle, rgba(255, 255, 255, ${intensity}) 0%, rgba(255, 215, 0, ${intensity * 0.9}) 30%, rgba(255, 152, 0, ${intensity * 0.7}) 100%)`;
        particle.style.boxShadow = `0 0 ${size * 2}px rgba(255, 215, 0, ${intensity}), 0 0 ${size * 4}px rgba(255, 152, 0, ${intensity * 0.8}), 0 0 ${size * 6}px rgba(255, 215, 0, ${intensity * 0.4})`;
        particle.style.zIndex = '995';
        particle.style.pointerEvents = 'none';
        particle.style.transform = 'translate(-50%, -50%)';
        document.body.appendChild(particle);
        return particle;
    }

    function drawContinuousTrail(trail, strength, containerRect, signalId = 'default') {
        // Remove any existing trail for this specific signal
        const existingTrail = document.querySelector(`.continuous-trail-${signalId}`);
        if (existingTrail) {
            existingTrail.remove();
        }
        
        // Create SVG for smooth trail
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.className = `continuous-trail continuous-trail-${signalId}`;
        svg.style.position = 'fixed';
        svg.style.top = '0';
        svg.style.left = '0';
        svg.style.width = '100vw';
        svg.style.height = '100vh';
        svg.style.pointerEvents = 'none';
        svg.style.zIndex = '990';
        document.body.appendChild(svg);
        
        // Create path for trail
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        
        // Build path data
        let pathData = '';
        trail.forEach((point, index) => {
            const x = containerRect.left + point.x;
            const y = containerRect.top + point.y;
            
            if (index === 0) {
                pathData += `M ${x} ${y}`;
            } else {
                pathData += ` L ${x} ${y}`;
            }
        });
        
        path.setAttribute('d', pathData);
        path.setAttribute('stroke', `rgba(255, 215, 0, ${strength * 0.8})`);
        path.setAttribute('stroke-width', Math.max(3, strength * 6));
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('stroke-linejoin', 'round');
        path.style.filter = `drop-shadow(0 0 ${strength * 8}px rgba(255, 215, 0, ${strength * 0.6}))`;
        
        // Add gradient effect
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
        gradient.setAttribute('id', 'trailGradient');
        gradient.setAttribute('gradientUnits', 'userSpaceOnUse');
        
        const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
        stop1.setAttribute('offset', '0%');
        stop1.setAttribute('stop-color', `rgba(255, 215, 0, 0)`);
        
        const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
        stop2.setAttribute('offset', '70%');
        stop2.setAttribute('stop-color', `rgba(255, 215, 0, ${strength * 0.6})`);
        
        const stop3 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
        stop3.setAttribute('offset', '100%');
        stop3.setAttribute('stop-color', `rgba(255, 255, 255, ${strength})`);
        
        gradient.appendChild(stop1);
        gradient.appendChild(stop2);
        gradient.appendChild(stop3);
        defs.appendChild(gradient);
        svg.appendChild(defs);
        
        path.setAttribute('stroke', 'url(#trailGradient)');
        svg.appendChild(path);
        
        // Auto-remove trail after animation
        setTimeout(() => {
            if (svg.parentNode) {
                svg.remove();
            }
        }, 150);
    }

    function addNodeGlow(nodeId, strength) {
        // Set glow strength
        nodeGlowLevels[nodeId] = Math.min(1.0, strength);
        updateNodeGlow(nodeId);
        createNodePulse(nodeId, strength);
        
        // Restart decay interval if not already running
        if (!glowDecayInterval) {
            startGlowDecay();
        }
    }

    function updateNodeGlow(nodeId) {
        const glowLevel = nodeGlowLevels[nodeId];
        if (glowLevel <= 0.01) {
            const existingGlow = document.getElementById(`node-glow-${nodeId}`);
            if (existingGlow) existingGlow.remove();
            return;
        }
        
        let glow = document.getElementById(`node-glow-${nodeId}`);
        
        if (!glow) {
            glow = document.createElement('div');
            glow.id = `node-glow-${nodeId}`;
            glow.className = 'persistent-node-glow';
            glow.style.position = 'fixed';
            glow.style.borderRadius = '50%';
            glow.style.pointerEvents = 'none';
            glow.style.zIndex = '992';
            glow.style.transition = 'opacity 0.3s ease-out';
            glow.style.animation = 'gentle-pulse 2s ease-in-out infinite';
            document.body.appendChild(glow);
        }

        // Get positions
        const positions = memoryNetwork.getPositions([nodeId]);
        const nodePos = memoryNetwork.canvasToDOM(positions[nodeId]);
        const container = document.getElementById('memory-network');
        const containerRect = container.getBoundingClientRect();
        
        // Get the actual node size for proportional glow
        const node = networkData.nodes.find(n => n.id === nodeId);
        const nodeSize = node ? node.size : 35; // Default size if node not found
        
        // Make glow proportional to node size (1.5x to 2.5x the node size)
        const glowMultiplier = 1.5 + (glowLevel * 1.0); // Range: 1.5x to 2.5x
        const size = Math.max(nodeSize * glowMultiplier, 60); // Minimum 60px for visibility
        
        const x = containerRect.left + nodePos.x - size/2;
        const y = containerRect.top + nodePos.y - size/2;
        
        glow.style.transform = `translate(${x}px, ${y}px)`;
        glow.style.width = size + 'px';
        glow.style.height = size + 'px';
        glow.style.background = `radial-gradient(circle, rgba(168,85,247,${Math.floor(glowLevel * 120).toString(16).padStart(2, '0')}) 0%, rgba(168,85,247,${Math.floor(glowLevel * 60).toString(16).padStart(2, '0')}) 40%, transparent 70%)`;
        glow.style.opacity = Math.min(0.8, glowLevel * 1.1);
        glow.style.filter = `blur(${Math.max(2, 6 * glowLevel)}px)`;
        glow.style.setProperty('--glow-opacity', glowLevel.toString());
    }

    function createNodePulse(nodeId, strength) {
        const positions = memoryNetwork.getPositions([nodeId]);
        const nodePos = memoryNetwork.canvasToDOM(positions[nodeId]);
        const container = document.getElementById('memory-network');
        const containerRect = container.getBoundingClientRect();
        
        for (let i = 0; i < Math.ceil(strength * 2); i++) {
            setTimeout(() => {
                const pulse = document.createElement('div');
                // Get the actual node size for proportional pulse
                const node = networkData.nodes.find(n => n.id === nodeId);
                const nodeSize = node ? node.size : 35; // Default size if node not found
                
                // Make pulse proportional to node size (1.2x to 2.0x the node size)
                const pulseMultiplier = 1.2 + (strength * 0.8); // Range: 1.2x to 2.0x
                const size = Math.max(nodeSize * pulseMultiplier, 50); // Minimum 50px for visibility
                
                pulse.style.position = 'fixed';
                pulse.style.left = (containerRect.left + nodePos.x - size/2) + 'px';
                pulse.style.top = (containerRect.top + nodePos.y - size/2) + 'px';
                pulse.style.width = size + 'px';
                pulse.style.height = size + 'px';
                pulse.style.borderRadius = '50%';
                pulse.style.border = '3px solid rgba(168,85,247,0.8)';
                pulse.style.pointerEvents = 'none';
                pulse.style.zIndex = '993';
                pulse.style.opacity = strength;
                document.body.appendChild(pulse);

                pulse.style.transition = 'all 0.8s ease-out';
                pulse.style.transform = 'scale(2.5)';
                pulse.style.opacity = '0';

                setTimeout(() => pulse.remove(), 800);
            }, i * 150);
        }
    }

    function createNodeVibration(nodeId, strength) {
        const positions = memoryNetwork.getPositions([nodeId]);
        const nodePos = memoryNetwork.canvasToDOM(positions[nodeId]);
        const container = document.getElementById('memory-network');
        const containerRect = container.getBoundingClientRect();
        
        const vibration = document.createElement('div');
        // Get the actual node size for proportional vibration
        const node = networkData.nodes.find(n => n.id === nodeId);
        const nodeSize = node ? node.size : 35; // Default size if node not found
        
        // Make vibration proportional to node size (1.0x to 1.8x the node size)
        const vibrationMultiplier = 1.0 + (strength * 0.8); // Range: 1.0x to 1.8x
        const size = Math.max(nodeSize * vibrationMultiplier, 40); // Minimum 40px for visibility
        
        vibration.style.position = 'fixed';
        vibration.style.left = (containerRect.left + nodePos.x - size/2) + 'px';
        vibration.style.top = (containerRect.top + nodePos.y - size/2) + 'px';
        vibration.style.width = size + 'px';
        vibration.style.height = size + 'px';
        vibration.style.borderRadius = '50%';
        vibration.style.background = `radial-gradient(circle, rgba(255,255,255,${strength * 0.8}) 0%, rgba(255,215,0,${strength * 0.6}) 50%, transparent 100%)`;
        vibration.style.pointerEvents = 'none';
        vibration.style.zIndex = '994';
        vibration.style.opacity = Math.min(0.9, strength * 1.2);
        document.body.appendChild(vibration);

        const vibrationIntensity = Math.max(2, strength * 8);
        const vibrationDuration = Math.max(200, strength * 400);
        const vibrationSteps = 12;
        
        let step = 0;
        const vibrateInterval = setInterval(() => {
            if (step >= vibrationSteps) {
                clearInterval(vibrateInterval);
                vibration.style.transition = 'all 0.2s ease-out';
                vibration.style.opacity = '0';
                vibration.style.transform = 'scale(0.5)';
                setTimeout(() => vibration.remove(), 200);
                return;
            }
            
            const offsetX = (Math.random() - 0.5) * vibrationIntensity;
            const offsetY = (Math.random() - 0.5) * vibrationIntensity;
            const scale = 1 + (Math.random() - 0.5) * 0.3 * strength;
            
            vibration.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scale})`;
            
            step++;
        }, vibrationDuration / vibrationSteps);
    }

    let glowDecayInterval = null;

    function startGlowDecay() {
        if (glowDecayInterval) {
            clearInterval(glowDecayInterval);
        }
        
        glowDecayInterval = setInterval(() => {
            let hasActiveGlows = false;
            
            for (const nodeId in nodeGlowLevels) {
                if (nodeGlowLevels[nodeId] > 0.001) {
                    nodeGlowLevels[nodeId] *= 0.3;
                    updateNodeGlow(nodeId);
                    hasActiveGlows = true;
                } else if (nodeGlowLevels[nodeId] > 0) {
                    nodeGlowLevels[nodeId] = 0;
                    const existingGlow = document.getElementById(`node-glow-${nodeId}`);
                    if (existingGlow) {
                        existingGlow.style.transition = 'opacity 0.2s ease-out';
                        existingGlow.style.opacity = '0';
                        setTimeout(() => existingGlow.remove(), 200);
                    }
                }
            }
            
            if (!hasActiveGlows) {
                clearInterval(glowDecayInterval);
                glowDecayInterval = null;
            }
        }, 100);
    }

    function easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }

    function getCurvedPathPosition(fromPos, toPos, progress, fromId, toId) {
        const edge = networkData.edges.find(e => 
            (e.from === fromId && e.to === toId) || 
            (e.from === toId && e.to === fromId)
        );
        
        if (!edge) {
            const currentX = fromPos.x + (toPos.x - fromPos.x) * progress;
            const currentY = fromPos.y + (toPos.y - fromPos.y) * progress;
            return { currentX, currentY };
        }
        
        const dx = toPos.x - fromPos.x;
        const dy = toPos.y - fromPos.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        let curveDirection = -1;
        
        const isReversed = edge.from === toId;
        if (isReversed) {
            curveDirection = 1;
        }
        
        const roundness = 0.25;
        const curveOffset = distance * roundness * curveDirection;
        
        const perpX = -dy / distance;
        const perpY = dx / distance;
        
        const midX = (fromPos.x + toPos.x) / 2 + perpX * curveOffset;
        const midY = (fromPos.y + toPos.y) / 2 + perpY * curveOffset;
        
        const t = progress;
        const currentX = (1 - t) * (1 - t) * fromPos.x + 
                    2 * (1 - t) * t * midX + 
                    t * t * toPos.x;
        const currentY = (1 - t) * (1 - t) * fromPos.y + 
                    2 * (1 - t) * t * midY + 
                    t * t * toPos.y;
        
        return { currentX, currentY };
    }

    // Threshold slider handler
    document.getElementById('threshold-slider').addEventListener('input', function(e) {
        currentThreshold = parseFloat(e.target.value);
        document.getElementById('threshold-value').textContent = currentThreshold.toFixed(2);
        loadMemoryNetwork();
    });

    // Manual refresh button handler
    function refreshMemoryNetworkManual() {
        console.log('🔄 Manual refresh triggered');
        loadMemoryNetwork();
    }

    // Initialize memory network after page load
    setTimeout(() => {
        initializeMemoryNetwork();
        loadMemoryNetwork();
        
        // Note: Real-time memory updates now use immediate temporary nodes instead of polling
        // startNewMemoryPolling(); // Disabled - using immediate temp nodes instead
        
        // Initialize live score updates (disabled by default)
        console.log('🎉 Memory Network initialized! Auto-refresh disabled by default for persistent node positions.');
        console.log('💡 Use the refresh button or enable auto-refresh if needed.');
        console.log('🚀 Real-time memory updates enabled via immediate temporary nodes!');
        console.log('📊 Live score updates available - click "Enable Live Scores" to activate!');
    }, 1000);
    </script>
    ''' 