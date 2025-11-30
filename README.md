- **Deployment**: Docker containerization

## Features
- **Smart Route Planning**: Optimal paths considering battery range
- **Charging Station Integration**: Real-time availability and compatibility
- **Car Model Database**: Specifications for different EV models
- **AI Chatbot**: Natural language assistance for navigation
- **Semantic Search**: RAG-powered information retrieval
- **Agent-based Processing**: Modular, autonomous components

## Project Structure
```
├── backend/
│   ├── orchestrator.py      # Main FastAPI application
│   ├── src/
│   │   ├── agents/          # Geographic & route optimization agents
│   │   ├── services/        # AI, Database, Qdrant, Redis services
│   │   ├── models/          # Data models (vehicles, navigation, RAG)
│   │   ├── database/        # PostgreSQL connection
│   │   └── rag/             # RAG system (embeddings, vector store, semantic chunker)
│   ├── routes/              # API route handlers
│   └── config/              # Configuration files
├── frontend/
│   └── react_app/           # React + Vite web application
│       ├── src/
│       │   ├── App.jsx      # Main React component
│       │   ├── api.js       # Backend API client
│       │   └── styles.css   # Styling
│       └── package.json     # Dependencies
├── data/
│   ├── car_models/          # EV specifications (CSV + Python)
│   └── charging_stations/   # Station data
├── docker-compose.yml       # Multi-container setup
└── .env                     # Environment variables
```

## Getting Started

### Prerequisites
- Python 3.9+ (venv recommended)
- Node.js 18+ (for React frontend)
- Docker & Docker Compose
- OpenAI or OpenRouter API Key

### Quick Start

#### 1. Start Backend Services (Docker)
```bash
docker-compose up -d
```
This starts: PostgreSQL, Redis, Qdrant, and FastAPI backend on port 8000.

#### 2. Configure Environment
Create `.env` file in project root:
```env
OPENAI_API_KEY=your_openai_or_openrouter_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1  # Optional: for OpenRouter
OPENAI_MODEL=gpt-4o-mini  # or nvidia/nemotron-nano-9b-v2:free

DATABASE_URL=postgresql://evuser:evpass@localhost:5432/evnavigation
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
```

#### 3. Run Backend (if not using Docker for API)
```bash
# Activate virtual environment
.\venv_new\Scripts\Activate.ps1  # Windows
source venv_new/bin/activate      # Linux/Mac

# Start orchestrator
python backend/orchestrator.py
```
Backend runs on: **http://localhost:8000**  
API Docs: **http://localhost:8000/docs**

#### 4. Run React Frontend
```bash
cd frontend/react_app
npm install
npm run dev
```
Frontend runs on: **http://localhost:5173**

### API Endpoints
- `GET /` - System status
- `GET /api/test-db` - Database health check
- `GET /api/vehicles-db` - List all 384 vehicle models
- `POST /api/ai-chat` - AI chatbot (send `{message: "your question"}`)
- `POST /api/smart-vehicle-search` - AI-powered vehicle recommendations
- `POST /api/plan-route` - Route planning with charging stations
```

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: 384+ EV models with specifications
- **Redis**: Caching and session management
- **Qdrant**: Vector database for semantic search
- **OpenAI/OpenRouter**: GPT-4o-mini for chat and embeddings
- **Docker**: Multi-container deployment

### Frontend
- **React 18**: UI framework
- **Vite**: Fast build tool and dev server
- **Axios**: HTTP client for API calls

### AI & RAG
- **Semantic Chunking**: Intelligent document segmentation
- **Vector Embeddings**: OpenAI text-embedding models
- **Retrieval System**: Qdrant similarity search
- **Generation**: GPT-4o-mini or Nemotron for responses

## System Flow
1. **User Input**: Query via React web interface
2. **API Request**: Frontend calls backend REST endpoints
3. **Agent Processing**: Route optimizer analyzes request
4. **Database Query**: PostgreSQL fetches vehicle specs
5. **RAG Retrieval**: Qdrant searches charging station knowledge
6. **AI Generation**: OpenAI generates intelligent responses
7. **Response**: Structured data returned to frontend
8. **Chatbot**: Natural language Q&A for EV guidance

## Development Status
- [x] Backend orchestrator with FastAPI
- [x] PostgreSQL database (384 vehicle models)
- [x] Docker multi-container setup
- [x] RAG system architecture
- [x] OpenAI/OpenRouter integration
- [x] React frontend scaffold
- [x] API endpoints (vehicles, chat, route planning)
- [ ] Enhanced route optimization algorithms
- [ ] Real-time charging station availability
- [ ] Advanced vehicle comparison features
- [ ] Mobile-responsive UI improvements

## Contributing
Please read our contributing guidelines before submitting pull requests.

## License
This project is licensed under the MIT License.