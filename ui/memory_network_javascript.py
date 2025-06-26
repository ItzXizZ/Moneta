#!/usr/bin/env python3

# Memory Network JavaScript Component with advanced neural animations
MEMORY_NETWORK_JAVASCRIPT = '''
<script>
// Memory Network Variables
let memoryNetwork = null;
let networkData = { nodes: [], edges: [] };
let activeMemories = new Set();
let currentThreshold = 0.35;

// Advanced Signal Trail System for Neural-like Visualization
let signalTrails = [];
let sparkleSystem = [];
let trailAnimationActive = false;
let nodeGlowLevels = {}; // Track accumulating glow for each node
let activeSignals = 0;

// Memory Network Functions
function initializeMemoryNetwork() {
    const container = document.getElementById('memory-network');
    
    // Clear any loading text first
    container.innerHTML = '<div class="memory-activity-indicator" id="activity-indicator">🔥 Memory Activity</div>';
    
    const options = {
        nodes: {
            shape: 'dot',
            scaling: { min: 20, max: 55 },
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
                centralGravity: 0.1,
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
    
    // Gently position network towards the right
    memoryNetwork.on('stabilizationIterationsDone', function() {
        setTimeout(() => {
            // Just adjust the view to show the right side of the network
            const containerRect = container.getBoundingClientRect();
            const rightOffset = containerRect.width * 0.2; // Gentle offset to the right
            
            memoryNetwork.moveTo({
                position: { x: rightOffset, y: 0 },
                scale: 1.0,
                animation: {
                    duration: 1000,
                    easingFunction: 'easeInOutCubic'
                }
            });
        }, 500);
    });
    
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

    memoryNetwork.on('dragEnd', function(params) {
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

async function loadMemoryNetwork() {
    try {
        const threshold = parseFloat(document.getElementById('threshold-slider').value);
        const response = await fetch(`/memory-network?threshold=${threshold}`);
        const data = await response.json();
        
        // Initialize node glow levels
        data.nodes.forEach(node => {
            nodeGlowLevels[node.id] = 0;
        });
        
        // Create nodes with elegant Apple-style design and slight rightward positioning
        networkData.nodes = data.nodes.map((node, index) => {
            const intensity = Math.max(0.7, Math.min(1, node.score / 100));
            const size = Math.max(30, Math.min(65, 30 + node.score * 0.45));
            
            // Add a slight rightward bias to initial positioning
            const rightwardBias = Math.random() * 200 +600; // Random position between 100-300 pixels right
            
            return {
                id: node.id,
                label: node.label.length > 25 ? node.label.substring(0, 25) + '…' : node.label,
                title: node.label,
                size: size,
                x: rightwardBias, // Initial rightward positioning
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
        
        networkData.edges = data.edges.map(edge => ({
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
        
        // Update network
        if (memoryNetwork) {
            memoryNetwork.setData(networkData);
        }
        
        // Update stats
        document.getElementById('memory-count').textContent = data.nodes.length;
        document.getElementById('connection-count').textContent = data.edges.length;
        document.getElementById('active-memories').textContent = activeMemories.size;
        
        console.log(`🧠 Loaded ${data.nodes.length} memories, ${data.edges.length} connections`);
        
        // Start glow decay system
        startGlowDecay();
        
    } catch (error) {
        console.error('Error loading memory network:', error);
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
    
    const size = Math.max(60, 120 * glowLevel);
    
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
            const size = 80 * strength;
            
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
    const size = Math.max(40, 60 * strength);
    
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

// Initialize memory network after page load
setTimeout(() => {
    initializeMemoryNetwork();
    loadMemoryNetwork();
    
    // Auto-refresh network every 30 seconds
    setInterval(loadMemoryNetwork, 30000);
}, 1000);
</script>
''' 