#!/bin/bash
# HexaBid SSL + Nginx Hardening Script
# Usage: sudo bash scripts/enable_ssl.sh <domain> [email]

set -e

DOMAIN="$1"
EMAIL="$2"
APP_NAME="hexabid-erp"
SITE_PATH="/etc/nginx/sites-available/$APP_NAME"

if [ -z "$DOMAIN" ]; then
  echo "Usage: $0 <domain> [email]"
  exit 1
fi

if ! command -v certbot >/dev/null 2>&1; then
  echo "[INFO] Installing certbot..."
  apt-get update && apt-get install -y certbot python3-certbot-nginx
fi

# Obtain certificate
if [ -n "$EMAIL" ]; then
  certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "$EMAIL" || true
else
  certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email || true
fi

# Generate DH params if missing
if [ ! -f /etc/ssl/certs/dhparam.pem ]; then
  echo "[INFO] Generating strong DH parameters (this can take a minute)..."
  openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048
fi

# Write hardened nginx config
cat > "$SITE_PATH" <<EOF
upstream backend_api {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN;

    root /var/www/hexabid/frontend/build;
    index index.html;

    # SSL
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_dhparam /etc/ssl/certs/dhparam.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header Content-Security-Policy "default-src 'self'; connect-src 'self' https: wss:; img-src 'self' data: https:; style-src 'self' 'unsafe-inline' https:; script-src 'self' 'unsafe-inline' https:; font-src 'self' data: https:" always;

    # Frontend
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend_api/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    client_max_body_size 50M;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml+rss application/rss+xml image/svg+xml;
}
EOF

nginx -t && systemctl reload nginx

# Setup auto renew
if ! crontab -l 2>/dev/null | grep -q 'certbot renew'; then
  echo "[INFO] Adding certbot auto-renew cron job"
  (crontab -l 2>/dev/null; echo "0 3 * * * /usr/bin/certbot renew --quiet && /usr/sbin/nginx -s reload") | crontab -
fi

echo "[OK] SSL enabled and Nginx hardened for $DOMAIN"
