# Offline Mode & Fallback Timing - FlexTraff Backend

## Overview

When the Raspberry Pi loses internet connection or the vehicle detection system becomes unavailable, the traffic control system automatically switches to a **safe offline mode** with default maximum cycle times. This ensures traffic flow continues safely without real-time optimization.

## When Fallback Mode Activates

The system switches to offline/fallback mode when:

1. **Internet Connection Lost** - Raspberry Pi cannot reach the backend server
2. **Vehicle Detection Offline** - RFID scanners or detection system fails
3. **Backend Server Unreachable** - Communication with backend server fails
4. **Invalid Vehicle Data** - Null or corrupted vehicle detection data received

## Fallback Mode Behavior

### Traffic Light Timing

When in fallback mode, all lanes receive **equal maximum green time**:

```
Per Lane:
  - Green Time: 90 seconds (maximum)
  - Yellow Time: 5 seconds
  - Red Time: Remaining cycle time from other lanes
  
Total Cycle Time: 380 seconds
  = (4 lanes × 90s green) + (4 lanes × 5s yellow)
  = 360s + 20s
  = 380s
```

### Safety Features

- ✅ **Equal Distribution** - All lanes treated equally for fairness
- ✅ **Maximum Green Time** - Gives sufficient time for all traffic to clear
- ✅ **Fixed Yellow Phase** - Standard 5-second yellow for all lanes
- ✅ **No Optimization** - No real-time vehicle counting needed
- ✅ **Safe Default** - Conservative timing prevents congestion

## Implementation Details

### Getting Fallback Times

```python
from app.services.traffic_calculator import TrafficCalculator

calculator = TrafficCalculator()

# Get fallback times (no parameters needed)
green_times, cycle_time = calculator.get_fallback_times()
# Returns: ([90, 90, 90, 90], 380)
```

### Using Fallback-Aware Calculation

```python
from app.services.traffic_calculator import TrafficCalculator

calculator = TrafficCalculator()

# Automatic fallback if internet is lost
lane_counts = [25, 22, 28, 24]
green_times, cycle_time, is_using_fallback = await calculator.calculate_green_times_with_fallback(
    lane_counts,
    is_offline=False  # Will auto-detect if offline
)

if is_using_fallback:
    print("⚠️ Using fallback mode")
else:
    print("✅ Using adaptive mode")
```

### Connectivity Manager

```python
from app.services.connectivity_manager import ConnectivityManager

conn_manager = ConnectivityManager(check_interval=30)  # Check every 30 seconds

# Check overall status
status = await conn_manager.update_connectivity_status(
    backend_url="https://your-backend.com",
    detection_endpoint="http://raspberry-pi:8000/detect"
)

if not status["is_online"]:
    print("🔴 System offline - using fallback mode")
    # Use get_fallback_times()
```

## API Integration

### FastAPI Endpoint Example

```python
from fastapi import APIRouter
from app.services.traffic_calculator import TrafficCalculator
from app.services.connectivity_manager import ConnectivityManager

router = APIRouter()
calculator = TrafficCalculator()
conn_manager = ConnectivityManager()

@router.post("/calculate-timing")
async def calculate_timing(lane_counts: list, junction_id: int = None):
    """Calculate traffic light timing with automatic fallback"""
    
    # Check connectivity first
    status = await conn_manager.update_connectivity_status()
    
    # Use calculate_green_times_with_fallback
    green_times, cycle_time, is_fallback = await calculator.calculate_green_times_with_fallback(
        lane_counts,
        junction_id=junction_id,
        is_offline=not status["is_online"]
    )
    
    return {
        "green_times": green_times,
        "cycle_time": cycle_time,
        "using_fallback": is_fallback,
        "mode": "offline" if is_fallback else "online",
        "connectivity": status
    }

@router.get("/fallback-info")
async def get_fallback_info():
    """Get fallback mode information"""
    return calculator.get_fallback_info()

@router.get("/connectivity-status")
async def get_connectivity():
    """Get current connectivity status"""
    return conn_manager.get_connectivity_status()
```

## Database Updates

### Add to traffic_cycles table

When storing cycles in offline mode, include:

```sql
ALTER TABLE traffic_cycles ADD COLUMN IF NOT EXISTS is_offline_mode boolean DEFAULT false;
ALTER TABLE traffic_cycles ADD COLUMN IF NOT EXISTS fallback_reason text;

-- Example insert
INSERT INTO traffic_cycles (
    junction_id, 
    cycle_start_time,
    total_cycle_time,
    lane_1_green_time, lane_2_green_time, lane_3_green_time, lane_4_green_time,
    lane_1_yellow_time, lane_2_yellow_time, lane_3_yellow_time, lane_4_yellow_time,
    is_offline_mode,
    fallback_reason
) VALUES (
    1,
    NOW(),
    380,
    90, 90, 90, 90,
    5, 5, 5, 5,
    true,
    'Internet connection lost'
);
```

## Monitoring & Logging

The system logs all mode transitions:

```
[INFO] ✅ Online mode: Calculated adaptive timing for [25, 22, 28, 24] vehicles
[WARNING] ⚠️ FALLBACK MODE ACTIVATED: Using offline/safe timing...
[WARNING] ❌ No internet connection detected
[WARNING] ⚠️ CONNECTIVITY LOST - Switching to offline/fallback mode
[INFO] ✅ All systems online - Using adaptive traffic timing
```

## Testing

Run offline mode tests:

```bash
# Run all offline mode tests
pytest tests/test_offline_mode.py -v

# Run specific test
pytest tests/test_offline_mode.py::TestOfflineMode::test_fallback_times_basic -v
```

## Configuration

### Custom Fallback Times

You can customize fallback behavior:

```python
# Create calculator with custom parameters
calculator = TrafficCalculator(
    min_time=15,      # Minimum green time
    max_time=90,      # Maximum green time (used in fallback)
    base_cycle_time=120
)

# Fallback will use the max_time (90s) for each lane
fallback_green, fallback_cycle = calculator.get_fallback_times()
```

## Comparison: Online vs Offline Mode

| Aspect | Online Mode | Offline Mode |
|--------|-----------|--------------|
| **Data Source** | Real-time vehicle detection | Fixed maximum times |
| **Green Time** | Proportional to traffic | 90s per lane (equal) |
| **Optimization** | Adaptive, intelligent | None, safe default |
| **Cycle Time** | 80-200s (variable) | 380s (fixed) |
| **Yellow Time** | 5s per lane | 5s per lane |
| **Safety** | High (optimized) | High (conservative) |
| **Complexity** | Complex algorithm | Simple distribution |
| **Dependencies** | Internet, detection | None (local only) |

## Troubleshooting

### System keeps switching between online/offline

- Check Raspberry Pi internet connection
- Verify backend server is accessible
- Ensure vehicle detection system is responding
- Check firewall/network rules

### Fallback mode takes too long

- Increase `check_interval` in ConnectivityManager
- Or decrease it for more frequent checks

### Fallback timing not optimal for peak hours

- Modify `max_time` parameter when initializing TrafficCalculator
- Consider junction-specific fallback configurations

## Future Enhancements

- [ ] Gradual fallback (reduce optimization rather than full fallback)
- [ ] Multiple fallback profiles (peak hour, off-peak, emergency)
- [ ] Local caching of recent traffic patterns
- [ ] Hybrid mode: partial vehicle detection with limited optimization
- [ ] Machine learning fallback patterns based on history

## Security Considerations

- Fallback mode doesn't authenticate with backend (safe for offline)
- Vehicle detection data not processed in fallback
- No personal/sensitive data in fallback timing
- Local-only operation in offline mode

## Support & Monitoring

Monitor fallback activations in logs:

```bash
# View fallback events
grep "FALLBACK\|offline" /var/log/flextraff/traffic-control.log

# Real-time monitoring
tail -f /var/log/flextraff/traffic-control.log | grep -i "offline\|fallback\|connectivity"
```
