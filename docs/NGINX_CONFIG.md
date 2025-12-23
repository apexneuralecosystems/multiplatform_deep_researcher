# Nginx Configuration for Multiplatform Deep Researcher

This guide covers Nginx reverse proxy setup for production deployment.

## Production URLs

| Service | URL | Port |
|---------|-----|------|
| Frontend | https://multiplatform.apexneural.cloud | 3014 |
| Backend API | https://multiplatform-api.apexneural.cloud | 8097 |

## The Problem: "Unexpected token '<'"

If you see this error:
```
Unexpected token '<', "<!DOCTYPE "... is not valid JSON
```

It means **Nginx is serving HTML instead of proxying to the backend**. 

---

## Nginx Configuration

### Backend API (multiplatform-api.apexneural.cloud)

```nginx
server {
    listen 80;
    server_name multiplatform-api.apexneural.cloud;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name multiplatform-api.apexneural.cloud;

    ssl_certificate /etc/letsencrypt/live/multiplatform-api.apexneural.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/multiplatform-api.apexneural.cloud/privkey.pem;

    # Proxy all requests to FastAPI backend on port 8097
    location / {
        proxy_pass http://127.0.0.1:8097;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout for long-running research
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://127.0.0.1:8097;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

### Frontend (multiplatform.apexneural.cloud)
    location / {
        root /path/to/multiplatform_deep_researcher/frontend/dist;
        index index.html;
        
        # SPA fallback - return index.html for client-side routing
        try_files $uri $uri/ /index.html;
    }

    # ─────────────────────────────────────────────────────────────
    # Error handling
    # ─────────────────────────────────────────────────────────────
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

---

## Quick Fix: Test Configuration

After editing the config:

```bash
# Test nginx config syntax
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

---

## Common Mistakes

### 1. Backend not running
Make sure your FastAPI backend is running on port 8000:
```bash
pm2 status  # Check if running
pm2 restart multiplatform-api  # Restart if needed
```

### 2. Wrong proxy_pass URL
- Use `http://127.0.0.1:8000` (not `localhost`)
- Make sure the port matches your backend

### 3. Missing trailing slash
```nginx
# Wrong - will result in /api/research -> /research
location /api {
    proxy_pass http://127.0.0.1:8000;
}

# Correct - preserves path
location /api/ {
    proxy_pass http://127.0.0.1:8000;
}
```

### 4. Frontend build not updated
```bash
cd frontend
npm run build  # Rebuild after changes
```

---

## Debug Commands

```bash
# Check if backend is responding directly
curl http://127.0.0.1:8000/api/health

# Check nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check nginx access logs
sudo tail -f /var/log/nginx/access.log

# Check if port 8000 is in use
sudo netstat -tlnp | grep 8000
```

---

## Testing the Setup

1. **Test backend health**:
   ```bash
   curl https://your-domain.com/api/health
   ```
   Should return: `{"status": "healthy"}`

2. **Test frontend**:
   Open `https://your-domain.com` in browser

3. **Test WebSocket** (in browser console):
   ```javascript
   const ws = new WebSocket('wss://your-domain.com/ws/test');
   ws.onopen = () => console.log('Connected!');
   ```
