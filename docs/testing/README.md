# FlexTraff Backend Testing Documentation

## Overview

This document provides comprehensive guidance for testing the FlexTraff Backend API. Our testing infrastructure ensures reliability, performance, and maintainability of the traffic management system.

## Test Architecture

### Test Organization

```
tests/
├── conftest.py                 # Test configuration and fixtures
├── test_api_endpoints.py       # API endpoint tests (31 tests)
├── test_traffic_algorithm.py   # Algorithm tests (13 tests)
└── performance/                # Performance testing (future)
```

### Test Categories

1. **Unit Tests**: Individual component testing with mocking
2. **Integration Tests**: Component interaction testing
3. **Algorithm Tests**: Traffic calculation logic validation
4. **API Endpoint Tests**: Complete endpoint coverage

## Quick Start

### Prerequisites

1. **Python Environment**: Python 3.13.5 with virtual environment
2. **Dependencies**: Install test dependencies
3. **Database**: Test database configuration

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify pytest installation
pytest --version
```

### Running Tests

#### Quick Test Suite (Recommended)

```bash
# Run the complete quick test suite
python run_tests.py quick
```

**Output**: Comprehensive summary with all test results, timing, and success rates.

#### Individual Test Categories

```bash
# Algorithm Tests Only (13 tests)
pytest tests/test_traffic_algorithm.py -v

# API Endpoint Tests Only (31 tests)
pytest tests/test_api_endpoints.py -v

# Unit Tests Only (excludes integration)
pytest tests/test_api_endpoints.py -m "not integration" -v
```

#### Advanced Test Execution

```bash
# Run with coverage report
pytest --cov=src --cov-report=html tests/

# Run specific test class
pytest tests/test_api_endpoints.py::TestTrafficCalculationEndpoint -v

# Run specific test method
pytest tests/test_algorithm.py::TestTrafficCalculator::test_basic_calculation -v

# Run tests with detailed output
pytest tests/ -v --tb=long

# Run tests in parallel (if pytest-xdist installed)
pytest tests/ -n auto
```

## Test Configuration

### conftest.py Overview

Our test configuration provides:

- **Mock Services**: Database and traffic calculator mocking
- **Test Client**: FastAPI test client with dependency overrides
- **Fixtures**: Reusable test data and configurations

```python
# Key fixtures available in all tests:
@pytest.fixture
def test_client():
    """FastAPI test client with mocked dependencies"""

@pytest.fixture
def mock_db_service():
    """Mocked database service"""

@pytest.fixture
def mock_traffic_calculator():
    """Mocked traffic calculation service"""
```

### Dependency Injection for Testing

Tests use FastAPI's dependency override system:

```python
# Example from conftest.py
app.dependency_overrides[get_db_service] = lambda: mock_db_service
app.dependency_overrides[get_traffic_calculator] = lambda: mock_traffic_calculator
```

## Algorithm Testing (test_traffic_algorithm.py)

### Test Coverage: 13 Tests

#### Core Functionality Tests
- `test_basic_calculation`: Standard traffic scenario validation
- `test_minimum_vehicle_scenario`: Edge case with minimal traffic
- `test_high_traffic_scenario`: Heavy traffic optimization
- `test_uneven_distribution`: Asymmetric traffic patterns

#### Validation & Edge Cases
- `test_input_validation`: Invalid input handling
- `test_zero_traffic_scenario`: No traffic conditions
- `test_edge_case_100_vehicles`: Boundary condition testing
- `test_edge_case_101_vehicles`: Over-boundary handling

#### Algorithm Properties
- `test_proportionality_principle`: Mathematical correctness
- `test_custom_parameters`: Parameter flexibility
- `test_algorithm_info`: Metadata validation
- `test_maximum_constraint_enforcement`: Timing limits

#### Scenario Testing
- `test_sample_scenarios`: Real-world scenario validation

### Key Testing Patterns

#### Async Testing
All algorithm tests use async patterns:

```python
@pytest.mark.asyncio
async def test_basic_calculation(self, mock_traffic_calculator):
    # Arrange
    lanes = [LaneData(direction="north", vehicle_count=10)]
    
    # Act
    result = await mock_traffic_calculator.calculate_green_times(lanes)
    
    # Assert
    assert result is not None
```

#### Comprehensive Validation
Each test validates:
- **Return Type**: Correct data structure
- **Mathematical Properties**: Timing constraints and proportionality
- **Edge Cases**: Boundary conditions
- **Error Handling**: Invalid inputs

## API Endpoint Testing (test_api_endpoints.py)

### Test Coverage: 31 Tests Across 9 Endpoints

#### 1. Root Endpoint (/)
- `test_root_endpoint_success`: Welcome message validation

#### 2. Health Check (/health)
- `test_health_check_healthy`: System health validation
- `test_health_check_unhealthy`: Failure scenario handling

#### 3. Traffic Calculation (/calculate-timing)
- `test_calculate_timing_success`: Valid calculation request
- `test_calculate_timing_without_junction_id`: Optional parameter handling
- `test_calculate_timing_invalid_lanes`: Input validation (5 test cases)
- `test_calculate_timing_calculation_error`: Error handling

#### 4. Vehicle Detection (/log-vehicle-detection)
- `test_log_vehicle_detection_success`: Valid detection logging
- `test_log_vehicle_detection_invalid`: Input validation (3 test cases)
- `test_log_vehicle_detection_database_error`: Database error handling

#### 5. Junctions Listing (/junctions)
- `test_get_junctions_success`: Junction retrieval
- `test_get_junctions_empty`: No junctions scenario
- `test_get_junctions_database_error`: Database error handling

#### 6. Junction Status (/junction/{junction_id}/status)
- `test_get_junction_status_success`: Valid status retrieval
- `test_get_junction_status_not_found`: Non-existent junction
- `test_get_junction_status_all_valid_ids`: Multiple ID validation (3 test cases)

#### 7. Live Timing (/live-timing)
- `test_get_live_timing_success`: Current timing retrieval
- `test_get_live_timing_with_time_window`: Time-based filtering

#### 8. Junction History (/junction/{junction_id}/history)
- `test_get_junction_history_success`: Historical data retrieval
- `test_get_junction_history_with_limit`: Limited result handling

#### 9. Daily Summary (/daily-summary)
- `test_get_daily_summary_success`: Daily statistics
- `test_get_daily_summary_custom_date`: Custom date filtering
- `test_get_daily_summary_no_junctions`: Empty result handling

### Testing Patterns

#### Request/Response Validation
```python
def test_calculate_timing_success(self, test_client, mock_traffic_calculator):
    # Test data
    request_data = {
        "lanes": [
            {"direction": "north", "vehicle_count": 10},
            {"direction": "south", "vehicle_count": 8}
        ],
        "junction_id": "junction_001"
    }
    
    # API call
    response = test_client.post("/calculate-timing", json=request_data)
    
    # Validation
    assert response.status_code == 200
    assert "green_times" in response.json()
```

#### Error Handling Validation
```python
@pytest.mark.parametrize("invalid_data", [
    {"lanes": []},  # Empty lanes
    {"lanes": [{"direction": "invalid"}]},  # Invalid direction
    {"vehicle_count": -1}  # Negative count
])
def test_validation_errors(self, test_client, invalid_data):
    response = test_client.post("/calculate-timing", json=invalid_data)
    assert response.status_code == 422
```

## Test Data Patterns

### Lane Data Examples
```python
# Standard lane configuration
standard_lanes = [
    {"direction": "north", "vehicle_count": 10},
    {"direction": "south", "vehicle_count": 8},
    {"direction": "east", "vehicle_count": 12},
    {"direction": "west", "vehicle_count": 6}
]

# High traffic scenario
high_traffic_lanes = [
    {"direction": "north", "vehicle_count": 25},
    {"direction": "south", "vehicle_count": 30},
    {"direction": "east", "vehicle_count": 20},
    {"direction": "west", "vehicle_count": 15}
]

# Minimal traffic scenario
minimal_traffic_lanes = [
    {"direction": "north", "vehicle_count": 1},
    {"direction": "south", "vehicle_count": 1}
]
```

### Vehicle Detection Data
```python
# Valid detection data
valid_detection = {
    "junction_id": "junction_001",
    "lane_id": "north_lane_1",
    "vehicle_type": "car",
    "timestamp": "2024-01-15T10:30:00Z",
    "speed": 45.5,
    "confidence": 0.95
}

# Invalid detection examples
invalid_detections = [
    {"junction_id": "", "lane_id": "north_lane_1"},  # Empty junction
    {"junction_id": "junction_001", "lane_id": ""},  # Empty lane
    {"junction_id": "junction_001", "confidence": 1.5}  # Invalid confidence
]
```

## Performance Considerations

### Test Execution Performance

- **Algorithm Tests**: ~0.02-0.05 seconds (13 tests)
- **API Endpoint Tests**: ~0.17-0.20 seconds (31 tests)
- **Total Quick Suite**: ~2.00 seconds (44 tests)

### Memory Usage
- **Mock Objects**: Lightweight in-memory mocking
- **Test Isolation**: Each test runs independently
- **Resource Cleanup**: Automatic fixture cleanup

### Optimization Tips
```bash
# Parallel execution (if available)
pytest tests/ -n auto

# Only failed tests from last run
pytest --lf

# Stop on first failure
pytest -x

# Run specific test types
pytest -m "not slow"  # Exclude slow tests
```

## Debugging Failed Tests

### Common Issues & Solutions

#### 1. Async Test Failures
**Problem**: `TypeError: object NoneType can't be used in 'await' expression`

**Solution**: Ensure test methods are marked with `@pytest.mark.asyncio`
```python
@pytest.mark.asyncio
async def test_async_function(self):
    result = await some_async_function()
    assert result is not None
```

#### 2. Dependency Injection Issues
**Problem**: `AttributeError: 'Mock' object has no attribute 'xyz'`

**Solution**: Properly configure mock returns
```python
mock_service.calculate_green_times.return_value = expected_result
```

#### 3. Test Data Validation
**Problem**: `ValidationError: field required`

**Solution**: Ensure complete test data
```python
# Include all required fields
complete_data = {
    "required_field": "value",
    "optional_field": "value"  # Include if tested
}
```

### Debugging Commands

```bash
# Verbose output with full traceback
pytest tests/ -v --tb=long

# Debug specific test
pytest tests/test_api_endpoints.py::TestTrafficCalculationEndpoint::test_calculate_timing_success -v -s

# Print statements in tests (use -s flag)
pytest tests/ -s

# Debug with pdb
pytest tests/ --pdb

# Coverage with missing lines
pytest --cov=src --cov-report=term-missing tests/
```

## Best Practices

### Test Writing Guidelines

1. **AAA Pattern**: Arrange, Act, Assert
```python
def test_example(self):
    # Arrange
    input_data = {"key": "value"}
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_output
```

2. **Descriptive Test Names**
```python
# Good
def test_calculate_timing_with_high_traffic_returns_optimized_results(self):

# Bad
def test_calculation(self):
```

3. **Test Independence**
- Each test should run independently
- Use fixtures for setup/teardown
- Don't rely on test execution order

4. **Mock External Dependencies**
```python
# Mock database calls
mock_db.get_junction.return_value = mock_junction_data

# Mock API calls
with patch('requests.get') as mock_get:
    mock_get.return_value.json.return_value = mock_response
```

### Test Data Management

1. **Use Factories for Complex Objects**
```python
def create_lane_data(direction="north", count=10):
    return {"direction": direction, "vehicle_count": count}
```

2. **Parametrized Tests for Multiple Scenarios**
```python
@pytest.mark.parametrize("direction,count,expected", [
    ("north", 10, True),
    ("south", 5, True),
    ("invalid", 10, False)
])
def test_lane_validation(self, direction, count, expected):
    result = validate_lane(direction, count)
    assert result == expected
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python run_tests.py quick
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Troubleshooting

### Environment Issues

1. **Virtual Environment Not Activated**
```bash
# Check current environment
which python
# Should show path with .venv

# Activate if needed
source .venv/bin/activate
```

2. **Missing Dependencies**
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Verify installation
pytest --version
```

3. **Path Issues**
```bash
# Run from project root
cd /Users/ajaypsk2722/flextraff-backend

# Verify structure
ls -la tests/
```

### Database Connection Issues

1. **Test Database Configuration**
- Tests use mocked database by default
- No real database connection required
- Mock configuration in `conftest.py`

2. **If Real Database Testing Needed**
```python
# Configure test database in conftest.py
TEST_DATABASE_URL = "sqlite:///test.db"
```

## Maintenance

### Adding New Tests

1. **For New API Endpoints**
```python
class TestNewEndpoint:
    def test_new_endpoint_success(self, test_client):
        response = test_client.get("/new-endpoint")
        assert response.status_code == 200
        
    def test_new_endpoint_validation(self, test_client):
        response = test_client.post("/new-endpoint", json={})
        assert response.status_code == 422
```

2. **For New Algorithm Features**
```python
@pytest.mark.asyncio
async def test_new_algorithm_feature(self, mock_traffic_calculator):
    # Test new algorithm functionality
    result = await mock_traffic_calculator.new_feature()
    assert result is not None
```

### Updating Test Data

1. **When API Changes**
- Update request/response schemas in tests
- Update mock data to match new formats
- Add validation for new fields

2. **When Algorithm Changes**
- Update expected calculation results
- Add tests for new parameters
- Validate backward compatibility

## Monitoring & Reporting

### Test Metrics to Track

1. **Coverage Metrics**
   - Line coverage: >90%
   - Branch coverage: >80%
   - Function coverage: >95%

2. **Performance Metrics**
   - Test execution time: <5 seconds
   - Individual test time: <100ms
   - Setup/teardown time: <50ms

3. **Reliability Metrics**
   - Test flakiness: <1%
   - Success rate: >99%
   - False positive rate: <0.1%

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html tests/

# View coverage report
open htmlcov/index.html

# Terminal coverage report
pytest --cov=src --cov-report=term tests/

# Coverage with missing lines
pytest --cov=src --cov-report=term-missing tests/
```

## Advanced Testing

### Async Testing Best Practices

```python
# Correct async test pattern
@pytest.mark.asyncio
async def test_async_calculation(self):
    calculator = TrafficCalculator()
    lanes = [LaneData(direction="north", vehicle_count=10)]
    
    # Use await for async methods
    result = await calculator.calculate_green_times(lanes)
    
    assert result.green_times is not None
    assert len(result.green_times) == len(lanes)
```

### Performance Testing

```python
import time
import pytest

def test_calculation_performance(self, mock_traffic_calculator):
    """Ensure calculations complete within acceptable time"""
    start_time = time.time()
    
    # Run calculation
    result = mock_traffic_calculator.calculate_green_times(test_lanes)
    
    execution_time = time.time() - start_time
    assert execution_time < 0.1  # Should complete in <100ms
```

### Load Testing Preparation

```python
# Example stress test
@pytest.mark.parametrize("vehicle_count", [10, 50, 100, 200, 500])
def test_high_volume_calculations(self, mock_traffic_calculator, vehicle_count):
    lanes = [LaneData(direction="north", vehicle_count=vehicle_count)]
    result = mock_traffic_calculator.calculate_green_times(lanes)
    assert result is not None
```

## Support & Resources

### Documentation Links
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Asyncio](https://pytest-asyncio.readthedocs.io/)

### Team Contacts
- **Backend Team**: For algorithm and API questions
- **QA Team**: For testing strategy and practices
- **DevOps Team**: For CI/CD and deployment testing

### Common Commands Reference

```bash
# Essential test commands
python run_tests.py quick              # Full quick test suite
pytest tests/ -v                       # All tests verbose
pytest tests/test_api_endpoints.py     # API tests only
pytest tests/test_traffic_algorithm.py # Algorithm tests only

# Debugging commands
pytest tests/ -v --tb=long            # Detailed error traces
pytest tests/ -s                      # Show print statements
pytest tests/ --pdb                   # Debug on failure

# Coverage commands
pytest --cov=src tests/               # Basic coverage
pytest --cov=src --cov-report=html    # HTML coverage report

# Performance commands
pytest tests/ --durations=10          # Show slowest tests
pytest tests/ -x                      # Stop on first failure
```

---

## Conclusion

This testing infrastructure provides comprehensive coverage for the FlexTraff Backend API with:

- ✅ **44 Total Tests** (13 algorithm + 31 endpoint tests)
- ✅ **100% Success Rate** in current implementation
- ✅ **Complete API Coverage** across all 9 endpoints
- ✅ **Robust Algorithm Testing** with edge cases and validation
- ✅ **Fast Execution** (~2 seconds for full suite)
- ✅ **Production Ready** with proper mocking and isolation

The testing framework ensures reliability, maintainability, and confidence in the FlexTraff traffic management system.