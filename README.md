# Multiplatform Deep Researcher

An MCP-powered multi-agent, multi-platform deep researcher. It performs deep web searches using [Bright Data's Web MCP server](https://brightdata.com/ai/mcp-server), with agents orchestrated through [CrewAI](https://docs.crewai.com/).

## Features

- **Multi-Platform Research**: Scrapes and analyzes content from Instagram, LinkedIn, YouTube, X (Twitter), and the open web
- **Parallel Processing**: Uses asynchronous agents to research multiple platforms simultaneously
- **Real-time Updates**: WebSocket-based live progress updates during research
- **Modern React UI**: Cyberpunk-themed dashboard with animated components
- **Rate Limiting**: Built-in protection against API abuse
- **Health Monitoring**: Kubernetes-ready health check endpoints

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI, CrewAI, Python 3.11+ |
| Frontend | React 19, TypeScript, Vite |
| LLM Provider | OpenRouter (GPT-4o, Gemini, o3-mini) |
| Web Scraping | Bright Data MCP |

## Prerequisites

- Python 3.11+
- Node.js 18+ & npm
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Quick Start

### 1. Clone & Install

```bash
git clone <repository-url>
cd multiplatform_deep_researcher

# Install Python dependencies
uv sync
# Or: pip install -e .

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### 2. Configure Environment

Copy the example and add your API keys:

```bash
cp .env.example .env
```

Edit `.env`:
```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
BRIGHT_DATA_API_TOKEN=your-brightdata-token
MCP_MODE=sse  # "sse" (remote) or "stdio" (local)
```

### 3. Run the Application

**Terminal 1 - Backend:**
```bash
# Windows
.venv\Scripts\activate
uvicorn backend.main:app --reload --port 8000

# Linux/Mac
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 4. Access the App

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Project Structure

```
multiplatform_deep_researcher/
├── backend/                 # FastAPI backend
│   ├── api/                 # Routes & WebSocket
│   │   ├── routes/          # health.py, research.py
│   │   ├── models.py        # Request/Response schemas
│   │   └── websocket.py     # Real-time updates
│   ├── core/                # Configuration
│   │   ├── config.py        # Environment settings
│   │   ├── logging.py       # Structured logging
│   │   ├── mcp.py           # MCP server config
│   │   └── rate_limit.py    # SlowAPI rate limiting
│   ├── services/            # Business logic
│   │   ├── flow.py          # CrewAI research flow
│   │   ├── research.py      # Research orchestration
│   │   └── session.py       # Session management
│   └── main.py              # FastAPI app entry
├── frontend/                # React + Vite frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   └── App.tsx          # Main app
│   └── package.json
├── docs/                    # Documentation
│   └── SSL_SETUP.md         # SSL/TLS guide
├── logs/                    # Application logs (gitignored)
├── .env                     # Environment (gitignored)
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── pyproject.toml           # Python dependencies
└── README.md                # This file
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Basic health check |
| `/api/health/detailed` | GET | Detailed health with dependencies |
| `/api/ready` | GET | Kubernetes readiness probe |
| `/api/live` | GET | Kubernetes liveness probe |
| `/api/research` | POST | Start new research session |
| `/api/research/{id}` | GET | Get research status |
| `/ws/research/{id}` | WS | Real-time research updates |

## Production Deployment

```bash
# Build frontend
cd frontend && npm run build && cd ..

# Run with Gunicorn (production)
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

See `docs/SSL_SETUP.md` for SSL/TLS configuration.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | ✅ | OpenRouter API key |
| `BRIGHT_DATA_API_TOKEN` | ✅ | Bright Data MCP token |
| `MCP_MODE` | ❌ | `sse` (default) or `stdio` |
| `CORS_ORIGINS` | ❌ | Comma-separated allowed origins |
| `DEBUG` | ❌ | Enable debug mode (`true`/`false`) |

## Troubleshooting

- **"Failed to start research"**: Check that both API keys are valid in `.env`
- **Backend hangs on startup**: Ensure `MCP_MODE=sse` for faster startup
- **CORS errors**: Add your frontend URL to `CORS_ORIGINS` in `.env`
- **Rate limited**: Default is 10 requests/minute for research endpoint

## License

MIT
