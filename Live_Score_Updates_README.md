# Live Score Updates for MemoryOS

## Overview

The Live Score Updates feature allows you to see memory scores change in real-time as the system learns and reinforces connections. Node sizes and colors will animate smoothly as scores update, providing a dynamic visualization of the memory network's evolution.

## Features

### 🎯 Real-Time Score Updates
- **Automatic Updates**: Scores update every 3 seconds when enabled
- **Smooth Animations**: Node sizes and colors transition smoothly
- **Visual Feedback**: Changes are immediately visible in the network

### 📊 Dynamic Node Sizing
- **Proportional Scaling**: Node sizes adjust based on relative score importance
- **Smooth Transitions**: Size changes animate over 1 second
- **Color Intensity**: Node colors become more intense with higher scores

### 🔄 Intelligent Updates
- **Change Detection**: Only updates when scores change significantly (>0.01)
- **Performance Optimized**: Minimal network traffic and CPU usage
- **Timestamp Tracking**: Prevents unnecessary updates

## How to Use

### 1. Enable Live Score Updates
1. Open the Memory Network visualization
2. Look for the control panel in the top-right corner
3. Click the **"📊 Enable Live Scores"** button
4. The button will change to **"⏸️ Pause Score Updates"** when active

### 2. Watch the Changes
- **Node Sizes**: Will smoothly animate as scores change
- **Node Colors**: Intensity will adjust based on score values
- **Console Logs**: Check browser console for detailed update information

### 3. Trigger Score Changes
To see live updates in action, try:
- **Adding new memories** through the chat interface
- **Searching for memories** (this triggers reinforcement)
- **Interacting with the network** (clicking nodes, etc.)

## Technical Details

### Backend API
- **Endpoint**: `/score-updates`
- **Method**: GET
- **Response**: JSON with memory scores and timestamp
- **Frequency**: Called every 3 seconds when enabled

### Frontend Implementation
- **Polling Interval**: 3 seconds
- **Animation Duration**: 1 second for smooth transitions
- **Change Threshold**: 0.01 (prevents micro-updates)

### Score Calculation
Scores are calculated based on:
1. **Connection Strength**: Stronger connections = higher scores
2. **Hub Bonus**: Highly connected memories get bonuses
3. **Content Quality**: Longer, more detailed memories score higher
4. **Reinforcement**: Recalled memories and their neighbors get score boosts

### Score Preservation System
- **Reinforcement Protection**: Reinforcement scores are preserved during normal operations
- **Hybrid Scoring**: Combines base connection scores with existing reinforcement
- **Manual Override**: Use `/recalculate-scores` endpoint to reset all scores when needed
- **Smart Updates**: Only recalculates when explicitly requested or adding new memories

## Configuration

### Adjusting Update Frequency
To change how often scores update, modify the polling interval:

```javascript
// In ui/memory_network_javascript.py
scoreUpdateInterval = setInterval(checkForScoreUpdates, 3000); // 3 seconds
```

### Animation Settings
To adjust animation smoothness:

```javascript
// Animation duration (milliseconds)
const animationDuration = 1000; // 1 second

// Animation steps
const steps = 20; // More steps = smoother animation
```

### Change Threshold
To adjust sensitivity to score changes:

```javascript
// Only update if change is significant
if (Math.abs(newScore - oldScore) > 0.01) { // Adjust this value
```

## Testing

### Run the Test Script
Use the provided test script to demonstrate live updates:

```bash
python test_live_score_updates.py
```

This script will:
1. Add test memories to the system
2. Trigger score changes through searches
3. Show before/after score comparisons
4. Demonstrate the reinforcement mechanism

### Manual Testing
1. Start the MemoryOS backend
2. Open the memory network visualization
3. Enable live score updates
4. Add memories or perform searches
5. Watch for real-time changes

## Troubleshooting

### Live Updates Not Working
- **Check Console**: Look for error messages in browser console
- **Verify Backend**: Ensure the backend is running on port 5000
- **Network Issues**: Check if `/score-updates` endpoint is accessible

### No Score Changes Visible
- **Enable Updates**: Make sure live score updates are enabled
- **Add Activity**: Try adding memories or searching to trigger changes
- **Check Threshold**: Verify that score changes exceed the 0.01 threshold
- **Reinforcement Preserved**: Scores are now preserved and won't be overwritten

### Performance Issues
- **Reduce Frequency**: Increase polling interval (e.g., 5000ms instead of 3000ms)
- **Limit Animations**: Reduce animation steps for faster updates
- **Disable Auto-refresh**: Turn off auto-refresh if both are enabled

### Score Preservation Issues
- **Reinforcement Overwritten**: If scores keep resetting, run the preservation test
- **Manual Recalculation**: Use `/recalculate-scores` endpoint to reset all scores
- **Test Script**: Run `test_reinforcement_preservation.py` to verify the fix

## Integration with Other Features

### Auto-Refresh Compatibility
Live score updates work alongside auto-refresh:
- **Live Updates**: Update scores every 3 seconds
- **Auto-Refresh**: Reload entire network every 30 seconds
- **Coordination**: Both can be enabled simultaneously

### Memory Reinforcement
Live updates enhance the reinforcement system:
- **Immediate Feedback**: See reinforcement effects in real-time
- **Visual Learning**: Understand how connections strengthen
- **Network Evolution**: Watch the memory network grow and adapt

## Future Enhancements

### Planned Features
- **WebSocket Support**: Real-time updates without polling
- **Customizable Intervals**: User-configurable update frequencies
- **Score History**: Track score changes over time
- **Advanced Animations**: More sophisticated visual effects

### Performance Optimizations
- **Delta Updates**: Only send changed scores
- **Batch Processing**: Group multiple updates together
- **Smart Polling**: Adaptive intervals based on activity

## API Reference

### GET /score-updates
Returns current memory scores for live updates.

**Response:**
```json
{
  "success": true,
  "updates": [
    {
      "id": "mem_123",
      "score": 15.67,
      "content": "Memory content..."
    }
  ],
  "timestamp": 1640995200.123
}
```

**Parameters:**
- None

**Headers:**
- `Content-Type: application/json`

## Contributing

To contribute to the live score update feature:

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Test thoroughly**
5. **Submit a pull request**

### Development Guidelines
- **Performance**: Keep polling intervals reasonable
- **User Experience**: Ensure smooth animations
- **Error Handling**: Gracefully handle network issues
- **Documentation**: Update this README for new features

---

## Support

For issues or questions about live score updates:
- **Check the console** for error messages
- **Review this documentation** for configuration options
- **Test with the provided script** to verify functionality
- **Report bugs** with detailed reproduction steps

The live score update feature brings the memory network to life, showing the dynamic nature of learning and memory formation in real-time! 🧠✨ 