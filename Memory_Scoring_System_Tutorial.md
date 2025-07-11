# MemoryOS Scoring System Tutorial

## Overview

This document provides a comprehensive guide to the scoring system used in MemoryOS, including how memory scores are calculated, how relevance scores work, and how connections between memories are formed. This system is designed to mimic human memory processes with neural network-like reinforcement learning.

## Table of Contents

1. [Memory Score Calculation](#memory-score-calculation)
2. [Relevance Score System](#relevance-score-system)
3. [Connection Formation](#connection-formation)
4. [Memory Reinforcement](#memory-reinforcement)
5. [Node Size Visualization](#node-size-visualization)
6. [Adjustment Parameters](#adjustment-parameters)
7. [Key Functions Reference](#key-functions-reference)

---

## Memory Score Calculation

### Core Scoring Algorithm

The memory score is calculated in the `_calculate_all_scores_and_connections()` function in `memory-app/backend/memory_manager.py`. Each memory's score is determined by several factors:

#### 1. Connection-Based Scoring
```python
# Base score from connections
for neighbor, sim in connections[i]:
    # Weight stronger connections more heavily
    if sim >= 0.7:
        weight = 3.0  # Strong connections
    elif sim >= 0.5:
        weight = 2.0  # Moderate connections
    else:
        weight = 1.0  # Weak connections
    score += sim * weight
```

**Connection Weighting:**
- **Strong connections (≥0.7)**: Weight = 3.0
- **Moderate connections (≥0.5)**: Weight = 2.0  
- **Weak connections (<0.5)**: Weight = 1.0

#### 2. Hub Bonus
```python
# Bonus for being a hub (connected to many relevant memories)
if connection_count >= 3:
    score += connection_count * 0.1
```

Memories with 3+ connections get a bonus of `0.1 × connection_count`.

#### 3. Content Quality Bonus
```python
# Content quality bonus (longer, more detailed memories)
word_count = len(mem['content'].split())
if word_count >= 10:
    score += 0.2
elif word_count >= 5:
    score += 0.1
```

**Content Quality Rewards:**
- **10+ words**: +0.2 bonus
- **5-9 words**: +0.1 bonus
- **<5 words**: No bonus

### Score Calculation Formula

```
Final Score = (Connection Score × Weight) + Hub Bonus + Content Quality Bonus
```

Where:
- **Connection Score** = Sum of all connection similarities × their respective weights
- **Hub Bonus** = 0.1 × number of connections (if ≥3 connections)
- **Content Quality Bonus** = Based on word count

---

## Relevance Score System

### Search Relevance Calculation

When searching memories, a hybrid scoring system combines semantic similarity with memory importance:

```python
# Hybrid score: semantic relevance + memory importance
final_score = (float(similarity) * 0.7) + (memory.get('score', 0) / 100 * 0.3)
```

**Relevance Score Components:**
- **Semantic Similarity (70%)**: Direct similarity between query and memory content
- **Memory Importance (30%)**: Normalized memory score (score/100)

### Relevance Thresholds

The system uses different similarity thresholds for different purposes:

```python
sim_threshold: Minimum similarity for connections (default 0.35)
- 0.35-0.5: Weak but meaningful connection
- 0.5-0.7: Moderate connection  
- 0.7-0.85: Strong connection
- 0.85+: Very strong connection
```

---

## Connection Formation

### Similarity Matrix Calculation

Connections are formed based on semantic similarity using cosine similarity:

```python
# 1. Calculate similarity matrix using proper cosine similarity
normalized_embeddings = normalize(self.search_embeddings, norm='l2')
sim_matrix = normalized_embeddings @ normalized_embeddings.T
```

### Connection Filtering

The system applies intelligent filtering to avoid false connections:

```python
# Apply stricter similarity filtering
if sim >= sim_threshold:
    # Additional quality check: avoid connecting very short/generic texts
    mem_i_words = len(all_mems[i]['content'].split())
    mem_j_words = len(all_mems[j]['content'].split())
    
    # Require higher similarity for short texts
    min_words = min(mem_i_words, mem_j_words)
    if min_words <= 3:
        required_sim = max(sim_threshold + 0.15, 0.6)  # Much higher for very short texts
    elif min_words <= 5:
        required_sim = sim_threshold + 0.1  # Moderately higher for short texts
    else:
        required_sim = sim_threshold  # Standard threshold
```

**Dynamic Threshold Adjustment:**
- **≤3 words**: +0.15 to threshold (minimum 0.6)
- **≤5 words**: +0.1 to threshold
- **>5 words**: Standard threshold

---

## Memory Reinforcement

### Reinforcement Algorithm

When memories are recalled during search, they trigger a reinforcement cascade:

```python
def _reinforce_recalled_memories(self, recalled_memories):
    """
    Reinforce memories that were recalled by:
    1. Adding relevance score to the recalled memory's score (100%)
    2. Adding 30% to immediate neighbors (connected memories)
    3. Adding 30% of that (9%) to neighbors of neighbors
    4. Adding 30% of that (2.7%) to third-degree neighbors
    """
```

### Reinforcement Cascade

**Reinforcement Levels:**
1. **Recalled Memory**: 100% of relevance score
2. **1st Degree Neighbors**: 30% of base reinforcement
3. **2nd Degree Neighbors**: 9% of base reinforcement (30% of 30%)
4. **3rd Degree Neighbors**: 2.7% of base reinforcement (30% of 9%)

### Reinforcement Calculation

```python
base_reinforcement = min(1.0, max(0.0, relevance_score))
neighbor_reinforcement = base_reinforcement * 0.3
second_degree_reinforcement = neighbor_reinforcement * 0.3
third_degree_reinforcement = second_degree_reinforcement * 0.3
```

---

## Node Size Visualization

### Proportional Node Sizing

Node sizes in the visualization are calculated using a sophisticated proportional system:

```javascript
function calculateProportionalNodeSize(score, allScores) {
    // Apply logarithmic scaling to handle infinite growth
    const logMin = Math.log(minScore + 1);
    const logMax = Math.log(maxScore + 1);
    const logScore = Math.log(score + 1);
    
    // Calculate relative position (0-1)
    const relativePosition = (logScore - logMin) / (logMax - logMin);
    
    // Apply sigmoid function for smooth distribution
    const sigmoid = 1 / (1 + Math.exp(-10 * (relativePosition - 0.5)));
    
    // Map to size range
    const minSize = 25;  // Minimum visible size
    const maxSize = 80;  // Maximum size cap
    const sizeRange = maxSize - minSize;
    
    return minSize + (sigmoid * sizeRange);
}
```

### Size Calculation Process

1. **Logarithmic Scaling**: Prevents infinite growth of high-scoring nodes
2. **Relative Positioning**: Normalizes scores to 0-1 range
3. **Sigmoid Function**: Creates smooth, natural distribution
4. **Size Mapping**: Maps to visual size range (25-80 pixels)

---

## Adjustment Parameters

### Key Parameters You Can Modify

#### 1. Connection Threshold (`sim_threshold`)
**Location**: `_calculate_all_scores_and_connections(sim_threshold=0.35)`

**Effects:**
- **Lower values (0.2-0.3)**: More connections, denser network
- **Higher values (0.5-0.7)**: Fewer connections, sparser network
- **Default**: 0.35 (balanced)

#### 2. Connection Weights
**Location**: Connection scoring section in `_calculate_all_scores_and_connections()`

```python
if sim >= 0.7:
    weight = 3.0  # Strong connections
elif sim >= 0.5:
    weight = 2.0  # Moderate connections
else:
    weight = 1.0  # Weak connections
```

**Adjustment Effects:**
- **Higher weights**: Emphasize strong connections more
- **Lower weights**: More balanced scoring

#### 3. Hub Bonus Multiplier
**Location**: Hub bonus calculation

```python
if connection_count >= 3:
    score += connection_count * 0.1  # Adjust this multiplier
```

**Adjustment Effects:**
- **Higher multiplier**: Rewards highly connected memories more
- **Lower multiplier**: Reduces hub dominance

#### 4. Content Quality Bonuses
**Location**: Content quality bonus section

```python
if word_count >= 10:
    score += 0.2  # Adjust these values
elif word_count >= 5:
    score += 0.1
```

#### 5. Reinforcement Decay Rate
**Location**: `_reinforce_recalled_memories()`

```python
neighbor_reinforcement = base_reinforcement * 0.3  # Adjust this rate
```

**Adjustment Effects:**
- **Higher rate (0.5)**: Stronger reinforcement spread
- **Lower rate (0.1)**: More localized reinforcement

#### 6. Search Score Weights
**Location**: `search_memories()` function

```python
final_score = (float(similarity) * 0.7) + (memory.get('score', 0) / 100 * 0.3)
```

**Adjustment Effects:**
- **Higher similarity weight**: More emphasis on direct relevance
- **Higher importance weight**: More emphasis on memory scores

---

## Key Functions Reference

### Core Scoring Functions

#### `_calculate_all_scores_and_connections(sim_threshold=0.35)`
**Purpose**: Main function that calculates all memory scores and connections
**Parameters**:
- `sim_threshold`: Minimum similarity for connections (default: 0.35)
**Returns**: `(connections, sim_matrix)`

#### `_reinforce_recalled_memories(recalled_memories)`
**Purpose**: Reinforces memories that were recalled during search
**Parameters**:
- `recalled_memories`: List of (memory_id, relevance_score) tuples
**Effects**: Updates memory scores through reinforcement cascade

#### `search_memories(query, top_k=10, min_relevance=0.2)`
**Purpose**: Searches memories with hybrid scoring
**Parameters**:
- `query`: Search query string
- `top_k`: Number of results to return (default: 10)
- `min_relevance`: Minimum relevance threshold (default: 0.2)
**Returns**: List of scored memory results

### Visualization Functions

#### `calculateProportionalNodeSize(score, allScores)`
**Purpose**: Calculates node size for visualization
**Parameters**:
- `score`: Individual memory score
- `allScores`: Array of all memory scores
**Returns**: Pixel size for node visualization

#### `recalculateAllNodeSizes()`
**Purpose**: Recalculates all node sizes when scores change
**Effects**: Updates network visualization with new sizes

### Utility Functions

#### `add_memory(content, tags=None)`
**Purpose**: Adds new memory to the system
**Parameters**:
- `content`: Memory content text
- `tags`: Optional tags list
**Effects**: Triggers score recalculation

#### `boost_memory(memory_id, boost_factor=1.2)`
**Purpose**: Manually boosts a memory's score
**Parameters**:
- `memory_id`: ID of memory to boost
- `boost_factor`: Multiplier for score increase (default: 1.2)

---

## Example Adjustments

### Making the Network More Connected
```python
# In _calculate_all_scores_and_connections()
sim_threshold = 0.25  # Lower threshold for more connections
```

### Emphasizing Strong Connections More
```python
# In connection scoring section
if sim >= 0.7:
    weight = 5.0  # Increased from 3.0
elif sim >= 0.5:
    weight = 3.0  # Increased from 2.0
else:
    weight = 1.0
```

### Increasing Hub Bonus
```python
# In hub bonus calculation
if connection_count >= 3:
    score += connection_count * 0.2  # Increased from 0.1
```

### Stronger Reinforcement Spread
```python
# In _reinforce_recalled_memories()
neighbor_reinforcement = base_reinforcement * 0.5  # Increased from 0.3
```

### More Emphasis on Memory Importance in Search
```python
# In search_memories()
final_score = (float(similarity) * 0.5) + (memory.get('score', 0) / 100 * 0.5)
```

---

## Best Practices

1. **Start with Default Values**: The default parameters are well-tuned for most use cases
2. **Adjust Gradually**: Make small changes and observe the effects
3. **Monitor Network Density**: Too many connections can make visualization cluttered
4. **Balance Scoring Components**: Ensure no single factor dominates the scoring
5. **Test with Real Data**: Always test adjustments with your actual memory data
6. **Consider Performance**: Lower thresholds create more connections but slower performance

---

## Troubleshooting

### Common Issues and Solutions

#### Network Too Sparse
- **Problem**: Few connections between memories
- **Solution**: Lower `sim_threshold` (try 0.25-0.3)

#### Network Too Dense
- **Problem**: Too many connections, visualization cluttered
- **Solution**: Increase `sim_threshold` (try 0.4-0.5)

#### High-Scoring Memories Dominate
- **Problem**: Few memories have very high scores
- **Solution**: Reduce connection weights or hub bonus multiplier

#### Low-Quality Connections
- **Problem**: Irrelevant memories being connected
- **Solution**: Increase similarity thresholds for short texts

#### Reinforcement Too Strong
- **Problem**: Scores growing too quickly
- **Solution**: Reduce reinforcement decay rate (0.3 → 0.2)

---

This tutorial provides a comprehensive understanding of the MemoryOS scoring system. You can now confidently adjust the parameters to suit your specific needs and create the desired memory network behavior. 