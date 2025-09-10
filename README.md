# AI Startup Copilot

A comprehensive AI-powered platform for analyzing startups using web scraping, LLM analysis, and vector embeddings.

## Architecture

- **FastAPI**: Modern, fast web framework for building APIs
- **Celery**: Distributed task queue for background AI processing
- **Redis**: Message broker and result backend
- **MongoDB**: Document database and vector storage
- **LangChain + Ollama**: Local LLM integration for AI analysis
- **Playwright**: Web scraping for content extraction
- **Vector Embeddings**: Semantic search capabilities

## Project Structure

```
ai_copilot/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── agents/              # AI Agents
│   │   ├── __init__.py
│   │   └── profile_agent.py # Company analysis agent
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── endpoints.py # API routes with MongoDB integration
│   │       └── schemas.py   # Pydantic models
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Configuration settings
│   │   ├── mongo_client.py  # MongoDB client management
│   │   └── embeddings.py    # Vector embeddings utility
│   └── workers/
│       ├── __init__.py
│       ├── celery_app.py    # Celery configuration
│       └── tasks.py         # AI-powered background tasks
├── requirements.txt         # Updated with AI dependencies
├── docker-compose.yml       # Updated for Phase 2 services
├── Dockerfile              # With Playwright support
├── start_api.py            # API server startup script
├── start_worker.py         # Worker startup script
├── test_api.py             # Updated test script
├── env.example             # Environment variables template
└── README.md
```

## Quick Start

### Prerequisites

1. **Install Ollama and required models:**
   ```bash
   # Install Ollama (macOS/Linux)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull required models
   ollama pull llama3.2
   ollama pull nomic-embed-text
   ```

2. **MongoDB Setup:**
   - **Option A**: Use MongoDB Atlas (recommended)
     - Create a free cluster at https://cloud.mongodb.com
     - Get your connection string
   - **Option B**: Install MongoDB locally
     ```bash
     # macOS
     brew install mongodb-community
     brew services start mongodb/brew/mongodb-community
     ```

### Using Docker Compose (Recommended)

1. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your MongoDB connection string
   ```

2. **Start all services:**
   ```bash
   docker-compose up --build
   ```

3. **Access the services:**
   - API Documentation: http://localhost:8000/api/v1/docs
   - API Base URL: http://localhost:8000/api/v1
   - Flower (Celery monitoring): http://localhost:5555

### Manual Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your settings
   ```

3. **Start services:**
   ```bash
   # Terminal 1: Redis
   redis-server
   
   # Terminal 2: Celery worker
   python start_worker.py
   
   # Terminal 3: API server
   python start_api.py
   ```

4. **Test the setup:**
   ```bash
   python test_api.py
   ```

## API Endpoints

### POST /api/v1/analyze
Start a startup analysis task.

**Request:**
```json
{
  "company_name": "Stripe",
  "company_url": "https://stripe.com"
}
```

**Response (New Analysis):**
```json
{
  "task_id": "12345678-1234-5678-9abc-123456789012",
  "message": "Analysis task created successfully"
}
```

**Response (Cached Analysis):**
```json
{
  "task_id": "60f7b3b4c9e6a5d4e8f9a1b2",
  "message": "Analysis already complete for Stripe. Use /report/60f7b3b4c9e6a5d4e8f9a1b2 to get the full report."
}
```

### GET /api/v1/status/{task_id}
Check the status of an analysis task.

**Response (In Progress):**
```json
{
  "task_id": "12345678-1234-5678-9abc-123456789012",
  "status": "PROGRESS",
  "progress": {
    "current_step": "Scraping website and analyzing content",
    "progress": 2,
    "total_steps": 6,
    "percentage": 33
  }
}
```

**Response (Completed):**
```json
{
  "task_id": "12345678-1234-5678-9abc-123456789012",
  "status": "SUCCESS",
  "result": {
    "company_name": "Stripe",
    "status": "Analysis Complete",
    "mongodb_id": "60f7b3b4c9e6a5d4e8f9a1b2",
    "summary": "Stripe is a technology company that builds economic infrastructure for the internet...",
    "processing_time_seconds": 127.5,
    "embedding_dimension": 768
  }
}
```

### GET /api/v1/report/{company_id}
Get a comprehensive company analysis report from MongoDB.

### GET /api/v1/health
Health check endpoint for the API and Celery workers.

## Environment Variables

Create a `.env` file in the project root:

```env
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# FastAPI Configuration
API_V1_STR=/api/v1
PROJECT_NAME=AI Startup Copilot
VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests (to be implemented in Phase 2)
pytest
```

### Code Quality
```bash
# Install development dependencies
pip install black isort flake8 mypy

# Format code
black .
isort .

# Lint code
flake8 .
mypy .
```

## Phase 1 Features

✅ **Completed:**
- FastAPI application with async endpoints
- Celery integration for background tasks
- Redis message broker setup
- Docker containerization
- API documentation with Swagger/OpenAPI
- Request/response validation with Pydantic
- Health check endpoints
- Error handling and logging
- Task status tracking

🚧 **Phase 1 Limitations:**
- Analysis task is a placeholder (sleeps for 10-15 seconds)
- No actual AI agent integration yet
- Company reports are dummy data
- No data persistence (Elasticsearch integration in Phase 2)

## Next Steps (Phase 2)

- Integrate LangChain/LangGraph for AI agent orchestration
- Add Elasticsearch for data storage and vector search
- Implement actual startup analysis logic
- Add RAG-powered chatbot functionality
- Enhanced monitoring and observability

## Monitoring

- **Flower**: Celery task monitoring at http://localhost:5555
- **API Docs**: Interactive API documentation at http://localhost:8000/api/v1/docs
- **Health Check**: Service health at http://localhost:8000/health

## Troubleshooting

**Redis Connection Issues:**
- Ensure Redis is running: `redis-cli ping`
- Check Redis configuration in `.env` file

**Celery Worker Issues:**
- Check worker logs for errors
- Verify Redis connectivity
- Ensure all dependencies are installed

**API Issues:**
- Check API logs for detailed error information
- Verify all environment variables are set
- Ensure port 8000 is not in use by another service
