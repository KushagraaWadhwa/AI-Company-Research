# AI Startup Copilot Tests

This directory contains comprehensive tests for the AI Startup Copilot application.

## Test Structure

### `test_components.py`
Tests individual components of the system:
- **Playwright**: Web scraping functionality
- **Ollama LLM**: Language model integration  
- **Ollama Embeddings**: Text embedding generation
- **MongoDB**: Database connectivity
- **CompanyProfileAgent**: Complete agent workflow

### `test_worker_debug.py`
Debug tests for worker connectivity and task processing:
- API health checks
- Task submission and status tracking
- Direct Celery task testing
- Redis connectivity verification

### `test_api.py`
Comprehensive API endpoint testing:
- Health endpoint validation
- Analysis endpoint with various inputs
- Status endpoint for task tracking
- Report endpoint functionality
- Error handling validation

### `test_analysis_types.py`
Tests all three analysis types:
- **Standard analysis** - Basic company profiling
- **Comprehensive analysis** - Enhanced multi-source analysis
- **Universal analysis** - Complete intelligence from 50+ sources
- Task monitoring and completion tracking
- Analysis type validation and differences

## Running Tests

### Prerequisites
Ensure all services are running:
```bash
# Start MongoDB
brew services start mongodb/brew/mongodb-community

# Start Redis
brew services start redis

# Start Ollama
ollama serve

# Start the API server (in one terminal)
cd ai_copilot
python start_api.py

# Start the worker (in another terminal)  
cd ai_copilot
python start_worker.py
```

### Run Individual Tests

```bash
# Test components
python tests/test_components.py

# Debug worker issues
python tests/test_worker_debug.py

# Test API endpoints
python tests/test_api.py

# Test all analysis types
python tests/test_analysis_types.py
```

### Run All Tests

```bash
# From the ai_copilot directory
python tests/run_all_tests.py

# Or run them individually
for test in tests/test_*.py; do
    echo "Running $test..."
    python "$test"
    echo "---"
done
```

## Test Output

Each test provides detailed output:
- ✅ Success indicators
- ❌ Failure indicators with error details
- 📊 Summary statistics
- 🔧 Troubleshooting suggestions

## API Testing Resources

### cURL Commands
See `api_curl_commands.md` for comprehensive cURL examples:
- Health checks
- Analysis submissions
- Status monitoring
- Report retrieval
- Error testing
- Load testing scripts

### Postman Collection
Import `AI_Startup_Copilot_API.postman_collection.json` for:
- Interactive API testing
- Automated test workflows
- Environment management
- Response validation

See `postman_setup_guide.md` for detailed setup instructions.

## Troubleshooting

### Common Issues

1. **Import errors (`No module named 'app'`)**:
   - Tests now automatically add the project root to Python path
   - Run tests from the `ai_copilot` directory

2. **Playwright not installed**:
   ```bash
   pip install playwright
   playwright install chromium
   ```

3. **Ollama not running**:
   ```bash
   ollama serve
   ollama pull llama3.2
   ollama pull nomic-embed-text
   ```

4. **MongoDB connection failed**:
   ```bash
   brew services start mongodb/brew/mongodb-community
   ```

5. **Redis connection failed**:
   ```bash
   brew services start redis
   redis-cli ping  # Should return PONG
   ```

6. **Worker not processing tasks**:
   - Check if worker terminal shows "celery@hostname ready"
   - Restart worker: Ctrl+C then `python start_worker.py`
   - Verify .env file exists with correct Redis settings

### Environment Variables

Ensure your `.env` file contains:
```env
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379/0
OLLAMA_BASE_URL=http://localhost:11434
```

## Adding New Tests

When adding new tests:

1. **Component Tests**: Add to `test_components.py`
2. **API Tests**: Add to `test_api.py` 
3. **Worker Tests**: Add to `test_worker_debug.py`
4. **New Test Files**: Follow naming convention `test_*.py`

### Test Function Template

```python
async def test_new_feature():
    """Test description."""
    print("🔧 Testing new feature...")
    try:
        # Test implementation
        result = await some_function()
        print("✅ New feature working")
        return True
    except Exception as e:
        print(f"❌ New feature failed: {e}")
        return False
```

## Integration with CI/CD

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Run Tests
  run: |
    python tests/test_components.py
    python tests/test_api.py
    python tests/test_worker_debug.py
```

## Performance Testing

For load testing the API:
```bash
# Install httpie for easier HTTP testing
brew install httpie

# Test analyze endpoint
for i in {1..10}; do
  http POST localhost:8000/api/v1/analyze company_name="Test$i" company_url="https://example$i.com" &
done
```
