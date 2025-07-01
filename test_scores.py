#!/usr/bin/env python3

def calculate_proportional_node_size(score, all_scores):
    """Python version of the JavaScript proportional sizing function for testing"""
    if not all_scores or len(all_scores) == 0:
        return 40  # Default size if no scores available
    
    # Find min/max scores in the dataset
    min_score = min(all_scores)
    max_score = max(all_scores)
    
    # Handle edge case where all scores are the same
    if min_score == max_score:
        return 40  # Default size for uniform scores
    
    # Apply logarithmic scaling to handle infinite growth
    import math
    log_min = math.log(min_score + 1)
    log_max = math.log(max_score + 1)
    log_score = math.log(score + 1)
    
    # Calculate relative position (0-1)
    relative_position = (log_score - log_min) / (log_max - log_min)
    
    # Apply sigmoid function for smooth distribution
    sigmoid = 1 / (1 + math.exp(-10 * (relative_position - 0.5)))
    
    # Map to size range with minimum visibility guarantee
    min_size = 30  # Increased minimum visible size
    max_size = 70  # Slightly reduced maximum size cap
    size_range = max_size - min_size
    
    calculated_size = min_size + (sigmoid * size_range)
    
    # Ensure the size is within reasonable bounds
    final_size = max(30, min(70, calculated_size))
    
    return final_size

# Test with the actual score range from the API
actual_scores = [0.0, 1.17, 1.61, 2.71, 2.81, 3.0, 3.26, 4.07, 4.23, 5.2, 5.25, 6.02, 6.48, 6.77, 7.7, 7.85]

print("🧪 Testing with actual score range from API")
print("=" * 50)
print(f"Score range: {min(actual_scores)} - {max(actual_scores)}")
print()

for score in sorted(actual_scores):
    size = calculate_proportional_node_size(score, actual_scores)
    print(f"Score {score:4.2f} → Size {size:5.1f}px")

print()
print("✅ This should give much better visibility!") 