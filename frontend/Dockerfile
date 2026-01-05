# ─────────────────────────────────────────────────────────────
# Multi-stage build for production-optimized React + Vite frontend
# Build context: frontend/ folder (cd frontend && docker build .)
# ─────────────────────────────────────────────────────────────

FROM node:20-alpine AS builder

WORKDIR /build

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies (both prod and dev needed for build)
RUN npm ci --ignore-scripts

# Copy frontend source code
COPY . .

# Build application (VITE_* env vars can be passed at build time)
ARG VITE_API_URL
ARG VITE_WS_URL
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL

RUN npm run build

# ─────────────────────────────────────────────────────────────
# Production stage with Nginx
# ─────────────────────────────────────────────────────────────

FROM nginx:alpine

# Copy built assets
COPY --from=builder /build/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
