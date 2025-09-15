# FlexTraff API Documentation

## Overview

The FlexTraff Backend API provides intelligent traffic management capabilities through real-time traffic calculation, vehicle detection logging, and comprehensive junction monitoring. This RESTful API is built with FastAPI and designed for integration with traffic management systems.

## Base Information

- **Base URL**: `http://localhost:8000` (development)
- **API Version**: 1.0
- **Content-Type**: `application/json`
- **Response Format**: JSON

## Authentication

Currently, the API does not require authentication. Future versions may implement JWT-based authentication for production deployments.

## Error Handling

The API uses standard HTTP status codes and returns detailed error information:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Common HTTP Status Codes

- `200 OK`: Successful request
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error
- `404 Not Found`: Resource not found

## API Endpoints

### 1. Root Endpoint

**GET** `/`

Welcome endpoint providing basic API information.

#### Response

```json
{
  "message": "Welcome to FlexTraff API",
  "version": "1.0",
  "status": "active"
}
```

#### Example

```bash
curl -X GET "http://localhost:8000/"
```

```json
{
  "message": "Welcome to FlexTraff API",
  "version": "1.0", 
  "status": "active"
}
```

---

### 2. Health Check

**GET** `/health`

System health status endpoint for monitoring and load balancers.

#### Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "database": "connected",
  "algorithm": "ready"
}
```

#### Health Status Values

- `healthy`: System is fully operational
- `degraded`: Some services may be impacted
- `unhealthy`: System is experiencing issues

#### Example

```bash
curl -X GET "http://localhost:8000/health"
```

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456Z",
  "database": "connected",
  "algorithm": "ready"
}
```

---

### 3. Traffic Timing Calculation

**POST** `/calculate-timing`

Calculate optimal traffic light timing based on current lane traffic data.

#### Request Body

```json
{
  "lanes": [
    {
      "direction": "north",
      "vehicle_count": 10
    },
    {
      "direction": "south", 
      "vehicle_count": 8
    },
    {
      "direction": "east",
      "vehicle_count": 12
    },
    {
      "direction": "west",
      "vehicle_count": 6
    }
  ],
  "junction_id": "junction_001"
}
```

#### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `lanes` | Array | Yes | List of lane traffic data |
| `lanes[].direction` | String | Yes | Lane direction: `north`, `south`, `east`, `west` |
| `lanes[].vehicle_count` | Integer | Yes | Number of vehicles in lane (≥0) |
| `junction_id` | String | No | Junction identifier for logging |

#### Response

```json
{
  "green_times": {
    "north": 15.5,
    "south": 12.4,
    "east": 18.6,
    "west": 9.3
  },
  "total_cycle_time": 55.8,
  "timestamp": "2024-01-15T10:30:00Z",
  "junction_id": "junction_001",
  "algorithm_version": "1.0"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `green_times` | Object | Green light duration for each direction (seconds) |
| `total_cycle_time` | Float | Complete traffic light cycle duration (seconds) |
| `timestamp` | String | Calculation timestamp (ISO 8601) |
| `junction_id` | String | Junction identifier (if provided) |
| `algorithm_version` | String | Algorithm version used |

#### Examples

**Basic Request:**
```bash
curl -X POST "http://localhost:8000/calculate-timing" \
  -H "Content-Type: application/json" \
  -d '{
    "lanes": [
      {"direction": "north", "vehicle_count": 10},
      {"direction": "south", "vehicle_count": 8}
    ]
  }'
```

**High Traffic Scenario:**
```bash
curl -X POST "http://localhost:8000/calculate-timing" \
  -H "Content-Type: application/json" \
  -d '{
    "lanes": [
      {"direction": "north", "vehicle_count": 25},
      {"direction": "south", "vehicle_count": 30},
      {"direction": "east", "vehicle_count": 20},
      {"direction": "west", "vehicle_count": 15}
    ],
    "junction_id": "main_intersection_001"
  }'
```

**Response:**
```json
{
  "green_times": {
    "north": 27.8,
    "south": 33.3,
    "east": 22.2,
    "west": 16.7
  },
  "total_cycle_time": 100.0,
  "timestamp": "2024-01-15T10:30:00.123456Z",
  "junction_id": "main_intersection_001",
  "algorithm_version": "1.0"
}
```

#### Error Cases

**Empty Lanes:**
```json
{
  "detail": [
    {
      "loc": ["body", "lanes"],
      "msg": "ensure this value has at least 1 items",
      "type": "value_error.list.min_items"
    }
  ]
}
```

**Invalid Direction:**
```json
{
  "detail": [
    {
      "loc": ["body", "lanes", 0, "direction"],
      "msg": "value is not a valid enumeration member",
      "type": "type_error.enum"
    }
  ]
}
```

---

### 4. Vehicle Detection Logging

**POST** `/log-vehicle-detection`

Log vehicle detection events from traffic sensors.

#### Request Body

```json
{
  "junction_id": "junction_001",
  "lane_id": "north_lane_1",
  "vehicle_type": "car",
  "timestamp": "2024-01-15T10:30:00Z",
  "speed": 45.5,
  "confidence": 0.95
}
```

#### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `junction_id` | String | Yes | Junction identifier |
| `lane_id` | String | Yes | Specific lane identifier |
| `vehicle_type` | String | Yes | Vehicle type: `car`, `truck`, `bus`, `motorcycle`, `bicycle` |
| `timestamp` | String | Yes | Detection timestamp (ISO 8601) |
| `speed` | Float | No | Vehicle speed in km/h |
| `confidence` | Float | No | Detection confidence (0.0-1.0) |

#### Response

```json
{
  "status": "logged",
  "detection_id": "det_12345",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Example

```bash
curl -X POST "http://localhost:8000/log-vehicle-detection" \
  -H "Content-Type: application/json" \
  -d '{
    "junction_id": "junction_001",
    "lane_id": "north_lane_1", 
    "vehicle_type": "car",
    "timestamp": "2024-01-15T10:30:00Z",
    "speed": 45.5,
    "confidence": 0.95
  }'
```

**Response:**
```json
{
  "status": "logged",
  "detection_id": "det_67890",
  "timestamp": "2024-01-15T10:30:15.123456Z"
}
```

#### Batch Logging

```bash
curl -X POST "http://localhost:8000/log-vehicle-detection" \
  -H "Content-Type: application/json" \
  -d '{
    "detections": [
      {
        "junction_id": "junction_001",
        "lane_id": "north_lane_1",
        "vehicle_type": "car",
        "timestamp": "2024-01-15T10:30:00Z"
      },
      {
        "junction_id": "junction_001", 
        "lane_id": "south_lane_1",
        "vehicle_type": "truck",
        "timestamp": "2024-01-15T10:30:05Z"
      }
    ]
  }'
```

---

### 5. Junction Listing

**GET** `/junctions`

Retrieve list of all monitored junctions.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `active_only` | Boolean | No | Filter for active junctions only |
| `limit` | Integer | No | Maximum number of results (default: 100) |
| `offset` | Integer | No | Pagination offset (default: 0) |

#### Response

```json
{
  "junctions": [
    {
      "junction_id": "junction_001",
      "name": "Main Street & First Avenue",
      "location": {
        "latitude": 40.7128,
        "longitude": -74.0060
      },
      "status": "active",
      "lanes": [
        {"id": "north_lane_1", "direction": "north"},
        {"id": "south_lane_1", "direction": "south"},
        {"id": "east_lane_1", "direction": "east"},
        {"id": "west_lane_1", "direction": "west"}
      ],
      "last_updated": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 100
}
```

#### Example

```bash
curl -X GET "http://localhost:8000/junctions?active_only=true&limit=10"
```

**Response:**
```json
{
  "junctions": [
    {
      "junction_id": "junction_001",
      "name": "Main Street & First Avenue", 
      "location": {
        "latitude": 40.7128,
        "longitude": -74.0060
      },
      "status": "active",
      "lanes": [
        {"id": "north_lane_1", "direction": "north"},
        {"id": "south_lane_1", "direction": "south"}
      ],
      "last_updated": "2024-01-15T10:30:00.123456Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 10
}
```

---

### 6. Junction Status

**GET** `/junction/{junction_id}/status`

Get current status and real-time information for a specific junction.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `junction_id` | String | Yes | Junction identifier |

#### Response

```json
{
  "junction_id": "junction_001",
  "status": "active",
  "current_phase": "north_south_green",
  "phase_remaining": 23.5,
  "traffic_density": {
    "north": 0.7,
    "south": 0.5, 
    "east": 0.8,
    "west": 0.3
  },
  "last_calculation": "2024-01-15T10:29:45Z",
  "next_calculation": "2024-01-15T10:30:45Z",
  "system_health": "optimal"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `junction_id` | String | Junction identifier |
| `status` | String | Junction status: `active`, `maintenance`, `error` |
| `current_phase` | String | Current traffic light phase |
| `phase_remaining` | Float | Seconds remaining in current phase |
| `traffic_density` | Object | Traffic density per direction (0.0-1.0) |
| `last_calculation` | String | Last timing calculation timestamp |
| `next_calculation` | String | Next scheduled calculation timestamp |
| `system_health` | String | System health: `optimal`, `warning`, `critical` |

#### Examples

```bash
curl -X GET "http://localhost:8000/junction/junction_001/status"
```

**Response:**
```json
{
  "junction_id": "junction_001",
  "status": "active",
  "current_phase": "north_south_green", 
  "phase_remaining": 23.5,
  "traffic_density": {
    "north": 0.7,
    "south": 0.5,
    "east": 0.8, 
    "west": 0.3
  },
  "last_calculation": "2024-01-15T10:29:45.123456Z",
  "next_calculation": "2024-01-15T10:30:45.123456Z",
  "system_health": "optimal"
}
```

**Junction Not Found:**
```bash
curl -X GET "http://localhost:8000/junction/nonexistent/status"
```

**Response:**
```json
{
  "detail": "Junction not found"
}
```

---

### 7. Live Timing Information

**GET** `/live-timing`

Get real-time traffic light timing for all junctions or specific time window.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `junction_ids` | String | No | Comma-separated junction IDs |
| `time_window` | Integer | No | Time window in minutes (default: 5) |
| `include_predictions` | Boolean | No | Include predicted timing (default: false) |

#### Response

```json
{
  "live_timing": [
    {
      "junction_id": "junction_001",
      "current_timing": {
        "north": {"status": "green", "remaining": 23.5},
        "south": {"status": "green", "remaining": 23.5},
        "east": {"status": "red", "remaining": 45.2},
        "west": {"status": "red", "remaining": 45.2}
      },
      "next_cycle": {
        "north": {"next_green": 68.7, "duration": 15.5},
        "south": {"next_green": 68.7, "duration": 12.4},
        "east": {"next_green": 0.0, "duration": 18.6},
        "west": {"next_green": 0.0, "duration": 9.3}
      },
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z",
  "time_window": 5
}
```

#### Example

```bash
curl -X GET "http://localhost:8000/live-timing?junction_ids=junction_001,junction_002&time_window=10"
```

**Response:**
```json
{
  "live_timing": [
    {
      "junction_id": "junction_001",
      "current_timing": {
        "north": {"status": "green", "remaining": 23.5},
        "south": {"status": "green", "remaining": 23.5},
        "east": {"status": "red", "remaining": 45.2},
        "west": {"status": "red", "remaining": 45.2}
      },
      "timestamp": "2024-01-15T10:30:00.123456Z"
    }
  ],
  "timestamp": "2024-01-15T10:30:00.123456Z",
  "time_window": 10
}
```

---

### 8. Junction History

**GET** `/junction/{junction_id}/history`

Retrieve historical traffic and timing data for a specific junction.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `junction_id` | String | Yes | Junction identifier |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | String | No | Start date (ISO 8601) |
| `end_date` | String | No | End date (ISO 8601) |
| `limit` | Integer | No | Maximum records (default: 100) |
| `metrics` | String | No | Comma-separated metrics: `traffic`, `timing`, `incidents` |

#### Response

```json
{
  "junction_id": "junction_001",
  "history": [
    {
      "timestamp": "2024-01-15T10:00:00Z",
      "traffic_data": {
        "north": {"vehicle_count": 10, "avg_speed": 45.2},
        "south": {"vehicle_count": 8, "avg_speed": 42.1},
        "east": {"vehicle_count": 12, "avg_speed": 38.5},
        "west": {"vehicle_count": 6, "avg_speed": 41.8}
      },
      "calculated_timing": {
        "north": 15.5,
        "south": 12.4,
        "east": 18.6,
        "west": 9.3
      },
      "actual_timing": {
        "north": 16.0,
        "south": 12.0,
        "east": 19.0,
        "west": 9.0
      },
      "efficiency_score": 0.92
    }
  ],
  "period": {
    "start": "2024-01-15T00:00:00Z",
    "end": "2024-01-15T23:59:59Z"
  },
  "total_records": 144,
  "page": 1,
  "per_page": 100
}
```

#### Example

```bash
curl -X GET "http://localhost:8000/junction/junction_001/history?start_date=2024-01-15T00:00:00Z&limit=50"
```

**Response:**
```json
{
  "junction_id": "junction_001",
  "history": [
    {
      "timestamp": "2024-01-15T10:00:00.000000Z",
      "traffic_data": {
        "north": {"vehicle_count": 10, "avg_speed": 45.2},
        "south": {"vehicle_count": 8, "avg_speed": 42.1}
      },
      "calculated_timing": {
        "north": 15.5,
        "south": 12.4
      },
      "efficiency_score": 0.92
    }
  ],
  "period": {
    "start": "2024-01-15T00:00:00Z",
    "end": "2024-01-15T23:59:59Z"
  },
  "total_records": 50,
  "page": 1,
  "per_page": 50
}
```

---

### 9. Daily Summary

**GET** `/daily-summary`

Get aggregated daily statistics and performance metrics.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date` | String | No | Specific date (YYYY-MM-DD, default: today) |
| `junction_ids` | String | No | Comma-separated junction IDs |
| `include_trends` | Boolean | No | Include 7-day trends (default: false) |

#### Response

```json
{
  "date": "2024-01-15",
  "summary": {
    "total_vehicles": 15420,
    "avg_wait_time": 32.5,
    "efficiency_score": 0.87,
    "incidents": 2,
    "peak_hours": ["08:00-09:00", "17:00-18:00"]
  },
  "junctions": [
    {
      "junction_id": "junction_001",
      "vehicles_processed": 3890,
      "avg_efficiency": 0.92,
      "peak_traffic_time": "08:15",
      "total_calculations": 144,
      "avg_cycle_time": 85.3
    }
  ],
  "hourly_breakdown": {
    "00": {"vehicles": 89, "efficiency": 0.95},
    "01": {"vehicles": 45, "efficiency": 0.98},
    "08": {"vehicles": 1250, "efficiency": 0.82},
    "17": {"vehicles": 1180, "efficiency": 0.79}
  },
  "trends": {
    "7_day_avg_vehicles": 14850,
    "7_day_avg_efficiency": 0.85,
    "trend_direction": "improving"
  }
}
```

#### Example

```bash
curl -X GET "http://localhost:8000/daily-summary?date=2024-01-15&include_trends=true"
```

**Response:**
```json
{
  "date": "2024-01-15",
  "summary": {
    "total_vehicles": 15420,
    "avg_wait_time": 32.5,
    "efficiency_score": 0.87,
    "incidents": 2,
    "peak_hours": ["08:00-09:00", "17:00-18:00"]
  },
  "junctions": [
    {
      "junction_id": "junction_001",
      "vehicles_processed": 3890,
      "avg_efficiency": 0.92,
      "peak_traffic_time": "08:15",
      "total_calculations": 144,
      "avg_cycle_time": 85.3
    }
  ],
  "trends": {
    "7_day_avg_vehicles": 14850,
    "7_day_avg_efficiency": 0.85,
    "trend_direction": "improving"
  }
}
```

**No Data Available:**
```json
{
  "date": "2024-01-15",
  "summary": {
    "total_vehicles": 0,
    "message": "No traffic data available for this date"
  },
  "junctions": []
}
```

---

## Data Models

### Lane Data Model

```json
{
  "direction": "north|south|east|west",
  "vehicle_count": "integer >= 0"
}
```

### Vehicle Detection Model

```json
{
  "junction_id": "string",
  "lane_id": "string", 
  "vehicle_type": "car|truck|bus|motorcycle|bicycle",
  "timestamp": "ISO 8601 datetime",
  "speed": "float (optional)",
  "confidence": "float 0.0-1.0 (optional)"
}
```

### Junction Model

```json
{
  "junction_id": "string",
  "name": "string",
  "location": {
    "latitude": "float",
    "longitude": "float"
  },
  "status": "active|maintenance|error",
  "lanes": [
    {
      "id": "string",
      "direction": "north|south|east|west"
    }
  ],
  "last_updated": "ISO 8601 datetime"
}
```

## Rate Limiting

Current implementation does not enforce rate limiting. Production deployments should implement:

- **Calculation Endpoint**: 100 requests/minute per IP
- **Detection Logging**: 1000 requests/minute per IP
- **Status Endpoints**: 300 requests/minute per IP

## Monitoring & Analytics

### Key Performance Indicators

1. **Response Times**
   - Calculation endpoint: <100ms (95th percentile)
   - Status endpoints: <50ms (95th percentile)
   - History endpoints: <200ms (95th percentile)

2. **Availability**
   - Target uptime: 99.9%
   - Health check frequency: 30 seconds
   - Automatic failover: <5 seconds

3. **Accuracy**
   - Traffic calculation accuracy: >95%
   - Detection logging success: >99.5%
   - Data consistency: 100%

### Logging

All API requests are logged with:
- Request timestamp
- Endpoint accessed
- Response status
- Processing time
- Client IP (anonymized)

## Integration Examples

### Python Client

```python
import requests
import json

class FlexTraffAPI:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def calculate_timing(self, lanes, junction_id=None):
        """Calculate traffic light timing"""
        payload = {"lanes": lanes}
        if junction_id:
            payload["junction_id"] = junction_id
            
        response = requests.post(
            f"{self.base_url}/calculate-timing",
            json=payload
        )
        return response.json()
    
    def log_detection(self, detection_data):
        """Log vehicle detection"""
        response = requests.post(
            f"{self.base_url}/log-vehicle-detection",
            json=detection_data
        )
        return response.json()
    
    def get_junction_status(self, junction_id):
        """Get junction status"""
        response = requests.get(
            f"{self.base_url}/junction/{junction_id}/status"
        )
        return response.json()

# Usage example
api = FlexTraffAPI()

# Calculate timing
lanes = [
    {"direction": "north", "vehicle_count": 10},
    {"direction": "south", "vehicle_count": 8}
]
result = api.calculate_timing(lanes, "junction_001")
print(f"Green times: {result['green_times']}")

# Log detection
detection = {
    "junction_id": "junction_001",
    "lane_id": "north_lane_1",
    "vehicle_type": "car",
    "timestamp": "2024-01-15T10:30:00Z"
}
api.log_detection(detection)
```

### JavaScript Client

```javascript
class FlexTraffAPI {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async calculateTiming(lanes, junctionId = null) {
        const payload = { lanes };
        if (junctionId) {
            payload.junction_id = junctionId;
        }
        
        const response = await fetch(`${this.baseUrl}/calculate-timing`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });
        
        return response.json();
    }
    
    async getJunctionStatus(junctionId) {
        const response = await fetch(
            `${this.baseUrl}/junction/${junctionId}/status`
        );
        return response.json();
    }
    
    async getLiveTiming(junctionIds = [], timeWindow = 5) {
        const params = new URLSearchParams();
        if (junctionIds.length > 0) {
            params.append('junction_ids', junctionIds.join(','));
        }
        params.append('time_window', timeWindow);
        
        const response = await fetch(
            `${this.baseUrl}/live-timing?${params}`
        );
        return response.json();
    }
}

// Usage example
const api = new FlexTraffAPI();

// Calculate timing
const lanes = [
    { direction: 'north', vehicle_count: 10 },
    { direction: 'south', vehicle_count: 8 }
];

api.calculateTiming(lanes, 'junction_001')
    .then(result => {
        console.log('Green times:', result.green_times);
        console.log('Total cycle:', result.total_cycle_time);
    });

// Get live timing
api.getLiveTiming(['junction_001'], 10)
    .then(data => {
        console.log('Live timing:', data.live_timing);
    });
```

### cURL Examples

```bash
#!/bin/bash

# Set base URL
BASE_URL="http://localhost:8000"

# Health check
curl -X GET "$BASE_URL/health"

# Calculate timing for intersection
curl -X POST "$BASE_URL/calculate-timing" \
  -H "Content-Type: application/json" \
  -d '{
    "lanes": [
      {"direction": "north", "vehicle_count": 15},
      {"direction": "south", "vehicle_count": 12},
      {"direction": "east", "vehicle_count": 8},
      {"direction": "west", "vehicle_count": 5}
    ],
    "junction_id": "main_intersection"
  }'

# Log vehicle detection
curl -X POST "$BASE_URL/log-vehicle-detection" \
  -H "Content-Type: application/json" \
  -d '{
    "junction_id": "junction_001",
    "lane_id": "north_lane_1",
    "vehicle_type": "car",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "speed": 45.5,
    "confidence": 0.95
  }'

# Get junction status
curl -X GET "$BASE_URL/junction/junction_001/status"

# Get daily summary
curl -X GET "$BASE_URL/daily-summary?date=$(date +%Y-%m-%d)&include_trends=true"
```

## Development & Testing

### Local Development Setup

```bash
# Start development server
uvicorn main:app --reload --port 8000

# API will be available at:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

### Testing Endpoints

```bash
# Run API tests
pytest tests/test_api_endpoints.py -v

# Test specific endpoint
pytest tests/test_api_endpoints.py::TestTrafficCalculationEndpoint -v

# Generate API documentation
python scripts/generate_api_docs.py
```

### Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Production Considerations

### Security

1. **Authentication**: Implement JWT tokens for production
2. **Rate Limiting**: Prevent API abuse
3. **Input Validation**: Strict validation on all inputs
4. **HTTPS**: Use TLS encryption in production
5. **CORS**: Configure appropriate CORS policies

### Scalability

1. **Load Balancing**: Multiple API instances
2. **Database Optimization**: Connection pooling and indexing
3. **Caching**: Redis for frequently accessed data
4. **Monitoring**: Comprehensive logging and metrics

### Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  flextraff-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/flextraff
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
      
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: flextraff
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      
  redis:
    image: redis:7-alpine
```

## Support & Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Traffic Management Standards](https://example.com/standards)
- [API Testing Guide](docs/testing/README.md)

### Contact Information
- **API Support**: api-support@flextraff.com
- **Technical Issues**: tech-support@flextraff.com
- **Documentation**: docs@flextraff.com

---

## Changelog

### Version 1.0 (Current)
- Initial API release
- 9 core endpoints
- Real-time traffic calculation
- Vehicle detection logging
- Junction monitoring
- Historical data access
- Daily analytics

### Planned Features (Version 1.1)
- WebSocket real-time updates
- Advanced analytics endpoints
- Bulk operation support
- Enhanced authentication
- Performance optimizations

---

*Last Updated: 2024-01-15*  
*API Version: 1.0*  
*Documentation Version: 1.0*