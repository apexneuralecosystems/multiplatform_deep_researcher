# Docker Deployment Guide

Production-ready Dockerfiles for Multiplatform Deep Researcher.

## Files Created

- `Dockerfile.backend` - FastAPI backend container
- `Dockerfile.frontend` - React + Vite frontend container (Nginx)
- `.dockerignore` - Optimized build exclusions

## Quick Start

### Build Backend

```bash
docker build -f Dockerfile.backend -t multiplatform-backend:latest .
```

### Build Frontend

```bash
docker build -f Dockerfile.frontend -t multiplatform-frontend:latest .
```

### Run Backend

```bash
docker run -d \
  --name multiplatform-backend \
  -p 8000:8000 \
  -e OPENROUTER_API_KEY=sk-or-v1-your-key \
  -e BRIGHT_DATA_API_TOKEN=your-token \
  -e MCP_MODE=sse \
  -e PORT=8000 \
  -e CORS_ORIGINS=https://yourdomain.com \
  multiplatform-backend:latest
```

### Run Frontend

```bash
docker run -d \
  --name multiplatform-frontend \
  -p 80:80 \
  multiplatform-frontend:latest
```

## Environment Variables

### Backend (Required)

- `OPENROUTER_API_KEY` - OpenRouter API key
- `BRIGHT_DATA_API_TOKEN` - Bright Data MCP token

### Backend (Optional)

- `MCP_MODE` - "sse" (remote) or "stdio" (local), default: "stdio"
- `PORT` - Server port, default: 8000
- `HOST` - Bind address, default: "0.0.0.0"
- `DEBUG` - Debug mode, default: "false"
- `CORS_ORIGINS` - Comma-separated allowed origins

### Frontend (Build-time, Optional)

- `VITE_API_URL` - Backend API URL (if not using relative paths)
- `VITE_WS_URL` - WebSocket URL (if not using relative paths)

## Dorkploy Deployment

For Dorkploy-style deployments where containers are separate:

1. **Backend**: Deploy as-is, expose port 8000
2. **Frontend**: 
   - If backend is on a different host, set `VITE_API_URL` and `VITE_WS_URL` at build time
   - Or modify nginx config in Dockerfile.frontend to proxy to your backend URL

## Notes

- Backend runs as non-root user (appuser)
- Frontend serves static files via Nginx
- Health check included in backend container
- Logs directory is writable at `/app/logs` in backend container

