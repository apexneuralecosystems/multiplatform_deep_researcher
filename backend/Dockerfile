# ─────────────────────────────────────────────────────────────
# Multi-stage build for production-optimized FastAPI backend
# Build context: backend/ folder (cd backend && docker build .)
# ─────────────────────────────────────────────────────────────

FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files (from backend/ folder)
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge || true

# ─────────────────────────────────────────────────────────────
# Production stage
# ─────────────────────────────────────────────────────────────

FROM python:3.11-slim

WORKDIR /app

# Create non-root user (don't create logs directory yet)
RUN useradd -m -u 1000 appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy dependency files and backend code (from backend/ context)
COPY pyproject.toml requirements.txt ./
COPY . ./backend/

# Install package in editable mode (create logs after install to avoid package discovery issues)
RUN pip install --no-cache-dir -e . && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port (default 8000, configurable via PORT env var)
EXPOSE 8000

# Health check (reads PORT from environment, defaults to 8000)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx, os; port = os.getenv('PORT', '8000'); httpx.get(f'http://localhost:{port}/api/health', timeout=5)" || exit 1

# Production server command (JSON form for proper signal handling)
CMD ["sh", "-c", "gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --timeout 120 --access-logfile - --error-logfile -"]
