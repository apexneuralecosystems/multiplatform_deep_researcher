# SSL/TLS Setup Guide

This guide covers SSL/TLS certificate setup for production deployment.

## Option 1: Let's Encrypt with Certbot (Recommended)

### Prerequisites
- Domain name pointing to your server
- Port 80 and 443 open

### Installation (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

### Get Certificate
```bash
# For Nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Standalone (if Nginx not installed yet)
sudo certbot certonly --standalone -d yourdomain.com
```

### Auto-Renewal
```bash
# Test renewal
sudo certbot renew --dry-run

# Cron job (added automatically, but verify)
sudo crontab -l | grep certbot
```

---

## Option 2: Nginx Configuration with SSL

### Create Nginx Config
```nginx
# /etc/nginx/sites-available/deep-researcher

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL Certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend (React static files)
    location / {
        root /var/www/deep-researcher/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/deep-researcher /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Option 3: Uvicorn with SSL (Development/Testing)

```bash
# Generate self-signed certificate (for testing only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout key.pem -out cert.pem \
    -subj "/CN=localhost"

# Run uvicorn with SSL
uvicorn backend.main:app --host 0.0.0.0 --port 443 \
    --ssl-keyfile key.pem --ssl-certfile cert.pem
```

---

## Option 4: Cloud Provider SSL

### AWS (ACM + ALB)
1. Request certificate in AWS Certificate Manager
2. Create Application Load Balancer
3. Add HTTPS listener with ACM certificate
4. Target group points to backend on port 8000

### Cloudflare
1. Add domain to Cloudflare
2. Enable "Full (strict)" SSL mode
3. Cloudflare handles SSL termination
4. Origin server can use self-signed cert

---

## Environment Variables

Update `.env` for production:
```bash
# Add your production domain to CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

## Verification

```bash
# Test SSL configuration
curl -I https://yourdomain.com

# Check certificate details
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# SSL Labs test (comprehensive)
# https://www.ssllabs.com/ssltest/
```
