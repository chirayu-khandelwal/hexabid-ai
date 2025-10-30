#!/bin/bash

#############################################
# HexaBid ERP Deployment Script
# For deployment on VPN Server (app.hexabid.co.in)
#############################################

set -e  # Exit on error

echo "========================================"
echo "HexaBid ERP Deployment Script"
echo "========================================"

# Configuration
APP_NAME="hexabid-erp"
DEPLOY_DIR="/var/www/hexabid"
BACKEND_DIR="$DEPLOY_DIR/backend"
FRONTEND_DIR="$DEPLOY_DIR/frontend"
DOMAIN="app.hexabid.co.in"
SERVER_USER="root"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use sudo)"
    exit 1
fi

print_info "Starting deployment process..."

# Step 1: Update system packages
print_info "Updating system packages..."
apt-get update
apt-get upgrade -y

# Step 2: Install required dependencies
print_info "Installing system dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    nginx \
    certbot \
    python3-certbot-nginx \
    mongodb \
    git \
    curl \
    wget \
    chromium-browser \
    chromium-chromedriver

# Install yarn globally
npm install -g yarn

# Step 3: Create application directory
print_info "Creating application directory at $DEPLOY_DIR..."
mkdir -p $DEPLOY_DIR
mkdir -p $BACKEND_DIR
mkdir -p $FRONTEND_DIR
mkdir -p /var/log/hexabid

# Step 4: Copy application files
print_info "Copying application files..."
if [ -d "./backend" ]; then
    cp -r ./backend/* $BACKEND_DIR/
    print_info "Backend files copied"
else
    print_error "Backend directory not found in current location"
    exit 1
fi

if [ -d "./frontend" ]; then
    cp -r ./frontend/* $FRONTEND_DIR/
    print_info "Frontend files copied"
else
    print_error "Frontend directory not found in current location"
    exit 1
fi

# Step 5: Setup Python backend
print_info "Setting up Python backend..."
cd $BACKEND_DIR

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy production environment file
if [ -f ".env.production" ]; then
    cp .env.production .env
    print_info "Production environment file activated"
fi

deactivate

# Step 6: Setup Node.js frontend
print_info "Setting up frontend..."
cd $FRONTEND_DIR

# Copy production environment file
if [ -f ".env.production" ]; then
    cp .env.production .env
    print_info "Production frontend environment activated"
fi

# Install dependencies
yarn install

# Build production bundle
print_info "Building frontend production bundle..."
yarn build

# Step 7: Setup MongoDB
print_info "Setting up MongoDB..."
systemctl start mongodb
systemctl enable mongodb

# Step 8: Configure Nginx
print_info "Configuring Nginx..."
cat > /etc/nginx/sites-available/$APP_NAME <<EOF
# HexaBid ERP Nginx Configuration

# Backend API Server
upstream backend_api {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    # Redirect HTTP to HTTPS (will be enabled after SSL setup)
    # return 301 https://\$server_name\$request_uri;
    
    # Root directory for frontend
    root $FRONTEND_DIR/build;
    index index.html;

    # Frontend static files
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://backend_api/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Increase client body size for file uploads
    client_max_body_size 50M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/rss+xml font/truetype font/opentype application/vnd.ms-fontobject image/svg+xml;
}

# HTTPS Configuration (will be configured by certbot)
# server {
#     listen 443 ssl http2;
#     listen [::]:443 ssl http2;
#     server_name $DOMAIN;
#
#     # SSL certificates will be added by certbot
#     
#     root $FRONTEND_DIR/build;
#     index index.html;
#
#     location / {
#         try_files \$uri \$uri/ /index.html;
#     }
#
#     location /api/ {
#         proxy_pass http://backend_api/api/;
#         # ... same proxy settings as above
#     }
# }
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/$APP_NAME

# Remove default nginx site if exists
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Reload nginx
systemctl reload nginx
systemctl enable nginx

print_info "Nginx configured successfully"

# Step 9: Setup systemd service for backend
print_info "Creating systemd service for backend..."
cat > /etc/systemd/system/hexabid-backend.service <<EOF
[Unit]
Description=HexaBid ERP Backend API
After=network.target mongodb.service

[Service]
Type=simple
User=$SERVER_USER
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin"
ExecStart=$BACKEND_DIR/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
systemctl daemon-reload
systemctl start hexabid-backend
systemctl enable hexabid-backend

print_info "Backend service created and started"

# Step 10: Setup SSL with Certbot (optional - requires domain to be pointing to server)
print_info "SSL Certificate setup..."
read -p "Do you want to setup SSL certificate now? Domain must be pointing to this server. (y/n): " setup_ssl

if [ "$setup_ssl" = "y" ] || [ "$setup_ssl" = "Y" ]; then
    print_info "Setting up SSL certificate..."
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@hexabid.co.in
    print_info "SSL certificate installed successfully"
else
    print_warning "Skipping SSL setup. You can run 'certbot --nginx -d $DOMAIN' later to enable HTTPS"
fi

# Step 11: Configure firewall (if UFW is installed)
if command -v ufw &> /dev/null; then
    print_info "Configuring firewall..."
    ufw allow 'Nginx Full'
    ufw allow OpenSSH
    ufw --force enable
    print_info "Firewall configured"
fi

# Step 12: Display status
print_info "========================================"
print_info "Deployment Summary"
print_info "========================================"
print_info "Application Directory: $DEPLOY_DIR"
print_info "Domain: $DOMAIN"
print_info "Backend Service: hexabid-backend"
print_info "Database: MongoDB (localhost:27017)"
print_info ""
print_info "Service Status:"
systemctl status hexabid-backend --no-pager -l | head -5
print_info ""
systemctl status nginx --no-pager -l | head -5
print_info ""
print_info "========================================"
print_info "Deployment completed successfully!"
print_info "========================================"
print_info ""
print_info "Next steps:"
print_info "1. Update DNS records to point $DOMAIN to this server IP"
print_info "2. Configure email, WhatsApp, and payment gateway services"
print_info "3. Run './configure_scraper.sh' to setup GeM scraper"
print_info "4. Setup SSL if not done: certbot --nginx -d $DOMAIN"
print_info ""
print_info "To check logs:"
print_info "  Backend: journalctl -u hexabid-backend -f"
print_info "  Nginx: tail -f /var/log/nginx/error.log"
print_info ""
print_info "To restart services:"
print_info "  Backend: systemctl restart hexabid-backend"
print_info "  Nginx: systemctl reload nginx"
print_info ""

exit 0
