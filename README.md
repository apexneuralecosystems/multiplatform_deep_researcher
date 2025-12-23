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

### Linux Server Setup (First Time)

```bash
# Navigate to your project directory
cd /path/to/multiplatform_deep_researcher

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install all dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
nano .env  # Add your API keys

# Build frontend for production
cd frontend && npm install && npm run build && cd ..
```

### Running the Application

**Development (Local):**
```bash
# Backend (Terminal 1)
source venv/bin/activate
uvicorn backend.main:app --reload --port 8000

# Frontend (Terminal 2)
cd frontend && npm run dev
```

**Production (Linux Server):**
```bash
# Activate virtual environment
source venv/bin/activate

# Run with Gunicorn (recommended for production)
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or run with PM2 for process management
pm2 start "gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000" --name multiplatform-api
```

### Updating Dependencies on Server

When you pull new code changes:
```bash
cd /path/to/multiplatform_deep_researcher
source venv/bin/activate
pip install -r requirements.txt --upgrade
# Restart your application
pm2 restart multiplatform-api  # or however you manage your process
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

### Common Errors & Fixes

| Error | Cause | Solution |
|-------|-------|----------|
| `ImportError: Fallback to LiteLLM is not available` | `litellm` package not installed | Run `pip install litellm>=1.50.0` in your venv |
| `ModuleNotFoundError: No module named 'openai'` | `openai` package not installed | Run `pip install openai>=1.50.0` |
| `ModuleNotFoundError: No module named 'instructor'` | `instructor` package not installed | Run `pip install instructor>=1.0.0` |
| `ModuleNotFoundError: No module named 'X'` | Missing dependency | Run `pip install -r requirements.txt` |
| `Failed to start research` | Invalid API keys | Check `.env` has valid `OPENROUTER_API_KEY` and `BRIGHT_DATA_API_TOKEN` |
| Backend hangs on startup | MCP mode issue | Set `MCP_MODE=sse` in `.env` for faster startup |
| CORS errors in browser | Frontend URL not allowed | Add your frontend URL to `CORS_ORIGINS` in `.env` |
| Rate limited (429 error) | Too many requests | Default is 10 req/min for research endpoint |

### Reinstalling Dependencies (Nuclear Option)

If you encounter persistent import errors:
```bash
cd /path/to/multiplatform_deep_researcher
source venv/bin/activate
pip freeze | xargs pip uninstall -y  # Remove all packages
pip install -r requirements.txt      # Fresh install
```

## FAQ

### Why is `requirements.txt` at the root instead of inside `backend/`?

This project is a **monorepo** containing both the Python backend and React frontend. The `requirements.txt` is placed at the project root for several reasons:

1. **Single Source of Truth**: All Python dependencies (backend, Streamlit app, dev tools) are managed in one place
2. **Easier CI/CD**: Deploy scripts can reference one requirements file at the root
3. **Standard Practice**: Most Python monorepos place `requirements.txt` or `pyproject.toml` at the root
4. **uv Compatibility**: The `uv` package manager expects `pyproject.toml` at the project root

The `pyproject.toml` file is the primary dependency definition; `requirements.txt` is generated for traditional pip compatibility.

## License

MIT
