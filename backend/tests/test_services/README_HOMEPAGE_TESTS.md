# Homepage Service Test Suite

This directory contains comprehensive tests for the `homepage_service.py` module.

## Test Files

### 1. `test_homepage_service.py`
**Main unit tests for homepage service functionality**

**Coverage:**
- All major functions in homepage_service.py
- SPARQL query mocking and validation
- Data processing and transformation
- Chart data preparation
- Error handling scenarios

**Key Test Areas:**
- ✅ `get_number_of_violations_in_validation_report`
- ✅ `get_number_of_node_shapes`
- ✅ `get_number_of_node_shapes_with_violations` (the fixed function)
- ✅ `get_violations_per_node_shape`
- ✅ `get_violations_per_path`
- ✅ `get_violations_per_focus_node`
- ✅ Distribution chart data generation
- ✅ Most violated entity analysis
- ✅ Constraint component analysis
- ✅ Benchmark function execution

### 2. `test_homepage_service_edge_cases.py`
**Edge case and boundary condition testing**

**Coverage:**
- Empty result handling
- Invalid data responses
- Network error scenarios
- Unicode character handling
- Large number processing
- Concurrent execution
- Memory efficiency with large datasets

### 3. `test_homepage_service_integration.py`
**SPARQL query integration testing**

**Coverage:**
- SPARQL query structure validation
- Query parameter safety
- Performance considerations
- Complex query patterns

## Running Tests

### Run All Homepage Service Tests
```bash
python -m pytest tests/test_services/test_homepage_service*.py -v
```

### Run Specific Test Files
```bash
# Main unit tests only
python -m pytest tests/test_services/test_homepage_service.py -v

# Edge case tests only
python -m pytest tests/test_services/test_homepage_service_edge_cases.py -v

# Integration tests only
python -m pytest tests/test_services/test_homepage_service_integration.py -v
```

### Run with Coverage
```bash
python -m pytest tests/test_services/test_homepage_service*.py --cov=functions.homepage_service --cov-report=html
```

## Test Categories

### Unit Tests (42 tests)
- Mock SPARQL responses
- Validate function behavior
- Test data processing logic
- Error handling verification

### Integration Tests (15+ tests)
- SPARQL query structure validation
- Query parameter injection safety
- Performance optimization verification

### Edge Case Tests (21 tests)
- Boundary conditions
- Error scenarios
- Network issues
- Data format problems

## Key Features Tested

### ✅ Fixed Function: `get_number_of_node_shapes_with_violations`
The main fix addresses a critical issue in counting node shapes with violations:

**Original Issue:**
- Incorrect UNION syntax in SPARQL query
- Potential double-counting of node shapes
- Poor query structure

**Fixed Implementation:**
- Proper SPARQL UNION structure
- DISTINCT counting to avoid duplicates
- Clear separation of direct vs indirect violations
- Efficient graph-specific querying

**Test Coverage:**
- Query structure validation
- Custom URI handling
- Response processing
- Error handling

### Mock Strategy
- Uses `unittest.mock.Mock` for SPARQLWrapper
- Simulates realistic SPARQL response format
- Tests both success and error scenarios
- Validates query construction without requiring actual database

### Error Handling
- Network timeouts
- Authentication failures
- Malformed responses
- Empty results
- Invalid data types

## Recent Updates

### Fixed Issues
1. **SPARQL Query Structure**: Fixed UNION syntax in `get_number_of_node_shapes_with_violations`
2. **Syntax Error**: Fixed stray `def ` statement in `virtuoso_service.py`
3. **Test Mocking**: Proper mock setup for functions using different HTTP clients
4. **Error Handling**: Corrected exception type expectations in tests

### Test Improvements
- Added comprehensive edge case coverage
- Enhanced error scenario testing
- Improved mock response validation
- Added performance consideration tests

## Notes
- Tests are designed to run without requiring actual SPARQL endpoints
- All external dependencies are mocked
- Tests validate both positive and negative scenarios
- Coverage includes boundary conditions and error cases