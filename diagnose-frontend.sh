#!/bin/bash
# Frontend Deployment Diagnostic Script
# Run this on your production server to diagnose 502 Bad Gateway

echo "=========================================="
echo "Frontend Deployment Diagnostic"
echo "=========================================="
echo ""

echo "=== 1. Docker Container Status ==="
echo "Looking for multiplatform frontend containers..."
docker ps -a | grep -i "multiplatform.*frontend\|frontend.*multiplatform" || echo "No frontend container found"
echo ""

echo "=== 2. All Multiplatform Containers ==="
docker ps -a | grep multiplatform || echo "No multiplatform containers found"
echo ""

echo "=== 3. Container Logs (Last 30 lines) ==="
FRONTEND_CONTAINER=$(docker ps -aq --filter "name=frontend" | head -1)
if [ -z "$FRONTEND_CONTAINER" ]; then
    FRONTEND_CONTAINER=$(docker ps -aq --filter "name=multiplatform" | head -1)
fi

if [ -n "$FRONTEND_CONTAINER" ]; then
    echo "Container ID: $FRONTEND_CONTAINER"
    docker logs "$FRONTEND_CONTAINER" --tail 30 2>&1
else
    echo "ERROR: No frontend container found!"
fi
echo ""

echo "=== 4. Test Container on Port 3014 ==="
curl -I http://localhost:3014 2>&1 | head -5 || echo "ERROR: Cannot connect to port 3014"
echo ""

echo "=== 5. Check Container Files ==="
if [ -n "$FRONTEND_CONTAINER" ]; then
    echo "Checking /usr/share/nginx/html/ contents:"
    docker exec "$FRONTEND_CONTAINER" ls -la /usr/share/nginx/html/ 2>&1 | head -15 || echo "ERROR: Cannot exec into container"
    echo ""
    echo "Checking if index.html exists:"
    docker exec "$FRONTEND_CONTAINER" test -f /usr/share/nginx/html/index.html && echo "✓ index.html exists" || echo "✗ index.html MISSING"
else
    echo "Skipped: No container found"
fi
echo ""

echo "=== 6. Container Nginx Config ==="
if [ -n "$FRONTEND_CONTAINER" ]; then
    docker exec "$FRONTEND_CONTAINER" cat /etc/nginx/conf.d/default.conf 2>&1 || echo "ERROR: Cannot read nginx config"
else
    echo "Skipped: No container found"
fi
echo ""

echo "=== 7. Port Listeners ==="
echo "Checking what's listening on ports 80, 443, 3014:"
sudo ss -tlnp 2>/dev/null | grep -E ":80 |:443 |:3014 " || netstat -tlnp 2>/dev/null | grep -E ":80 |:443 |:3014 " || echo "Cannot check ports (may need sudo)"
echo ""

echo "=== 8. Host Nginx Status ==="
if command -v nginx &> /dev/null; then
    echo "Nginx version:"
    nginx -v 2>&1
    echo ""
    echo "Nginx config test:"
    sudo nginx -t 2>&1
else
    echo "Nginx not found in PATH"
fi
echo ""

echo "=== 9. Host Nginx Config Files ==="
echo "Checking for multiplatform nginx configs:"
if [ -d "/etc/nginx/sites-enabled" ]; then
    ls -la /etc/nginx/sites-enabled/ | grep -i multiplatform || echo "No multiplatform config in sites-enabled"
    echo ""
    echo "Contents of multiplatform config (if exists):"
    find /etc/nginx/sites-enabled /etc/nginx/conf.d -name "*multiplatform*" -o -name "*apexneural*" 2>/dev/null | head -3 | while read file; do
        echo "--- $file ---"
        cat "$file" 2>/dev/null | head -30
        echo ""
    done
else
    echo "/etc/nginx/sites-enabled not found"
fi
echo ""

echo "=== 10. Nginx Error Logs (Last 20 lines) ==="
if [ -f "/var/log/nginx/error.log" ]; then
    sudo tail -20 /var/log/nginx/error.log 2>&1 | grep -i "multiplatform\|3014\|502" || echo "No relevant errors in last 20 lines"
else
    echo "Nginx error log not found at /var/log/nginx/error.log"
fi
echo ""

echo "=== 11. Nginx Access Logs (Last 10 lines) ==="
if [ -f "/var/log/nginx/access.log" ]; then
    sudo tail -10 /var/log/nginx/access.log 2>&1 | grep -i "multiplatform\|apexneural" || echo "No recent access logs"
else
    echo "Nginx access log not found"
fi
echo ""

echo "=== 12. Firewall Status ==="
if command -v ufw &> /dev/null; then
    sudo ufw status 2>&1 | head -10
elif command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --list-all 2>&1 | head -20
else
    echo "No firewall tool found (ufw/firewall-cmd)"
fi
echo ""

echo "=== 13. Docker Network ==="
docker network ls | grep multiplatform || echo "No multiplatform network found"
echo ""

echo "=========================================="
echo "Diagnostic Complete"
echo "=========================================="

