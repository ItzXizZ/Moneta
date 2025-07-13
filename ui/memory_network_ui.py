#!/usr/bin/env python3

# Memory Network UI Component with advanced neural animations
MEMORY_NETWORK_UI_TEMPLATE = '''
<!-- Memory Network Section -->
<div class="memory-network-container" id="memory-network-container">
    <div class="memory-network-header">
        <h3>Moneta: The Future of Memory</h3>
        <div class="network-controls">
            <button id="toggle-score-updates" class="btn btn-success" onclick="toggleLiveScoreUpdates()">
                📊 Enable Live Scores
            </button>
            <button id="auto-refresh-toggle" class="btn btn-secondary" onclick="toggleAutoRefresh()">
                🔄 Auto Refresh
            </button>
            <button id="save-scores-btn" class="btn btn-info" onclick="saveScoresToJSON()">
                💾 Save Scores
            </button>
        </div>
        <div class="threshold-controls">
            <label for="threshold-slider" style="color: var(--gray-400); font-size: 0.9rem;">Threshold:</label>
            <input type="range" id="threshold-slider" class="threshold-slider" min="0.1" max="0.8" step="0.05" value="0.35">
            <span id="threshold-value" style="color: var(--primary-400); font-size: 0.9rem;">0.35</span>
        </div>
    </div>
    
    <div class="memory-network-stats">
        <div class="stat-item">
            <span>Memories: </span><span class="stat-value" id="memory-count">0</span>
        </div>
        <div class="stat-item">
            <span>Connections: </span><span class="stat-value" id="connection-count">0</span>
        </div>
        <div class="stat-item">
            <span>Active: </span><span class="stat-value" id="active-memories">0</span>
        </div>
        <div class="stat-item">
            <span>Last: </span><span class="stat-value" id="last-search">None</span>
        </div>
    </div>
    
    <div id="memory-network">
        <div class="network-loading">Loading memory network...</div>
        <div class="memory-activity-indicator" id="activity-indicator">🔥 Memory Activity</div>
    </div>
</div>
'''

MEMORY_NETWORK_CSS = '''
/* Memory Network Visualization Styles */
.memory-network-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: transparent;
    backdrop-filter: none;
    border: none;
    border-radius: 0;
    padding: 0;
    box-shadow: none;
    display: flex;
    flex-direction: column;
    overflow: visible;
    z-index: 1;
    pointer-events: auto;
}

.memory-network-header {
    position: fixed;
    top: 20px;
    right: 20px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 16px 20px;
    box-shadow: 
        0 8px 32px rgba(0, 0, 0, 0.4),
        0 0 0 1px rgba(255, 255, 255, 0.1),
        inset 0 1px 0 rgba(255, 255, 255, 0.15);
    z-index: 1000;
    pointer-events: auto;
}

.memory-network-header h3 {
    color: var(--primary-300);
    margin: 0;
    font-size: 1.2rem;
    font-weight: 500;
}

.network-controls {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.network-controls .btn {
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    border-radius: 8px;
    padding: 6px 12px;
    color: rgba(255, 255, 255, 0.9);
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s var(--ease-smooth);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.network-controls .btn:hover {
    background: rgba(168, 85, 247, 0.2);
    border-color: var(--primary-400);
    transform: translateY(-1px);
    box-shadow: 
        0 4px 12px rgba(168, 85, 247, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.network-controls .btn-success {
    background: rgba(34, 197, 94, 0.2);
    border-color: rgba(34, 197, 94, 0.5);
}

.network-controls .btn-success:hover {
    background: rgba(34, 197, 94, 0.3);
    border-color: rgba(34, 197, 94, 0.7);
}

.network-controls .btn-warning {
    background: rgba(245, 158, 11, 0.2);
    border-color: rgba(245, 158, 11, 0.5);
}

.network-controls .btn-warning:hover {
    background: rgba(245, 158, 11, 0.3);
    border-color: rgba(245, 158, 11, 0.7);
}

.network-controls .btn-secondary {
    background: rgba(107, 114, 128, 0.2);
    border-color: rgba(107, 114, 128, 0.5);
}

.network-controls .btn-secondary:hover {
    background: rgba(107, 114, 128, 0.3);
    border-color: rgba(107, 114, 128, 0.7);
}

.network-controls .btn-info {
    background: rgba(59, 130, 246, 0.2);
    border-color: rgba(59, 130, 246, 0.5);
}

.network-controls .btn-info:hover {
    background: rgba(59, 130, 246, 0.3);
    border-color: rgba(59, 130, 246, 0.7);
}

.threshold-controls {
    display: none; /* Hidden threshold slider container */
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
}

.threshold-slider {
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    padding: 8px 12px;
    color: rgba(255, 255, 255, 0.9);
    font-size: 0.875rem;
    transition: all 0.3s var(--ease-smooth);
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
}

.threshold-slider:focus {
    outline: none;
    border-color: var(--glass-border-strong);
    box-shadow: 
        0 0 0 2px rgba(168, 85, 247, 0.15),
        inset 0 2px 4px rgba(0, 0, 0, 0.15);
}

.memory-network-stats {
    position: fixed;
    bottom: 20px;
    right: 20px;
    display: flex;
    gap: 8px;
    font-size: 0.8rem;
    color: var(--gray-400);
    flex-wrap: wrap;
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    padding: 12px 16px;
    box-shadow: 
        0 8px 32px rgba(0, 0, 0, 0.4),
        0 0 0 1px rgba(255, 255, 255, 0.1),
        inset 0 1px 0 rgba(255, 255, 255, 0.15);
    z-index: 1000;
    pointer-events: auto;
}

.stat-item {
    background: rgba(31, 41, 55, 0.8);
    backdrop-filter: var(--glass-blur);
    padding: 8px 12px;
    border-radius: 8px;
    border: 1px solid var(--glass-border);
}

.stat-value {
    color: var(--primary-300);
    font-weight: 500;
}

#memory-network {
    position: absolute;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    border: none;
    border-radius: 0;
    background: radial-gradient(ellipse at center, rgba(10, 10, 10, 0.98) 0%, rgba(17, 24, 39, 0.95) 60%, rgba(5, 5, 5, 0.99) 100%);
    backdrop-filter: none;
    overflow: hidden;
    box-shadow: none;
    z-index: 0;
}

#memory-network::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
        radial-gradient(circle at 20% 20%, rgba(255, 215, 0, 0.02) 0%, transparent 50%),
        radial-gradient(circle at 80% 80%, rgba(168, 85, 247, 0.03) 0%, transparent 50%),
        radial-gradient(circle at 40% 70%, rgba(255, 215, 0, 0.01) 0%, transparent 30%);
    pointer-events: none;
    z-index: 1;
}

.memory-activity-indicator {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: linear-gradient(45deg, #ffd700, #ffed4e);
    color: #46096b;
    padding: 12px 20px;
    border-radius: 16px;
    font-size: 1rem;
    font-weight: 600;
    opacity: 0;
    transition: all 0.4s ease;
    border: 2px solid rgba(255, 215, 0, 0.6);
    box-shadow: 0 0 30px rgba(255, 215, 0, 0.6);
    z-index: 2000;
    pointer-events: none;
}

.memory-activity-indicator.active {
    opacity: 1;
    animation: neuralPulse 1.5s ease-in-out infinite;
}

@keyframes neuralPulse {
    0%, 100% { 
        transform: scale(1); 
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
    }
    50% { 
        transform: scale(1.05); 
        box-shadow: 0 0 25px rgba(255, 215, 0, 0.8);
    }
}

.network-loading {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: var(--gray-400);
    font-style: italic;
    z-index: 2;
    display: none;
}

.persistent-node-glow {
    transition: all 0.3s ease-out;
    animation: gentle-pulse 3s ease-in-out infinite;
}

@keyframes gentle-pulse {
    0%, 100% { 
        transform: scale(1); 
        opacity: var(--glow-opacity, 0.6); 
    }
    50% { 
        transform: scale(1.4); 
        opacity: calc(var(--glow-opacity, 1) * 1.8); 
    }
}

@media (max-width: 1024px) {
    .memory-network-container {
        min-height: 300px;
    }
    
    #memory-network {
        height: 240px;
    }
}

@media (max-width: 768px) {
    .memory-network-stats {
        flex-wrap: wrap;
        gap: 8px;
    }
    
    .stat-item {
        font-size: 0.7rem;
        padding: 4px 8px;
    }
}
'''

# JavaScript will be included separately in the chat JavaScript file